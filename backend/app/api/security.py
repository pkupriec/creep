"""Shared bearer authorization and bounded, strict JSON request parsing.

Both API surfaces derive the same configured-token namespace. Health probes
remain public. Request errors expose neither submitted values nor credentials.
"""

import hmac
from collections.abc import Callable
from typing import TypeVar

from fastapi import Request
from pydantic import BaseModel, ValidationError
from starlette.types import ASGIApp, Receive, Scope, Send

from app.contracts.api import ChatCompletionRequest, StartRunRequest, ToolMessage
from app.contracts.config import MAX_REQUEST_BYTES, Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import canonical_json
from app.providers.sse import strict_json
from app.tools.bridge import validate_result

DTO = TypeVar("DTO", bound=BaseModel)


def authorization(settings: Settings) -> Callable:
    """Compare raw UTF-8 bytes safely; never retain the supplied token."""

    async def authorize(request: Request) -> str:
        if settings.api_token is not None:
            headers = [
                value for key, value in request.scope["headers"] if key.lower() == b"authorization"
            ]
            expected = settings.api_token.get_secret_value().encode("utf-8")
            valid = False
            if len(headers) == 1:
                scheme, separator, supplied = headers[0].partition(b" ")
                valid = (
                    scheme.lower() == b"bearer"
                    and bool(separator)
                    and hmac.compare_digest(supplied, expected)
                )
            if not valid:
                raise CGError(ErrorCode.UNAUTHORIZED, "Bearer authentication is required.")
        return settings.caller_namespace()

    return authorize


class BodyLimitMiddleware:
    """Bound chunked bodies before any route, including graph management."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > MAX_REQUEST_BYTES:
                error = CGError(ErrorCode.REQUEST_TOO_LARGE, "Request exceeds the size limit.")
                from fastapi.responses import JSONResponse

                return await JSONResponse(error.payload().model_dump(mode="json"), status_code=413)(
                    scope, receive, send
                )
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)


async def read_body(request: Request, model: type[DTO]) -> DTO:
    """Reject duplicates, nonfinite numbers, invalid UTF-8 and semantic extras."""
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            raise CGError(ErrorCode.REQUEST_TOO_LARGE, "Request exceeds the size limit.")
        chunks.append(chunk)
    try:
        payload = strict_json(b"".join(chunks))
        canonical_json(payload).encode("utf-8")
        result = model.model_validate(payload)
    except ValidationError as exc:
        code = (
            ErrorCode.UNSUPPORTED_PARAMETER
            if any(error["type"] == "extra_forbidden" for error in exc.errors(include_input=False))
            else ErrorCode.INVALID_PARAMETER
        )
        raise CGError(code, "Invalid or unsupported request parameters.") from None
    except (ValueError, UnicodeError, RecursionError):
        raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid JSON request body.") from None
    if isinstance(result, ChatCompletionRequest | StartRunRequest):
        for message in result.messages:
            if isinstance(message, ToolMessage):
                validate_result(message.content)
    return result
