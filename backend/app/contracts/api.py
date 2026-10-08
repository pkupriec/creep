"""Text/function Chat Completions profile and management wire DTOs."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from .errors import ErrorDetail
from .graph import Contract, ExactOne, ExactZero, Graph, Nonempty, PositiveInt, SafeID


class TextPart(Contract):
    type: Literal["text"]
    text: str


TextContent = str | Annotated[list[TextPart], Field(min_length=1)]


class FunctionCall(Contract):
    name: Nonempty
    arguments: str


class ToolCall(Contract):
    id: Nonempty
    type: Literal["function"]
    function: FunctionCall


class SystemMessage(Contract):
    role: Literal["system", "developer"]
    content: TextContent
    name: Nonempty | None = None


class UserMessage(Contract):
    role: Literal["user"]
    content: TextContent
    name: Nonempty | None = None


class AssistantMessage(Contract):
    role: Literal["assistant"]
    content: TextContent | None = None
    tool_calls: Annotated[list[ToolCall], Field(min_length=1)] | None = None
    name: Nonempty | None = None

    @model_validator(mode="after")
    def has_content_or_calls(self):
        if self.content is None and not self.tool_calls:
            raise ValueError("Assistant message requires text or tool_calls")
        return self


class ToolMessage(Contract):
    role: Literal["tool"]
    tool_call_id: Nonempty
    content: str
    name: Nonempty | None = None


Message = Annotated[
    SystemMessage | UserMessage | AssistantMessage | ToolMessage, Field(discriminator="role")
]


class FunctionDefinition(Contract):
    name: Nonempty
    description: str | None = None
    parameters: dict[str, JsonValue]
    strict: bool | None = None


class FunctionTool(Contract):
    type: Literal["function"]
    function: FunctionDefinition


class ToolChoiceFunction(Contract):
    name: Nonempty


class ForcedToolChoice(Contract):
    type: Literal["function"]
    function: ToolChoiceFunction


ToolChoice = Literal["none", "auto", "required"] | ForcedToolChoice


class TextResponseFormat(Contract):
    type: Literal["text"]


class JSONObjectResponseFormat(Contract):
    type: Literal["json_object"]


class JSONSchemaDefinition(Contract):
    name: SafeID
    description: str | None = None
    schema_: dict[str, JsonValue] = Field(alias="schema")
    strict: bool | None = None


class JSONSchemaResponseFormat(Contract):
    type: Literal["json_schema"]
    json_schema: JSONSchemaDefinition


ResponseFormat = Annotated[
    TextResponseFormat | JSONObjectResponseFormat | JSONSchemaResponseFormat,
    Field(discriminator="type"),
]


class StreamOptions(Contract):
    include_usage: bool = False


class ChatCompletionRequest(Contract):
    model: Annotated[str, Field(pattern=r"^(cg/[A-Za-z0-9][A-Za-z0-9_-]{0,63}|ollama/[^\s]+)$")]
    messages: Annotated[list[Message], Field(min_length=1)]
    tools: list[FunctionTool] | None = None
    tool_choice: ToolChoice | None = None
    parallel_tool_calls: bool = True
    stream: bool = False
    temperature: Annotated[float, Field(ge=0, le=2)] | None = None
    top_p: Annotated[float, Field(ge=0, le=1)] | None = None
    max_tokens: PositiveInt | None = None
    stop: str | Annotated[list[str], Field(min_length=1, max_length=4)] | None = None
    response_format: ResponseFormat | None = None
    stream_options: StreamOptions | None = None
    n: ExactOne = 1

    @model_validator(mode="after")
    def supported_profile(self):
        if self.stream_options is not None and not self.stream:
            raise ValueError("stream_options requires stream=true")
        names = [tool.function.name for tool in self.tools or []]
        if len(names) != len(set(names)):
            raise ValueError("Tool function names must be unique")
        if (
            isinstance(self.tool_choice, ForcedToolChoice)
            and self.tool_choice.function.name not in names
        ):
            raise ValueError("Forced tool must appear in tools")
        return self


class Usage(Contract):
    prompt_tokens: Annotated[int, Field(ge=0)]
    completion_tokens: Annotated[int, Field(ge=0)]
    total_tokens: Annotated[int, Field(ge=0)]


FinishReason = Literal["stop", "tool_calls", "length"]


class CompletionChoice(Contract):
    index: ExactZero = 0
    message: AssistantMessage
    finish_reason: FinishReason

    @model_validator(mode="after")
    def tools_finish_reason(self):
        if (self.finish_reason == "tool_calls") != bool(self.message.tool_calls):
            raise ValueError("tool_calls and finish_reason must agree")
        return self


class ChatCompletionResponse(Contract):
    id: Nonempty
    object: Literal["chat.completion"] = "chat.completion"
    created: Annotated[int, Field(ge=0)]
    model: Nonempty
    choices: Annotated[list[CompletionChoice], Field(min_length=1, max_length=1)]
    usage: Usage | None = None

    @classmethod
    def from_upstream(cls, payload: object) -> "ChatCompletionResponse":
        """Validate Ollama JSON, then remove only declared nonsemantic metadata.

        The adapter maps validation errors to sanitized upstream_error; this
        pure boundary performs no HTTP, retries, or model/name translation.
        """
        wire = _UpstreamCompletion.model_validate(payload)
        normalized = wire.model_dump(mode="json", exclude_unset=True)
        normalized.pop("system_fingerprint", None)
        if normalized.get("usage") is not None:
            normalized["usage"].pop("prompt_tokens_details", None)
        for choice in normalized["choices"]:
            for call in choice["message"].get("tool_calls") or []:
                call.pop("index", None)
        return cls.model_validate(normalized)


class _PromptTokensDetails(Contract):
    cached_tokens: Annotated[int, Field(ge=0)] | None = None


class _UpstreamUsage(Usage):
    prompt_tokens_details: _PromptTokensDetails | None = None


class _UpstreamToolCall(ToolCall):
    index: Annotated[int, Field(ge=0)] | None = None


class _UpstreamAssistantMessage(AssistantMessage):
    tool_calls: Annotated[list[_UpstreamToolCall], Field(min_length=1)] | None = None
    reasoning: str | None = Field(default=None, exclude=True, repr=False)

    @model_validator(mode="after")
    def call_indices_match_order(self):
        for ordinal, call in enumerate(self.tool_calls or []):
            if call.index is not None and call.index != ordinal:
                raise ValueError("Nonstream tool index must match its array ordinal")
        return self


class _UpstreamChoice(CompletionChoice):
    message: _UpstreamAssistantMessage


class _UpstreamCompletion(ChatCompletionResponse):
    system_fingerprint: str | None = None
    choices: Annotated[list[_UpstreamChoice], Field(min_length=1, max_length=1)]
    usage: _UpstreamUsage | None = None


class StreamFunctionDelta(Contract):
    name: str | None = None
    arguments: str | None = None


class StreamToolDelta(Contract):
    index: Annotated[int, Field(ge=0)]
    id: str | None = None
    type: Literal["function"] | None = None
    function: StreamFunctionDelta | None = None


class StreamDelta(Contract):
    role: Literal["assistant"] | None = None
    content: str | None = None
    tool_calls: list[StreamToolDelta] | None = None


class StreamChoice(Contract):
    index: ExactZero = 0
    delta: StreamDelta
    finish_reason: FinishReason | None = None


class ChatCompletionChunk(Contract):
    id: Nonempty
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: Annotated[int, Field(ge=0)]
    model: Nonempty
    choices: Annotated[list[StreamChoice], Field(max_length=1)]
    usage: Usage | None = None


class ModelInfo(Contract):
    id: Nonempty
    object: Literal["model"] = "model"
    created: Annotated[int, Field(ge=0)] = 0
    owned_by: Literal["cognitive-graph", "ollama"]


class ModelsResponse(Contract):
    object: Literal["list"] = "list"
    data: list[ModelInfo]


class GraphSummary(Contract):
    id: SafeID
    name: Nonempty
    revision: PositiveInt
    published_revision: PositiveInt | None = None


class GraphListResponse(Contract):
    graphs: list[GraphSummary]


class SaveGraphRequest(Contract):
    graph: Graph
    expected_revision: PositiveInt


class PublishGraphRequest(Contract):
    expected_revision: PositiveInt


class PublishGraphResponse(Contract):
    graph_id: SafeID
    published_revision: PositiveInt
    graph_hash: str


class ValidationIssue(Contract):
    code: Nonempty
    message: str
    node_id: SafeID | None = None
    edge_id: SafeID | None = None


class ValidationReport(Contract):
    valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @model_validator(mode="after")
    def valid_matches_errors(self):
        if self.valid != (not self.errors):
            raise ValueError("valid must match absence of errors")
        return self


RunStatus = Literal[
    "queued", "running", "waiting_tools", "completed", "failed", "cancelled", "interrupted"
]
NodeStatus = Literal[
    "pending", "ready", "running", "waiting_tools", "completed", "failed", "cancelled"
]
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "cancelled", "interrupted"})
TerminalFailureStatus = Literal["failed", "cancelled", "interrupted"]


class StartRunRequest(Contract):
    graph_id: SafeID
    revision: PositiveInt
    inputs: dict[SafeID, JsonValue]
    messages: list[Message] = Field(default_factory=list)
    tools: list[FunctionTool] = Field(default_factory=list)


class StartRunResponse(Contract):
    run_id: Nonempty
    status: RunStatus


class ToolResult(Contract):
    model_config = {"extra": "forbid", "strict": True, "frozen": True}
    tool_call_id: Nonempty
    content: str


class ToolResultsRequest(Contract):
    results: Annotated[list[ToolResult], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [result.tool_call_id for result in self.results]
        if len(set(ids)) != len(ids):
            raise ValueError("Tool result IDs must be unique")
        return self


class ToolResultsResponse(Contract):
    run_id: Nonempty
    status: RunStatus
    accepted_ids: list[str]
    missing_ids: list[str]


class RunSummary(Contract):
    run_id: Nonempty
    graph_id: SafeID
    revision: PositiveInt
    graph_hash: str
    status: RunStatus
    created_at: str
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: Annotated[float, Field(ge=0)]
    queue_seconds: Annotated[float, Field(ge=0)]
    node_executions: Annotated[int, Field(ge=0)]
    upstream_attempts: Annotated[int, Field(ge=0)]
    tool_rounds: Annotated[int, Field(ge=0)]


class RunListResponse(Contract):
    runs: list[RunSummary]
    total: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class ActivationView(Contract):
    activation_id: Nonempty
    node_id: SafeID
    scope_key: str
    iteration: Annotated[int, Field(ge=0)]
    status: NodeStatus
    ready_ports: list[SafeID]
    expected_ports: list[SafeID]
    started_at: str | None = None
    ended_at: str | None = None
    payload: JsonValue = None
    error: ErrorDetail | None = None
    usage: Usage | None = None


class PendingToolView(Contract):
    tool_call_id: Nonempty
    activation_id: Nonempty
    node_id: SafeID
    name: Nonempty
    arguments: str
    status: Literal["pending", "accepted"]
    result: str | None = None
    expires_at: str


class RunDetailResponse(Contract):
    run: RunSummary
    snapshot: Graph
    activations: list[ActivationView]
    pending_tools: list[PendingToolView]
    output: JsonValue = None
    error: ErrorDetail | None = None


class RunEvent(Contract):
    run_id: Nonempty
    event_id: PositiveInt
    type: Literal[
        "run.queued",
        "run.running",
        "run.waiting_tools",
        "run.completed",
        "run.failed",
        "run.cancelled",
        "run.interrupted",
        "activation.ready",
        "activation.running",
        "activation.completed",
        "activation.waiting_tools",
        "activation.failed",
        "activation.cancelled",
        "loop.continued",
        "loop.stopped",
        "tools.accepted",
    ]
    created_at: str
    payload: dict[str, JsonValue]


class HealthResponse(Contract):
    status: Literal["ok", "unavailable"]
    storage_ready: bool
    ollama_available: bool


PUBLIC_MODELS = (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ModelsResponse,
    GraphListResponse,
    SaveGraphRequest,
    PublishGraphRequest,
    PublishGraphResponse,
    ValidationReport,
    StartRunRequest,
    StartRunResponse,
    ToolResultsRequest,
    ToolResultsResponse,
    RunListResponse,
    RunDetailResponse,
    RunEvent,
    HealthResponse,
)
