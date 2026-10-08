"""OpenAI JSON/SSE orchestration; runtime work is independent of HTTP waiters.

Only an initial request detaches its unexposed run on disconnect. Continuations
join durable replay claims. Direct calls share admission and the provider's
global limiter, hold leases through stream closure and create no run history.
"""

import asyncio
import uuid
from collections.abc import Awaitable, Callable

from anyio import CancelScope
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.contracts.api import ChatCompletionRequest, ChatCompletionResponse, UserMessage
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import (
    AdmissionController,
    ContinuationRoute,
    GraphRepository,
    GraphRuntime,
    OllamaAdapter,
    ProviderRequest,
    ToolBridge,
    Validator,
    canonical_json,
)
from app.providers.sse import strict_json
from app.tools.bridge import canonical_request_hash

from .runs import submission
from .security import read_body

STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


class ClosingStreamResponse(StreamingResponse):
    """Close suspended iterators even if ASGI send fails between yielded chunks."""

    def __init__(self, *args, cleanup: Callable | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup = cleanup

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            with CancelScope(shield=True):
                await self.body_iterator.aclose()
                if self.cleanup is not None:
                    await self.cleanup()


async def connected_wait(request: Request, operation: Awaitable):
    """Cancellation stops this waiter, never a runtime reducer or shared claim."""
    task = asyncio.ensure_future(operation)
    try:
        while not task.done():
            if await request.is_disconnected():
                raise asyncio.CancelledError
            await asyncio.wait({task}, timeout=0.05)
        return await task
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


def data_event(value: dict) -> bytes:
    return ("data: " + canonical_json(value) + "\n\n").encode("utf-8")


def error_event(error: CGError) -> bytes:
    return ("event: error\ndata: " + error.payload().model_dump_json() + "\n\n").encode()


def completion_events(completion: ChatCompletionResponse, include_usage: bool):
    """Render a validated final payload or durable tool envelope, never control."""
    base = {
        "id": completion.id,
        "object": "chat.completion.chunk",
        "created": completion.created,
        "model": completion.model,
    }
    yield data_event(
        {**base, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]}
    )
    choice = completion.choices[0]
    message = choice.message
    if message.content is not None:
        content = (
            message.content
            if isinstance(message.content, str)
            else "".join(part.text for part in message.content)
        )
        yield data_event(
            {
                **base,
                "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
            }
        )
    if message.tool_calls:
        for index, call in enumerate(message.tool_calls):
            yield data_event(
                {
                    **base,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "tool_calls": [{"index": index, **call.model_dump(mode="json")}]
                            },
                            "finish_reason": None,
                        }
                    ],
                }
            )
    yield data_event(
        {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": choice.finish_reason}]}
    )
    if include_usage and completion.usage is not None:
        yield data_event({**base, "choices": [], "usage": completion.usage.model_dump()})
    yield b"data: [DONE]\n\n"


def client_chat_input(request: ChatCompletionRequest) -> str:
    for message in reversed(request.messages):
        if isinstance(message, UserMessage):
            return (
                message.content
                if isinstance(message.content, str)
                else "".join(part.text for part in message.content)
            )
    raise CGError(ErrorCode.INVALID_PARAMETER, "A new graph turn requires a user message.")


def create_chat_router(
    settings: Settings,
    graphs: GraphRepository,
    validator: Validator,
    provider: OllamaAdapter,
    runtime: GraphRuntime,
    bridge: ToolBridge,
    admission: AdmissionController,
    authorize: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/v1")

    async def direct(request: Request, body: ChatCompletionRequest):
        lease = await admission.acquire("direct_" + uuid.uuid4().hex)
        wire = ProviderRequest.model_validate(
            {
                **body.model_dump(mode="json", by_alias=True),
                "model": body.model.removeprefix("ollama/"),
            }
        )
        if not body.stream:
            try:
                await connected_wait(request, lease.wait())
                async with asyncio.timeout(settings.run_active_timeout_seconds):
                    completion = await connected_wait(request, provider.complete(wire))
                return JSONResponse(
                    completion.model_copy(update={"model": body.model}).model_dump(
                        mode="json", exclude_none=True
                    )
                )
            except TimeoutError:
                raise CGError(
                    ErrorCode.RUN_TIMEOUT, "Direct request active budget expired."
                ) from None
            finally:
                await lease.release()
        parts = provider.stream(wire)
        try:
            await connected_wait(request, lease.wait())
            deadline = asyncio.get_running_loop().time() + settings.run_active_timeout_seconds
            async with asyncio.timeout_at(deadline):
                first = await connected_wait(request, anext(parts))
        except BaseException as error:
            with CancelScope(shield=True):
                await parts.aclose()
                await lease.release()
            if isinstance(error, TimeoutError):
                raise CGError(ErrorCode.RUN_TIMEOUT, "Direct active budget expired.") from None
            raise

        def translate(part):
            if part == b"data: [DONE]\n\n":
                return part
            value = strict_json(part[6:].strip())
            value["model"] = body.model
            return data_event(value)

        async def stream():
            try:
                yield translate(first)
                while True:
                    if asyncio.get_running_loop().time() >= deadline:
                        raise CGError(
                            ErrorCode.RUN_TIMEOUT, "Direct request active budget expired."
                        )
                    try:
                        async with asyncio.timeout_at(deadline):
                            part = await anext(parts)
                    except StopAsyncIteration:
                        return
                    yield translate(part)
            except TimeoutError:
                yield error_event(
                    CGError(ErrorCode.RUN_TIMEOUT, "Direct request active budget expired.")
                )
            except CGError as error:
                yield error_event(error)

        async def cleanup():
            try:
                await parts.aclose()
            finally:
                await lease.release()

        return ClosingStreamResponse(
            stream(), cleanup=cleanup, media_type="text/event-stream", headers=STREAM_HEADERS
        )

    @router.post("/chat/completions")
    async def chat(request: Request, namespace: str = Depends(authorize)):
        body = await read_body(request, ChatCompletionRequest)
        route = await bridge.classify(body, namespace)
        if body.model.startswith("ollama/"):
            return await direct(request, body)
        initial = not isinstance(route, ContinuationRoute)
        if initial:
            try:
                snapshot = await graphs.load_snapshot(body.model[3:], published_only=True)
            except CGError as error:
                if error.code == ErrorCode.GRAPH_NOT_FOUND:
                    raise CGError(
                        ErrorCode.UNKNOWN_MODEL, "Published graph model not found."
                    ) from None
                raise
            inputs = {"chat": client_chat_input(body)}
            # Graphs may omit a chat declaration; fail clearly rather than drop input.
            run = await runtime.submit(
                submission(settings, validator, snapshot, namespace, inputs, body)
            )
            run_id = run.run_id

            def operation():
                return runtime.await_response(run_id, namespace)
        else:
            acceptance = await bridge.accept(route, canonical_request_hash(body))
            await runtime.resume(acceptance)
            run_id = route.run_id

            def operation():
                return bridge.await_response(acceptance.claim.claim_id)

        headers = {"X-CG-Run-ID": run_id}
        if not body.stream:
            try:
                envelope = await connected_wait(request, operation())
            except asyncio.CancelledError:
                if initial:
                    await runtime.detach_initial(run_id, namespace)
                raise
            return JSONResponse(
                envelope.completion().model_dump(mode="json", exclude_none=True), headers=headers
            )

        async def stream():
            try:
                envelope = await operation()
                include_usage = (
                    body.stream_options is not None and body.stream_options.include_usage
                )
                for part in completion_events(envelope.completion(), include_usage):
                    yield part
            except CGError as error:
                yield error_event(error)

        async def cleanup():
            # Completed or exposed runs are unchanged by the atomic detach guard.
            if initial:
                await runtime.detach_initial(run_id, namespace)

        return ClosingStreamResponse(
            stream(),
            cleanup=cleanup,
            media_type="text/event-stream",
            headers={**STREAM_HEADERS, **headers},
        )

    return router
