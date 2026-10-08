"""Bounded external Ollama Chat Completions transport, without retries or tools.

Inject one shared instance (or semaphore) into graph and direct paths. A stream
consumer must await generator.aclose() on disconnect; the permit spans the whole
exchange. close() only closes the HTTP client constructed by this adapter.
Normalized completion strings must encode as strict UTF-8 before crossing this
boundary; malformed provider scalars are upstream errors, not storage failures.
"""

import asyncio
from collections.abc import AsyncGenerator

import httpx
from pydantic import ValidationError

from app.contracts.api import ChatCompletionResponse
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import ProviderRequest, canonical_json

from .sse import strict_json, validated_stream


class HttpOllamaAdapter:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        limiter: asyncio.Semaphore | None = None,
    ):
        self.settings = settings
        self.client = (
            client
            if client is not None
            else httpx.AsyncClient(
                timeout=settings.llm_timeout_seconds, follow_redirects=False, trust_env=False
            )
        )
        self.owns_client = client is None
        self.limiter = (
            limiter if limiter is not None else asyncio.Semaphore(settings.max_parallel_llm)
        )

    def _url(self, path: str) -> str:
        return self.settings.ollama_base_url + path

    @staticmethod
    def _status(response: httpx.Response) -> None:
        if response.status_code == 404:
            raise CGError(ErrorCode.UNKNOWN_MODEL, "Requested upstream model was not found")
        if not 200 <= response.status_code < 300:
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Upstream rejected the inference request")

    @staticmethod
    def _payload(request: ProviderRequest, stream: bool) -> dict:
        body = request.model_dump(mode="json", by_alias=True, exclude_none=True)
        body["stream"] = stream
        if not stream:
            body.pop("stream_options", None)
        return body

    async def complete(self, request: ProviderRequest) -> ChatCompletionResponse:
        try:
            async with self.limiter:
                async with asyncio.timeout(self.settings.llm_timeout_seconds):
                    response = await self.client.post(
                        self._url("/chat/completions"),
                        json=self._payload(request, False),
                        timeout=self.settings.llm_timeout_seconds,
                        follow_redirects=False,
                    )
                    self._status(response)
                    completion = ChatCompletionResponse.from_upstream(strict_json(response.content))
                    canonical_json(completion.model_dump(mode="json")).encode("utf-8")
                    return completion
        except (TimeoutError, httpx.TimeoutException):
            raise CGError(ErrorCode.LLM_TIMEOUT, "Upstream inference timed out") from None
        except httpx.TransportError:
            raise CGError(ErrorCode.OLLAMA_UNAVAILABLE, "Ollama is unavailable") from None
        except (ValueError, ValidationError, UnicodeError):
            raise CGError(
                ErrorCode.UPSTREAM_ERROR, "Invalid upstream completion response"
            ) from None

    async def stream(self, request: ProviderRequest) -> AsyncGenerator[bytes, None]:
        try:
            async with self.limiter:
                deadline = asyncio.get_running_loop().time() + self.settings.llm_timeout_seconds
                wire = self.client.build_request(
                    "POST",
                    self._url("/chat/completions"),
                    json=self._payload(request, True),
                    timeout=self.settings.llm_timeout_seconds,
                )
                async with asyncio.timeout(self.settings.llm_timeout_seconds):
                    response = await self.client.send(wire, stream=True, follow_redirects=False)
                parts = validated_stream(response)
                try:
                    self._status(response)
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if content_type.strip().lower() != "text/event-stream":
                        raise CGError(ErrorCode.UPSTREAM_ERROR, "Invalid upstream stream type")
                    while True:
                        # A timeout context spanning yield would cancel unrelated
                        # consumer work while this generator is suspended.
                        if asyncio.get_running_loop().time() >= deadline:
                            raise TimeoutError
                        try:
                            async with asyncio.timeout_at(deadline):
                                part = await anext(parts)
                        except StopAsyncIteration:
                            return
                        yield part
                        if part == b"data: [DONE]\n\n":
                            return
                finally:
                    await parts.aclose()
                    await response.aclose()
        except (TimeoutError, httpx.TimeoutException):
            raise CGError(ErrorCode.LLM_TIMEOUT, "Upstream inference timed out") from None
        except httpx.TransportError:
            raise CGError(ErrorCode.OLLAMA_UNAVAILABLE, "Ollama is unavailable") from None

    async def models(self) -> tuple[str, ...]:
        try:
            async with asyncio.timeout(self.settings.llm_timeout_seconds):
                response = await self.client.get(
                    self._url("/models"),
                    timeout=self.settings.llm_timeout_seconds,
                    follow_redirects=False,
                )
                self._status(response)
                body = strict_json(response.content)
                if not isinstance(body, dict) or set(body) != {"object", "data"}:
                    raise ValueError("Invalid model list")
                if body["object"] != "list" or not isinstance(body["data"], list):
                    raise ValueError("Invalid model list")
                names = []
                for model in body["data"]:
                    if not isinstance(model, dict) or set(model) != {
                        "id",
                        "object",
                        "created",
                        "owned_by",
                    }:
                        raise ValueError("Invalid model entry")
                    if (
                        not isinstance(model["id"], str)
                        or not model["id"]
                        or any(char.isspace() for char in model["id"])
                        or model["object"] != "model"
                        or type(model["created"]) is not int
                        or model["created"] < 0
                        or not isinstance(model["owned_by"], str)
                    ):
                        raise ValueError("Invalid model entry")
                    # Inventory strings cross the public JSON boundary through
                    # the models endpoint. Reject escaped surrogate scalars at
                    # the provider boundary instead of leaking a serialization
                    # error from the API response model.
                    model["id"].encode("utf-8")
                    names.append(model["id"])
                if len(set(names)) != len(names):
                    raise ValueError("Duplicate model")
                return tuple(names)
        except (TimeoutError, httpx.TimeoutException):
            raise CGError(ErrorCode.LLM_TIMEOUT, "Upstream inventory timed out") from None
        except httpx.TransportError:
            raise CGError(ErrorCode.OLLAMA_UNAVAILABLE, "Ollama is unavailable") from None
        except (ValueError, UnicodeError):
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Invalid upstream model inventory") from None

    async def health(self) -> bool:
        try:
            await self.models()
            return True
        except CGError:
            return False

    async def close(self) -> None:
        if self.owns_client:
            await self.client.aclose()
