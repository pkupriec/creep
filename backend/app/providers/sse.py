"""Strict OpenAI SSE framing and indexed tool-delta validation.

Only the same known transport metadata as the JSON boundary is removed.
Arguments remain raw fragments; indices, finish reasons and usage are preserved.
Invalid/unfinished streams raise CGError so the HTTP owner can emit its error
event without a fabricated successful finish or DONE marker.
Wire lines use only CR, LF and CRLF. Incremental UTF-8 decoding rejects invalid
bytes rather than replacing them, preserving literal Unicode text separators.
"""

import codecs
import io
import json
import re
from collections.abc import AsyncIterator

import httpx
from pydantic import ValidationError

from app.contracts.api import ChatCompletionChunk, ChatCompletionResponse, Usage
from app.contracts.config import MAX_REQUEST_BYTES
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import canonical_json


def invalid_stream() -> CGError:
    return CGError(ErrorCode.UPSTREAM_ERROR, "Invalid upstream completion stream")


def strict_json(value: str | bytes) -> object:
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = item
        return result

    def finite(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(value, object_pairs_hook=unique, parse_constant=finite)


def normalize_chunk(value: object) -> ChatCompletionChunk:
    if not isinstance(value, dict):
        raise ValueError("Expected chunk object")
    value = dict(value)
    if "system_fingerprint" in value:
        fingerprint = value.pop("system_fingerprint")
        if fingerprint is not None and not isinstance(fingerprint, str):
            raise ValueError("Invalid fingerprint")
    if isinstance(value.get("usage"), dict):
        usage = dict(value["usage"])
        if "prompt_tokens_details" in usage:
            details = usage.pop("prompt_tokens_details")
            if details is not None:
                if not isinstance(details, dict) or set(details) - {"cached_tokens"}:
                    raise ValueError("Invalid prompt metadata")
                cached = details.get("cached_tokens")
                if cached is not None and (type(cached) is not int or cached < 0):
                    raise ValueError("Invalid cached token count")
        value["usage"] = Usage.model_validate(usage).model_dump(mode="json")
    if isinstance(value.get("choices"), list):
        choices = []
        for original in value["choices"]:
            if not isinstance(original, dict):
                raise ValueError("Invalid stream choice")
            choice = dict(original)
            if isinstance(choice.get("delta"), dict):
                delta = dict(choice["delta"])
                if "reasoning" in delta:
                    # Ollama default thinking emits this private hidden field.
                    reasoning = delta.pop("reasoning")
                    if reasoning is not None and not isinstance(reasoning, str):
                        raise ValueError("Invalid hidden reasoning metadata")
                choice["delta"] = delta
            choices.append(choice)
        value["choices"] = choices
    return ChatCompletionChunk.model_validate(value)


class StreamState:
    def __init__(self):
        self.identity: tuple[str, int, str] | None = None
        self.finished = False
        self.content = ""
        self.has_content = False
        self.tools: dict[int, dict] = {}

    def consume(self, chunk: ChatCompletionChunk) -> None:
        identity = (chunk.id, chunk.created, chunk.model)
        if self.identity is not None and self.identity != identity:
            raise ValueError("Stream identity changed")
        self.identity = identity
        if not chunk.choices:
            if chunk.usage is None:
                raise ValueError("Empty chunk requires usage")
            return
        choice = chunk.choices[0]
        delta = choice.delta
        if self.finished:
            raise ValueError("Choice arrived after finish")
        if delta.content is not None:
            self.has_content = True
            self.content += delta.content
        for fragment in delta.tool_calls or []:
            call = self.tools.setdefault(fragment.index, {"name": "", "arguments": ""})
            if fragment.id is not None:
                if not fragment.id or "id" in call and call["id"] != fragment.id:
                    raise ValueError("Invalid changing tool identity")
                call["id"] = fragment.id
            if fragment.function is not None:
                call["name"] += fragment.function.name or ""
                call["arguments"] += fragment.function.arguments or ""
        if choice.finish_reason is not None:
            calls = []
            if sorted(self.tools) != list(range(len(self.tools))):
                raise ValueError("Tool indices must be contiguous")
            for index in sorted(self.tools):
                call = self.tools[index]
                calls.append(
                    {
                        "id": call.get("id"),
                        "type": "function",
                        "function": {"name": call["name"], "arguments": call["arguments"]},
                    }
                )
            if len({call["id"] for call in calls}) != len(calls):
                raise ValueError("Duplicate tool IDs")
            message = {"role": "assistant", "content": self.content if self.has_content else None}
            if calls:
                message["tool_calls"] = calls
            ChatCompletionResponse.model_validate(
                {
                    "id": chunk.id,
                    "created": chunk.created,
                    "model": chunk.model,
                    "choices": [
                        {"index": 0, "message": message, "finish_reason": choice.finish_reason}
                    ],
                }
            )
            self.finished = True


async def _strict_utf8_lines(response: httpx.Response) -> AsyncIterator[str]:
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    line = io.StringIO()
    size = 0
    skip_lf = False
    try:
        async for raw in response.aiter_bytes():
            # Bound temporary splits without buffering until a transport chunk
            # fills: a short complete event must be emitted immediately.
            for start in range(0, len(raw), 4096):
                for fragment in re.split(rb"([\r\n])", raw[start : start + 4096]):
                    if fragment in {b"\r", b"\n"}:
                        if fragment == b"\n" and skip_lf:
                            skip_lf = False
                            continue
                        skip_lf = fragment == b"\r"
                        line.write(decoder.decode(b"", final=True))
                        value = line.getvalue()
                        line.seek(0)
                        line.truncate(0)
                        decoder.reset()
                        size = 0
                        yield value
                    elif fragment:
                        skip_lf = False
                        size += len(fragment)
                        if size > MAX_REQUEST_BYTES:
                            raise ValueError("Oversize stream line")
                        line.write(decoder.decode(fragment, final=False))
        line.write(decoder.decode(b"", final=True))
        if size:
            yield line.getvalue()
    finally:
        line.close()


async def validated_stream(response: httpx.Response) -> AsyncIterator[bytes]:
    state = StreamState()
    data: list[str] = []
    size = 0

    def event():
        nonlocal size
        body = "\n".join(data)
        data.clear()
        size = 0
        if body == "[DONE]":
            if not state.finished:
                raise ValueError("DONE before completion")
            return None
        chunk = normalize_chunk(strict_json(body))
        state.consume(chunk)
        return (
            b"data: "
            + canonical_json(chunk.model_dump(mode="json", exclude_none=True)).encode("utf-8")
            + b"\n\n"
        )

    lines = _strict_utf8_lines(response)
    try:
        async for line in lines:
            if not line:
                if data:
                    part = event()
                    if part is None:
                        yield b"data: [DONE]\n\n"
                        return
                    yield part
            elif line.startswith(":"):
                continue
            else:
                field, _, value = line.partition(":")
                value = value.removeprefix(" ")
                if field == "data":
                    size += len(value.encode("utf-8")) + (1 if data else 0)
                    if size > MAX_REQUEST_BYTES:
                        raise ValueError("Oversize stream event")
                    data.append(value)
                elif field == "event" and value in {"message", ""}:
                    continue
                else:
                    raise ValueError("Unsupported upstream stream event")
        raise ValueError("Upstream closed before DONE")
    except (ValueError, ValidationError, UnicodeError):
        raise invalid_stream() from None
    finally:
        await lines.aclose()
