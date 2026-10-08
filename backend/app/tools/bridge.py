"""Opaque tool mapping, quiescent exposure and SQLite-backed continuation.

map_calls is pure. Runtime durably saves its returned mappings and the owner's
assistant history/round before prepare_batch. Unknown effects serialize one
call per batch even when parallel_tool_calls permits more; no name declares a
call safe. An owner still waits for its whole internal provider round.

classify examines the latest assistant/tool segment, including compressed
histories, and validates echoes without rewriting saved raw arguments. accept
delegates fixed UTC deadlines, partial results, conflict checks and unique
claims to SQLite. await_response only reads the atomically bound first next
response; it never executes inference, tools or a runtime reducer.
"""

import json
import uuid
from datetime import timedelta

from app.contracts.api import (
    TERMINAL_RUN_STATUSES,
    AssistantMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ToolMessage,
    ToolResult,
)
from app.contracts.config import MAX_TOOL_RESULT_BYTES, Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import (
    ActivationRecord,
    Clock,
    ContinuationAcceptance,
    ContinuationRoute,
    EventBus,
    NewRunRoute,
    PendingTool,
    ResponseEnvelope,
    RunRepository,
    ToolBatch,
    ToolCheckpoint,
    canonical_arguments_hash,
    canonical_hash,
    raw_text_hash,
)
from app.providers.sse import strict_json


def canonical_request_hash(request: ChatCompletionRequest) -> str:
    """Include defaults/stream/policy; preserve array order and raw strings."""
    return canonical_hash(request.model_dump(mode="json", by_alias=True, exclude_none=True))


def conflict(message: str) -> CGError:
    return CGError(ErrorCode.CONTINUATION_CONFLICT, message)


def validate_result(content: str) -> None:
    try:
        size = len(content.encode("utf-8"))
    except UnicodeError:
        raise CGError(ErrorCode.INVALID_PARAMETER, "Tool result must be valid UTF-8 text") from None
    if size > MAX_TOOL_RESULT_BYTES:
        raise CGError(ErrorCode.REQUEST_TOO_LARGE, "Tool result exceeds the size limit")


class DurableToolBridge:
    def __init__(
        self, settings: Settings, repository: RunRepository, events: EventBus, clock: Clock
    ):
        self.settings = settings
        self.repository = repository
        self.events = events
        self.clock = clock

    def map_calls(
        self, activation: ActivationRecord, response: ChatCompletionResponse
    ) -> tuple[PendingTool, ...]:
        calls = response.choices[0].message.tool_calls or []
        if len({call.id for call in calls}) != len(calls):
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Upstream repeated an internal tool ID")
        mapped = []
        for ordinal, call in enumerate(calls):
            try:
                arguments = strict_json(call.function.arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be an object")
                hash_ = canonical_hash(arguments)
            except (ValueError, UnicodeError):
                raise CGError(ErrorCode.UPSTREAM_ERROR, "Invalid upstream tool arguments") from None
            mapped.append(
                PendingTool(
                    external_id="cg_" + uuid.uuid4().hex,
                    run_id=activation.key.run_id,
                    activation_id=activation.activation_id,
                    node_id=activation.key.node_id,
                    provider_round=activation.provider_round + 1,
                    call_ordinal=ordinal,
                    internal_id=call.id,
                    name=call.function.name,
                    arguments=call.function.arguments,
                    arguments_hash=raw_text_hash(call.function.arguments),
                    canonical_arguments_hash=hash_,
                    status="unexposed",
                )
            )
        return tuple(mapped)

    async def classify(
        self, request: ChatCompletionRequest, namespace: str
    ) -> NewRunRoute | ContinuationRoute:
        assistant = None
        suffix = []
        for message in reversed(request.messages):
            if isinstance(message, AssistantMessage):
                assistant = message
                break
            suffix.append(message)
        suffix.reverse()
        results = [message for message in suffix if isinstance(message, ToolMessage)]
        if (
            assistant is not None
            and not assistant.tool_calls
            and not request.model.startswith("ollama/")
        ):
            if results:
                raise CGError(
                    ErrorCode.UNKNOWN_TOOL_CALL, "Tool results lack an active tool segment"
                )
            return NewRunRoute()
        calls = assistant.tool_calls if assistant is not None else []
        ids = [message.tool_call_id for message in results]
        echoed_ids = [call.id for call in calls or []]
        lookup = tuple(dict.fromkeys(ids + echoed_ids))
        if not lookup:
            return NewRunRoute()
        tools = {tool.external_id: tool for tool in await self.repository.lookup_tools(lookup)}
        # Physical provider IDs have no reserved prefix. Direct requests bypass
        # graph continuation unless their latest IDs actually map to graph state.
        if request.model.startswith("ollama/") and not tools:
            return NewRunRoute()
        if len(set(ids)) != len(ids):
            raise conflict("Duplicate tool results in continuation")
        if len(set(echoed_ids)) != len(echoed_ids):
            raise conflict("Duplicate echoed tool IDs")
        has_new_user = any(message.role == "user" for message in suffix)
        if has_new_user:
            last_user = max(i for i, message in enumerate(suffix) if message.role == "user")
            trailing_results = any(
                isinstance(message, ToolMessage) for message in suffix[last_user + 1 :]
            )
            # Closed history may precede a new turn without a final assistant echo.
            if not trailing_results and all(
                id_ in tools and tools[id_].status in {"accepted", "terminal"} for id_ in lookup
            ):
                return NewRunRoute()
            raise CGError(
                ErrorCode.AMBIGUOUS_CONTINUATION,
                "A new user turn cannot be mixed with pending tool continuation",
            )
        if not results:
            raise conflict("Pending tool segment requires tool results")
        if set(lookup) - tools.keys():
            raise CGError(ErrorCode.UNKNOWN_TOOL_CALL, "Unknown latest tool-call ID")
        mappings = [tools[id_] for id_ in lookup]
        run_ids = {tool.run_id for tool in mappings}
        batch_ids = {tool.batch_id for tool in mappings}
        if len(run_ids) != 1 or len(batch_ids) != 1 or None in batch_ids:
            raise CGError(
                ErrorCode.AMBIGUOUS_CONTINUATION,
                "Tool results must identify one exposed run and batch",
            )
        run_id = mappings[0].run_id
        batch_id = mappings[0].batch_id
        try:
            run = await self.repository.get_run(run_id, namespace)
        except CGError as error:
            if error.code == ErrorCode.RUN_NOT_FOUND:
                raise conflict("Tool continuation namespace does not match") from None
            raise
        if request.model != "cg/" + run.snapshot.graph_id:
            raise conflict("Tool continuation model does not match")
        for call in calls or []:
            mapping = tools[call.id]
            try:
                arguments = strict_json(call.function.arguments)
                valid = (
                    isinstance(arguments, dict)
                    and canonical_arguments_hash(call.function.arguments)
                    == mapping.canonical_arguments_hash
                )
            except (ValueError, UnicodeError):
                valid = False
            if call.function.name != mapping.name or not valid:
                raise conflict("Echoed tool call differs from the saved mapping")
        for result in results:
            validate_result(result.content)
            if result.name is not None and result.name != tools[result.tool_call_id].name:
                raise conflict("Tool result name differs from its owner mapping")
        return ContinuationRoute(
            namespace=namespace,
            model=request.model,
            run_id=run_id,
            batch_id=batch_id,
            results=tuple(
                ToolResult(tool_call_id=result.tool_call_id, content=result.content)
                for result in results
            ),
        )

    async def accept(self, route: ContinuationRoute, request_hash: str) -> ContinuationAcceptance:
        for result in route.results:
            validate_result(result.content)
        acceptance = await self.repository.accept_results(route, request_hash, self.clock.now())
        await self.events.notify(route.run_id)
        return acceptance

    async def prepare_batch(self, run_id: str, namespace: str) -> ResponseEnvelope:
        # CAS retries only rebuild an unexposed local proposal, never an external effect.
        for _ in range(16):
            checkpoint = await self.repository.load_checkpoint(run_id, namespace)
            if checkpoint.run.status in TERMINAL_RUN_STATUSES:
                raise CGError(ErrorCode.RUN_TERMINAL, "Cannot expose tools for a terminal run")
            existing = next((batch for batch in checkpoint.batches if batch.status == "open"), None)
            if existing is not None:
                if self.clock.now() >= existing.expires_at:
                    raise CGError(
                        ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired"
                    )
                return existing.envelope
            if any(activation.status == "running" for activation in checkpoint.activations):
                raise conflict("Tool exposure requires a quiescent frontier")
            candidates = sorted(
                (tool for tool in checkpoint.pending_tools if tool.status == "unexposed"),
                key=lambda tool: (tool.activation_id, tool.provider_round, tool.call_ordinal),
            )
            if not candidates:
                raise conflict("No durable unexposed tool calls are available")
            if checkpoint.run.tool_rounds >= checkpoint.run.policy.max_tool_rounds:
                raise CGError(ErrorCode.BUDGET_EXCEEDED, "Tool batch budget exhausted")
            selected = candidates[0]
            batch_id = uuid.uuid4().hex
            sequence = len(checkpoint.responses) + 1
            now = self.clock.now()
            completion = ChatCompletionResponse.model_validate(
                {
                    "id": "chatcmpl_" + uuid.uuid4().hex,
                    "created": int(now.timestamp()),
                    "model": "cg/" + checkpoint.run.snapshot.graph_id,
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "tool_calls",
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": selected.external_id,
                                        "type": "function",
                                        "function": {
                                            "name": selected.name,
                                            "arguments": selected.arguments,
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            )
            envelope = ResponseEnvelope(
                run_id=run_id,
                batch_id=batch_id,
                response_sequence=sequence,
                completion_json=completion.model_dump_json(),
            )
            batch = ToolBatch(
                batch_id=batch_id,
                run_id=run_id,
                sequence=sequence,
                status="open",
                external_ids=(selected.external_id,),
                prepared_at=now,
                expires_at=now + timedelta(seconds=checkpoint.run.policy.tool_wait_timeout_seconds),
                envelope=envelope,
            )
            proposed = checkpoint.model_copy(
                update={
                    "run": checkpoint.run.model_copy(update={"status": "waiting_tools"}),
                    "pending_tools": tuple(
                        tool.model_copy(update={"status": "pending", "batch_id": batch_id})
                        if tool.external_id == selected.external_id
                        else tool
                        for tool in checkpoint.pending_tools
                    ),
                    "batches": checkpoint.batches + (batch,),
                    "responses": checkpoint.responses + (envelope,),
                }
            )
            try:
                await self.repository.checkpoint_batch(
                    ToolCheckpoint(checkpoint=proposed, batch=batch), checkpoint.run.state_version
                )
            except CGError as error:
                if error.code != ErrorCode.CONTINUATION_CONFLICT:
                    raise
                refreshed = await self.repository.get_run(run_id, namespace)
                if refreshed.state_version == checkpoint.run.state_version:
                    raise
                continue
            await self.events.notify(run_id)
            return envelope
        raise conflict("Tool checkpoint changed repeatedly; retry from durable state")

    async def await_response(self, claim_id: str) -> ResponseEnvelope:
        while True:
            claim = await self.repository.get_claim(claim_id)
            if claim.status == "completed":
                return claim.envelope
            if claim.status == "terminal":
                error = json.loads(claim.error_json) if claim.error_json is not None else {}
                try:
                    code = ErrorCode(error.get("code", "run_terminal"))
                except ValueError:
                    code = ErrorCode.RUN_TERMINAL
                raise CGError(code, "Continuation run reached a terminal outcome")
            checkpoint = await self.repository.load_checkpoint(claim.run_id, claim.namespace)
            batch = next(batch for batch in checkpoint.batches if batch.batch_id == claim.batch_id)
            if batch.status == "open" and self.clock.now() >= batch.expires_at:
                error = CGError(
                    ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired"
                )
                await self.repository.terminalize(
                    claim.run_id, "failed", error.payload().error, self.clock.now()
                )
                await self.events.notify(claim.run_id)
                continue
            await self.clock.sleep(0.05)
