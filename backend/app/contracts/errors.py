"""Stable sanitized API errors. Never use raw provider exception text as message."""

from enum import StrEnum

from .graph import Contract


class ErrorCode(StrEnum):
    GRAPH_VALIDATION_FAILED = "graph_validation_failed"
    INVALID_PARAMETER = "invalid_parameter"
    UNSUPPORTED_PARAMETER = "unsupported_parameter"
    UNSUPPORTED_TOOL_CHOICE = "unsupported_tool_choice"
    UNKNOWN_MODEL = "unknown_model"
    GRAPH_NOT_FOUND = "graph_not_found"
    RUN_NOT_FOUND = "run_not_found"
    REVISION_CONFLICT = "revision_conflict"
    CONTINUATION_CONFLICT = "continuation_conflict"
    UNKNOWN_TOOL_CALL = "unknown_tool_call"
    AMBIGUOUS_CONTINUATION = "ambiguous_continuation"
    RUN_TERMINAL = "run_terminal"
    QUEUE_FULL = "queue_full"
    UPSTREAM_ERROR = "upstream_error"
    OLLAMA_UNAVAILABLE = "ollama_unavailable"
    LLM_TIMEOUT = "llm_timeout"
    RUN_TIMEOUT = "run_timeout"
    TOOL_WAIT_TIMEOUT = "tool_wait_timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    INTERRUPTED = "interrupted"
    CANCELLED = "cancelled"
    CONTEXT_OVERFLOW = "context_overflow"
    STORAGE_ERROR = "storage_error"
    UNAUTHORIZED = "unauthorized"
    REQUEST_TOO_LARGE = "request_too_large"


ERROR_STATUS: dict[ErrorCode, int] = {
    ErrorCode.GRAPH_VALIDATION_FAILED: 400,
    ErrorCode.INVALID_PARAMETER: 400,
    ErrorCode.UNSUPPORTED_PARAMETER: 400,
    ErrorCode.UNSUPPORTED_TOOL_CHOICE: 400,
    ErrorCode.UNKNOWN_MODEL: 404,
    ErrorCode.GRAPH_NOT_FOUND: 404,
    ErrorCode.RUN_NOT_FOUND: 404,
    ErrorCode.REVISION_CONFLICT: 409,
    ErrorCode.CONTINUATION_CONFLICT: 409,
    ErrorCode.UNKNOWN_TOOL_CALL: 409,
    ErrorCode.AMBIGUOUS_CONTINUATION: 409,
    ErrorCode.RUN_TERMINAL: 409,
    ErrorCode.QUEUE_FULL: 429,
    ErrorCode.UPSTREAM_ERROR: 502,
    ErrorCode.OLLAMA_UNAVAILABLE: 503,
    ErrorCode.LLM_TIMEOUT: 504,
    ErrorCode.RUN_TIMEOUT: 504,
    ErrorCode.TOOL_WAIT_TIMEOUT: 504,
    ErrorCode.BUDGET_EXCEEDED: 400,
    ErrorCode.INTERRUPTED: 409,
    ErrorCode.CANCELLED: 409,
    ErrorCode.CONTEXT_OVERFLOW: 400,
    ErrorCode.STORAGE_ERROR: 500,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.REQUEST_TOO_LARGE: 413,
}


class ErrorDetail(Contract):
    message: str
    type: str
    code: str


class ErrorResponse(Contract):
    error: ErrorDetail


class CGError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = ERROR_STATUS[code]

    def payload(self) -> ErrorResponse:
        error_type = "invalid_request_error"
        if self.status_code == 401:
            error_type = "authentication_error"
        elif self.status_code == 429:
            error_type = "rate_limit_error"
        elif self.status_code >= 500:
            error_type = "server_error"
        return ErrorResponse(
            error=ErrorDetail(message=self.message, type=error_type, code=self.code.value)
        )
