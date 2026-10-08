"""Namespace-bound test runs, history, committed events and manual tool results.

Starting a UI run returns immediately; browser subscriptions never own its
execution. Mutation conflicts are not retried. Event cursors are per run.
"""

import json
from collections.abc import Callable
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.contracts.api import (
    ActivationView,
    ChatCompletionRequest,
    PendingToolView,
    RunDetailResponse,
    RunListResponse,
    RunSummary,
    StartRunRequest,
    StartRunResponse,
    ToolResultsRequest,
    ToolResultsResponse,
)
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import SafeID
from app.contracts.interfaces import (
    Clock,
    ContinuationRoute,
    EventBus,
    GraphRepository,
    GraphRuntime,
    RunContext,
    RunPolicy,
    RunRecord,
    RunRepository,
    RunSubmission,
    ToolBridge,
    Validator,
    canonical_hash,
    canonical_json,
)

from .security import read_body


def submission(
    settings: Settings,
    validator: Validator,
    snapshot,
    namespace: str,
    inputs: dict,
    request: ChatCompletionRequest,
) -> RunSubmission:
    """Capture immutable context, policy and prepared named inputs before admission."""
    return RunSubmission(
        plan=validator.compile(snapshot),
        inputs_json=validator.prepare_inputs(snapshot.graph(), canonical_json(inputs)),
        context=RunContext(
            namespace=namespace,
            messages_json=canonical_json([m.model_dump(mode="json") for m in request.messages]),
            tools_json=canonical_json([t.model_dump(mode="json") for t in request.tools or []]),
        ),
        policy=RunPolicy(
            client_request_json=canonical_json(
                request.model_dump(mode="json", by_alias=True, exclude_none=True)
            ),
            max_node_executions=settings.max_node_executions,
            max_tool_rounds=settings.max_tool_rounds,
            active_timeout_seconds=settings.run_active_timeout_seconds,
            tool_wait_timeout_seconds=settings.tool_wait_timeout_seconds,
        ),
    )


def summary(run: RunRecord, now: datetime) -> RunSummary:
    duration = max(
        0.0, ((run.ended_at or now) - (run.started_at or run.created_at)).total_seconds()
    )
    return RunSummary(
        run_id=run.run_id,
        graph_id=run.snapshot.graph_id,
        revision=run.snapshot.revision,
        graph_hash=run.snapshot.graph_hash,
        status=run.status,
        created_at=run.created_at.isoformat(),
        started_at=run.started_at.isoformat() if run.started_at else None,
        ended_at=run.ended_at.isoformat() if run.ended_at else None,
        duration_seconds=duration,
        queue_seconds=run.queue_elapsed_seconds,
        node_executions=run.node_executions,
        upstream_attempts=run.upstream_attempts,
        tool_rounds=run.tool_rounds,
    )


def create_runs_router(
    settings: Settings,
    graphs: GraphRepository,
    validator: Validator,
    repository: RunRepository,
    runtime: GraphRuntime,
    bridge: ToolBridge,
    events: EventBus,
    clock: Clock,
    authorize: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/api/runs")

    @router.post("", response_model=StartRunResponse, status_code=202)
    async def start(request: Request, namespace: str = Depends(authorize)):
        body = await read_body(request, StartRunRequest)
        snapshot = await graphs.load_snapshot(body.graph_id, body.revision)
        # Empty UI history is allowed. A neutral user message supplies a valid
        # ChatCompletionRequest without replacing the independently named inputs.
        try:
            client = ChatCompletionRequest(
                model="cg/" + body.graph_id,
                messages=body.messages or [{"role": "user", "content": ""}],
                tools=body.tools,
            )
        except ValueError:
            raise CGError(
                ErrorCode.INVALID_PARAMETER, "Invalid test-run context or tools."
            ) from None
        prepared = submission(settings, validator, snapshot, namespace, body.inputs, client)
        prepared = prepared.model_copy(
            update={
                "context": prepared.context.model_copy(
                    update={
                        "messages_json": canonical_json(
                            [m.model_dump(mode="json") for m in body.messages]
                        )
                    }
                )
            }
        )
        run = await runtime.submit(prepared)
        return StartRunResponse(run_id=run.run_id, status=run.status)

    @router.get("", response_model=RunListResponse)
    async def history(request: Request, namespace: str = Depends(authorize)):
        from pydantic import TypeAdapter, ValidationError

        from app.contracts.api import RunStatus

        query = request.query_params
        try:
            if set(query) - {"graph_id", "status", "limit", "offset"}:
                raise ValueError
            if any(len(query.getlist(key)) != 1 for key in query):
                raise ValueError
            limit, offset = int(query.get("limit", "20")), int(query.get("offset", "0"))
            if not 1 <= limit <= 100 or offset < 0:
                raise ValueError
            graph_id = query.get("graph_id")
            if graph_id is not None:
                TypeAdapter(SafeID).validate_python(graph_id)
            status = query.get("status")
            if status is not None:
                TypeAdapter(RunStatus).validate_python(status)
        except (ValueError, ValidationError):
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid history filters.") from None
        page = await repository.list_runs(
            namespace, graph_id=graph_id, status=status, limit=limit, offset=min(offset, 2**63 - 1)
        )
        return RunListResponse(
            runs=[summary(run, clock.now()) for run in page.runs],
            total=page.total,
            limit=limit,
            offset=offset,
        )

    @router.get("/{run_id}", response_model=RunDetailResponse)
    async def detail(run_id: str, namespace: str = Depends(authorize)):
        checkpoint = await repository.load_checkpoint(run_id, namespace)
        plan = validator.compile(checkpoint.run.snapshot)
        ports = {item.node_id: list(item.ordered_ports) for item in plan.ports}
        batches = {batch.batch_id: batch for batch in checkpoint.batches}
        return RunDetailResponse(
            run=summary(checkpoint.run, clock.now()),
            snapshot=checkpoint.run.snapshot.graph(),
            activations=[
                ActivationView(
                    activation_id=a.activation_id,
                    node_id=a.key.node_id,
                    scope_key=a.key.scope_key,
                    iteration=a.key.iteration,
                    status=a.status,
                    ready_ports=sorted({port.target_port for port in a.inputs}),
                    expected_ports=ports.get(a.key.node_id, []),
                    started_at=a.started_at.isoformat() if a.started_at else None,
                    ended_at=a.ended_at.isoformat() if a.ended_at else None,
                    payload=json.loads(a.payload_json) if a.payload_json is not None else None,
                    error=json.loads(a.error_json) if a.error_json is not None else None,
                    usage=json.loads(a.usage_json) if a.usage_json is not None else None,
                )
                for a in checkpoint.activations
            ],
            pending_tools=[
                PendingToolView(
                    tool_call_id=t.external_id,
                    activation_id=t.activation_id,
                    node_id=t.node_id,
                    name=t.name,
                    arguments=t.arguments,
                    status="accepted" if t.result is not None else "pending",
                    result=t.result,
                    expires_at=batches[t.batch_id].expires_at.isoformat(),
                )
                for t in checkpoint.pending_tools
                if t.batch_id in batches
            ],
            output=json.loads(checkpoint.run.output_json)
            if checkpoint.run.output_json is not None
            else None,
            error=json.loads(checkpoint.run.error_json)
            if checkpoint.run.error_json is not None
            else None,
        )

    @router.post("/{run_id}/cancel", response_model=StartRunResponse)
    async def cancel(run_id: str, namespace: str = Depends(authorize)):
        run = await runtime.cancel(run_id, namespace)
        return StartRunResponse(run_id=run_id, status=run.status)

    @router.post("/{run_id}/tool-results", response_model=ToolResultsResponse)
    async def results(run_id: str, request: Request, namespace: str = Depends(authorize)):
        run = await repository.get_run(run_id, namespace)
        body = await read_body(request, ToolResultsRequest)
        mappings = await repository.lookup_tools(tuple(r.tool_call_id for r in body.results))
        if len(mappings) != len(body.results) or any(t.run_id != run_id for t in mappings):
            raise CGError(ErrorCode.UNKNOWN_TOOL_CALL, "Unknown tool-call ID for this run.")
        batch_ids = {t.batch_id for t in mappings}
        if len(batch_ids) != 1 or None in batch_ids:
            raise CGError(ErrorCode.AMBIGUOUS_CONTINUATION, "Results must identify one batch.")
        route = ContinuationRoute(
            namespace=namespace,
            model="cg/" + run.snapshot.graph_id,
            run_id=run_id,
            batch_id=mappings[0].batch_id,
            results=tuple(body.results),
        )
        acceptance = await bridge.accept(
            route,
            canonical_hash(
                {"surface": "manual", "run_id": run_id, "results": body.model_dump(mode="json")}
            ),
        )
        await runtime.resume(acceptance)
        current = await repository.get_run(run_id, namespace)
        return ToolResultsResponse(
            run_id=run_id,
            status=current.status,
            accepted_ids=list(acceptance.accepted_ids),
            missing_ids=list(acceptance.missing_ids),
        )

    @router.get("/{run_id}/events")
    async def stream_events(run_id: str, request: Request, namespace: str = Depends(authorize)):
        await repository.get_run(run_id, namespace)
        raw = request.headers.get("last-event-id", "0")
        if not raw.isascii() or not raw.isdecimal():
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid event cursor.")
        try:
            cursor = min(int(raw), 2**63 - 1)
        except ValueError:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid event cursor.") from None

        async def stream():
            try:
                async for event in events.subscribe(run_id, namespace, cursor):
                    yield (
                        f"id: {event.event_id}\nevent: {event.type}\ndata: "
                        + event.model_dump_json()
                        + "\n\n"
                    ).encode("utf-8")
            except CGError as exc:
                yield ("event: error\ndata: " + exc.payload().model_dump_json() + "\n\n").encode()

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router
