"""Frozen component handoffs. Implementations own I/O, transactions and scheduling.

JSON strings in frozen records deliberately prevent mutable nested snapshots.
Root activation scope is the non-null empty string, iteration zero.
"""

import hashlib
import json
import re
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime
from typing import Annotated, Literal, Protocol

from pydantic import ConfigDict, Field, model_validator

from .api import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorDetail,
    FinishReason,
    GraphSummary,
    NodeStatus,
    RunEvent,
    RunStatus,
    TerminalFailureStatus,
    ToolResult,
    ValidationReport,
)
from .graph import Contract, Graph, Nonempty, PositiveInt, SafeID

SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonnegativeInt = Annotated[int, Field(ge=0)]
NonnegativeFloat = Annotated[float, Field(ge=0)]


def canonical_json(value: object) -> str:
    """Canonical objects; array order and raw arguments/results remain unchanged."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def raw_text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_arguments_hash(arguments: str) -> str:
    """Separate Hermes echo check; never replace the raw delivered arguments."""
    return canonical_hash(json.loads(arguments))


class FrozenRecord(Contract):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="after")
    def timezone_aware(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, datetime) and value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        return self

    @model_validator(mode="after")
    def valid_json_records(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            if name.endswith("_json") and value is not None:
                encoded = value if isinstance(value, tuple) else (value,)
                for item in encoded:
                    decoded = json.loads(item)
                    # Canonical JSON rejects Python's nonstandard NaN/Infinity parser values.
                    canonical_json(decoded)
        return self


class GraphSnapshot(FrozenRecord):
    graph_id: SafeID
    revision: PositiveInt
    graph_json: Nonempty
    graph_hash: SHA256

    @classmethod
    def from_graph(cls, graph: Graph) -> "GraphSnapshot":
        value = graph.model_dump(mode="json", by_alias=True)
        return cls(
            graph_id=graph.id,
            revision=graph.revision,
            graph_json=canonical_json(value),
            graph_hash=canonical_hash(value),
        )

    @model_validator(mode="after")
    def content_matches_identity(self):
        graph = Graph.model_validate_json(self.graph_json)
        if graph.id != self.graph_id or graph.revision != self.revision:
            raise ValueError("Snapshot graph identity mismatch")
        if canonical_hash(json.loads(self.graph_json)) != self.graph_hash:
            raise ValueError("Snapshot hash mismatch")
        return self

    def graph(self) -> Graph:
        return Graph.model_validate_json(self.graph_json)


class ActivationKey(FrozenRecord):
    run_id: Nonempty
    scope_key: str
    iteration: NonnegativeInt
    node_id: SafeID

    @model_validator(mode="after")
    def root_scope_iteration(self):
        if self.scope_key == "" and self.iteration != 0:
            raise ValueError("Root activations use iteration zero")
        if self.scope_key and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", self.scope_key):
            raise ValueError("Loop activation scope must be a safe ID")
        return self


class PortPlan(FrozenRecord):
    node_id: SafeID
    ordered_ports: tuple[SafeID, ...]


class LoopPlan(FrozenRecord):
    loop_id: SafeID
    members: tuple[SafeID, ...]
    controller_node_id: SafeID
    inbound_edge_ids: tuple[SafeID, ...]
    feedback_edge_ids: tuple[SafeID, ...]
    exit_edge_ids: tuple[SafeID, ...]


class CompiledGraph(FrozenRecord):
    snapshot: GraphSnapshot
    forward_order: tuple[SafeID, ...]
    ports: tuple[PortPlan, ...]
    loops: tuple[LoopPlan, ...]
    output_node_id: SafeID
    final_llm_node_id: SafeID | None


class PortValue(FrozenRecord):
    target: ActivationKey
    target_port: SafeID
    source_node_id: SafeID
    source_iteration: NonnegativeInt
    value_json: Nonempty


class LoopState(FrozenRecord):
    loop_id: SafeID
    iteration: NonnegativeInt
    status: Literal["waiting", "running", "completed"]
    external_inputs: tuple[PortValue, ...]
    next_feedback: tuple[PortValue, ...]


class RunContext(FrozenRecord):
    namespace: Nonempty
    messages_json: str
    tools_json: str


class RunPolicy(FrozenRecord):
    client_request_json: str
    max_node_executions: PositiveInt
    max_tool_rounds: PositiveInt
    active_timeout_seconds: PositiveInt
    tool_wait_timeout_seconds: PositiveInt


class RunSubmission(FrozenRecord):
    plan: CompiledGraph
    context: RunContext
    inputs_json: str
    policy: RunPolicy


class RunRecord(FrozenRecord):
    run_id: Nonempty
    snapshot: GraphSnapshot
    context: RunContext
    inputs_json: str
    policy: RunPolicy
    status: RunStatus
    state_version: NonnegativeInt
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    active_elapsed_seconds: NonnegativeFloat = 0
    queue_elapsed_seconds: NonnegativeFloat = 0
    node_executions: NonnegativeInt = 0
    upstream_attempts: NonnegativeInt = 0
    tool_rounds: NonnegativeInt = 0
    output_json: str | None = None
    error_json: str | None = None


class ActivationRecord(FrozenRecord):
    activation_id: Nonempty
    key: ActivationKey
    status: NodeStatus
    inputs: tuple[PortValue, ...]
    messages_json: str
    provider_round: NonnegativeInt = 0
    attempt_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    payload_json: str | None = None
    finish_reason: FinishReason | None = None
    control_decision: str | None = None
    error_json: str | None = None
    usage_json: str | None = None


class PendingTool(FrozenRecord):
    external_id: Nonempty
    run_id: Nonempty
    activation_id: Nonempty
    node_id: SafeID
    provider_round: PositiveInt
    call_ordinal: NonnegativeInt
    internal_id: Nonempty
    name: Nonempty
    arguments: str
    arguments_hash: SHA256
    canonical_arguments_hash: SHA256
    batch_id: str | None = None
    status: Literal["unexposed", "pending", "accepted", "terminal"]
    result: str | None = None
    result_hash: SHA256 | None = None

    @model_validator(mode="after")
    def validate_hashes(self):
        if self.arguments_hash != raw_text_hash(self.arguments):
            raise ValueError("Raw tool arguments hash mismatch")
        if self.canonical_arguments_hash != canonical_arguments_hash(self.arguments):
            raise ValueError("Canonical tool arguments hash mismatch")
        if self.result is not None and self.result_hash != raw_text_hash(self.result):
            raise ValueError("Tool result hash mismatch")
        if self.status == "accepted" and self.result is None:
            raise ValueError("Accepted tool requires its immutable result")
        return self


class ResponseEnvelope(FrozenRecord):
    run_id: str | None
    batch_id: str | None
    response_sequence: PositiveInt
    completion_json: Nonempty

    @model_validator(mode="after")
    def valid_completion(self):
        ChatCompletionResponse.model_validate_json(self.completion_json)
        if self.batch_id is not None and self.run_id is None:
            raise ValueError("Tool response requires a graph run")
        return self

    def completion(self) -> ChatCompletionResponse:
        return ChatCompletionResponse.model_validate_json(self.completion_json)


class ToolBatch(FrozenRecord):
    batch_id: Nonempty
    run_id: Nonempty
    sequence: PositiveInt
    status: Literal["open", "closed", "terminal"]
    external_ids: tuple[Nonempty, ...]
    prepared_at: datetime
    expires_at: datetime
    envelope: ResponseEnvelope

    @model_validator(mode="after")
    def valid_batch(self):
        if self.expires_at <= self.prepared_at:
            raise ValueError("Tool expiry must follow preparation")
        if not self.external_ids or len(set(self.external_ids)) != len(self.external_ids):
            raise ValueError("Batch requires unique external IDs")
        if (
            self.envelope.run_id != self.run_id
            or self.envelope.batch_id != self.batch_id
            or self.envelope.response_sequence != self.sequence
        ):
            raise ValueError("Batch envelope identity mismatch")
        calls = self.envelope.completion().choices[0].message.tool_calls or []
        if tuple(call.id for call in calls) != self.external_ids:
            raise ValueError("Batch envelope call IDs mismatch")
        return self


class RunCheckpoint(FrozenRecord):
    run: RunRecord
    activations: tuple[ActivationRecord, ...]
    loops: tuple[LoopState, ...]
    pending_tools: tuple[PendingTool, ...]
    batches: tuple[ToolBatch, ...]
    responses: tuple[ResponseEnvelope, ...]
    events_json: tuple[str, ...]


class ToolCheckpoint(FrozenRecord):
    """One quiescent frontier + new exposure; commit before response bytes."""

    checkpoint: RunCheckpoint
    batch: ToolBatch

    @model_validator(mode="after")
    def quiescent_exposure(self):
        checkpoint = self.checkpoint
        if checkpoint.run.status != "waiting_tools":
            raise ValueError("Tool exposure requires waiting_tools state")
        if any(activation.status == "running" for activation in checkpoint.activations):
            raise ValueError("Tool exposure requires a quiescent frontier")
        if self.batch.run_id != checkpoint.run.run_id or self.batch.status != "open":
            raise ValueError("Tool exposure must belong to run and be open")
        if tuple(batch for batch in checkpoint.batches if batch.status == "open") != (self.batch,):
            raise ValueError("Exactly the exposed batch must be open")
        if self.batch.envelope not in checkpoint.responses:
            raise ValueError("Tool exposure requires its persisted response")
        mappings = {tool.external_id: tool for tool in checkpoint.pending_tools}
        if any(
            external_id not in mappings
            or mappings[external_id].batch_id != self.batch.batch_id
            or mappings[external_id].status != "pending"
            for external_id in self.batch.external_ids
        ):
            raise ValueError("Tool exposure requires all pending mappings")
        return self


class ReplayClaim(FrozenRecord):
    claim_id: Nonempty
    namespace: Nonempty
    run_id: Nonempty
    batch_id: Nonempty
    request_hash: SHA256
    after_response_sequence: PositiveInt
    status: Literal["pending", "completed", "terminal"]
    envelope: ResponseEnvelope | None = None
    error_json: str | None = None


class NewRunRoute(FrozenRecord):
    kind: Literal["new"] = "new"


class ContinuationRoute(FrozenRecord):
    kind: Literal["continuation"] = "continuation"
    namespace: Nonempty
    model: Nonempty
    run_id: Nonempty
    batch_id: Nonempty
    results: tuple[ToolResult, ...]


class ContinuationAcceptance(FrozenRecord):
    kind: Literal["replay", "joined", "partial", "ready"]
    claim: ReplayClaim
    accepted_ids: tuple[str, ...]
    missing_ids: tuple[str, ...]

    @model_validator(mode="after")
    def claim_matches_acceptance(self):
        if self.kind == "replay":
            if self.claim.status != "completed" or self.claim.envelope is None:
                raise ValueError("Replay requires a completed durable response")
        elif self.claim.status != "pending":
            raise ValueError("New or joined acceptance requires pending claim")
        if self.kind == "partial" and not self.missing_ids:
            raise ValueError("Partial acceptance must identify missing results")
        if self.kind == "ready" and self.missing_ids:
            raise ValueError("Ready acceptance cannot have missing results")
        if set(self.accepted_ids) & set(self.missing_ids):
            raise ValueError("Accepted and missing IDs must be disjoint")
        return self


class RunPage(FrozenRecord):
    runs: tuple[RunRecord, ...]
    total: NonnegativeInt


class ProviderRequest(ChatCompletionRequest):
    """Translated physical model; optional explicit stored model-specific control."""

    model: Nonempty
    reasoning_effort: Literal["none", "low", "medium", "high"] | None = None


class GraphRepository(Protocol):
    async def list_graphs(self) -> tuple[GraphSummary, ...]: ...
    async def list_published(self) -> tuple[GraphSnapshot, ...]: ...
    async def create(self, graph: Graph) -> Graph: ...
    async def get(self, graph_id: str) -> Graph: ...
    async def save(self, graph: Graph, expected_revision: int) -> Graph: ...
    async def publish(self, graph_id: str, expected_revision: int) -> GraphSnapshot: ...
    async def load_snapshot(
        self, graph_id: str, revision: int | None = None, *, published_only: bool = False
    ) -> GraphSnapshot: ...


class Validator(Protocol):
    def validate(self, graph: Graph) -> ValidationReport: ...
    def compile(self, snapshot: GraphSnapshot) -> CompiledGraph: ...
    def prepare_inputs(self, graph: Graph, inputs_json: str) -> str: ...


class RunRepository(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...
    async def create_run(
        self, submission: RunSubmission, run_id: str, now: datetime
    ) -> RunRecord: ...
    async def get_run(self, run_id: str, namespace: str) -> RunRecord: ...
    async def list_runs(
        self,
        namespace: str,
        *,
        graph_id: str | None,
        status: RunStatus | None,
        limit: int,
        offset: int,
    ) -> RunPage: ...
    async def load_checkpoint(self, run_id: str, namespace: str) -> RunCheckpoint: ...
    async def save_checkpoint(
        self, checkpoint: RunCheckpoint, expected_version: int
    ) -> RunRecord: ...
    async def claim_activation(
        self, key: ActivationKey, attempt_id: str, now: datetime
    ) -> ActivationRecord | None: ...
    async def checkpoint_batch(
        self, checkpoint: ToolCheckpoint, expected_version: int
    ) -> RunRecord: ...
    async def complete_run(
        self, checkpoint: RunCheckpoint, envelope: ResponseEnvelope, expected_version: int
    ) -> RunRecord: ...
    async def lookup_tools(self, external_ids: tuple[str, ...]) -> tuple[PendingTool, ...]: ...
    async def accept_results(
        self, route: ContinuationRoute, request_hash: str, now: datetime
    ) -> ContinuationAcceptance: ...
    async def get_claim(self, claim_id: str) -> ReplayClaim: ...
    async def terminalize(
        self, run_id: str, status: TerminalFailureStatus, error: ErrorDetail | None, now: datetime
    ) -> RunRecord: ...
    async def cancel_if_unexposed(
        self, run_id: str, namespace: str, now: datetime
    ) -> RunRecord: ...
    async def recover(self, now: datetime) -> tuple[RunRecord, ...]: ...
    async def read_events(
        self, run_id: str, namespace: str, after_event_id: int, limit: int = 1000
    ) -> tuple[RunEvent, ...]: ...
    async def cleanup_history(self, before: datetime) -> int: ...


class GraphRuntime(Protocol):
    async def submit(self, submission: RunSubmission) -> RunRecord: ...
    async def resume(self, acceptance: ContinuationAcceptance) -> None: ...
    async def await_response(
        self, run_id: str, namespace: str, after_response_sequence: int = 0
    ) -> ResponseEnvelope: ...
    async def cancel(self, run_id: str, namespace: str) -> RunRecord: ...
    async def detach_initial(self, run_id: str, namespace: str) -> RunRecord: ...
    async def recover(self) -> None: ...
    async def shutdown(self) -> None: ...


class OllamaAdapter(Protocol):
    async def complete(self, request: ProviderRequest) -> ChatCompletionResponse: ...
    def stream(self, request: ProviderRequest) -> AsyncGenerator[bytes, None]: ...
    async def models(self) -> tuple[str, ...]: ...
    async def health(self) -> bool: ...
    async def close(self) -> None: ...


class ToolBridge(Protocol):
    def map_calls(
        self, activation: ActivationRecord, response: ChatCompletionResponse
    ) -> tuple[PendingTool, ...]: ...
    async def classify(
        self, request: ChatCompletionRequest, namespace: str
    ) -> NewRunRoute | ContinuationRoute: ...
    async def accept(
        self, route: ContinuationRoute, request_hash: str
    ) -> ContinuationAcceptance: ...
    async def prepare_batch(self, run_id: str, namespace: str) -> ResponseEnvelope: ...
    async def await_response(self, claim_id: str) -> ResponseEnvelope: ...


class EventBus(Protocol):
    async def notify(self, run_id: str) -> None: ...
    async def read_after(
        self, run_id: str, namespace: str, after_event_id: int
    ) -> tuple[RunEvent, ...]: ...
    def subscribe(
        self, run_id: str, namespace: str, after_event_id: int
    ) -> AsyncIterator[RunEvent]: ...


class AdmissionLease(Protocol):
    async def wait(self) -> None: ...
    async def release(self) -> None: ...


class AdmissionController(Protocol):
    """Shared graph + ephemeral direct admission; waiting_tools retains its lease."""

    async def acquire(self, job_id: str) -> AdmissionLease: ...
    async def restore(
        self, active_job_ids: tuple[str, ...], queued_job_ids: tuple[str, ...]
    ) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
    def monotonic(self) -> float: ...
    async def sleep(self, seconds: float) -> None: ...
