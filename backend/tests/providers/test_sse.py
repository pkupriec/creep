import asyncio
import json

import httpx
import pytest

from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import ProviderRequest
from app.providers.ollama import HttpOllamaAdapter


def chunk(delta=None, finish=None, **extra):
    return {
        "id": "c",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": "fixture",
        "choices": [{"index": 0, "delta": delta or {}, "finish_reason": finish}],
        **extra,
    }


def wire(*events):
    return "".join(
        "data: " + (event if isinstance(event, str) else json.dumps(event)) + "\r\n\r\n"
        for event in events
    ).encode()


async def collect(body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, content=body, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        return [
            part
            async for part in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            )
        ]


async def test_fragmented_tool_arguments_and_known_metadata():
    raw = '{"file": "a.txt"}'
    events = [
        chunk({"role": "assistant"}, system_fingerprint="known"),
        chunk(
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "internal",
                        "type": "function",
                        "function": {"name": "read", "arguments": raw[:8]},
                    }
                ]
            }
        ),
        chunk({"tool_calls": [{"index": 0, "function": {"arguments": raw[8:]}}]}),
        chunk(
            finish="tool_calls",
            usage={
                "prompt_tokens": 1,
                "completion_tokens": 2,
                "total_tokens": 3,
                "prompt_tokens_details": {"cached_tokens": 0},
            },
        ),
        "[DONE]",
    ]
    parts = await collect(wire(*events))
    decoded = [json.loads(part.decode().removeprefix("data: ").strip()) for part in parts[:-1]]
    assert "system_fingerprint" not in decoded[0]
    assert "prompt_tokens_details" not in decoded[-1]["usage"]
    calls = [c for item in decoded for c in item["choices"][0]["delta"].get("tool_calls", [])]
    assert "".join(c["function"].get("arguments", "") for c in calls) == raw
    assert calls[0]["id"] == "internal" and parts[-1] == b"data: [DONE]\n\n"


@pytest.mark.parametrize(
    "body",
    [
        wire(chunk({"content": "x"})),
        wire("[DONE]"),
        wire(chunk(finish="stop")),
        wire(chunk({"content": "x"}, extra_semantic=True), "[DONE]"),
        wire(chunk(finish="stop"), chunk({"content": "after"}), "[DONE]"),
        wire(
            chunk(
                {"tool_calls": [{"index": 1, "function": {"arguments": "{}"}}]}, finish="tool_calls"
            ),
            "[DONE]",
        ),
        b"data: {oops}\n\n",
        wire(chunk({"content": "x"}, finish="tool_calls"), "[DONE]"),
    ],
)
async def test_incomplete_or_invalid_stream_never_becomes_success(body):
    with pytest.raises(CGError):
        await collect(body)


class HeldStream(httpx.AsyncByteStream):
    def __init__(self):
        self.closed = False

    async def __aiter__(self):
        yield wire(chunk({"content": "first"}))
        await asyncio.Event().wait()

    async def aclose(self):
        self.closed = True


async def test_close_retains_then_releases_stream_permit_and_transport():
    upstream = HeldStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        limiter = asyncio.Semaphore(1)
        adapter = HttpOllamaAdapter(Settings(), client=client, limiter=limiter)
        stream = adapter.stream(
            ProviderRequest(
                model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
            )
        )
        assert await anext(stream)
        assert limiter.locked() and not upstream.closed
        await stream.aclose()
        assert not limiter.locked() and upstream.closed and not client.is_closed


async def test_usage_only_chunk_after_finish_and_heartbeats():
    body = b": keepalive\n\n" + wire(
        chunk({"content": "answer"}, finish="length"),
        {
            "id": "c",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "fixture",
            "choices": [],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        },
        "[DONE]",
    )
    parts = await collect(body)
    assert len(parts) == 3
    assert b'"finish_reason":"length"' in parts[0]
    assert b'"total_tokens":5' in parts[1]


async def test_known_hidden_reasoning_is_excluded_visible_text_preserved():
    parts = await collect(
        wire(
            chunk({"role": "assistant", "reasoning": "private thought"}),
            chunk({"content": "visible", "reasoning": None}, finish="stop"),
            "[DONE]",
        )
    )
    assert b"private thought" not in b"".join(parts)
    assert b"reasoning" not in b"".join(parts) and b"visible" in b"".join(parts)


@pytest.mark.parametrize("reasoning", [42, [], {}, True])
async def test_hidden_reasoning_metadata_remains_strict(reasoning):
    with pytest.raises(CGError):
        await collect(
            wire(chunk({"content": "visible", "reasoning": reasoning}, finish="stop"), "[DONE]")
        )


class ByteFragments(httpx.AsyncByteStream):
    async def __aiter__(self):
        for byte in wire(chunk({"content": "Привіт"}, finish="stop"), "[DONE]"):
            yield bytes([byte])


async def test_transport_fragments_include_multibyte_utf8():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=ByteFragments(), headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        parts = [
            p
            async for p in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            )
        ]
        assert "Привіт" in parts[0].decode() and parts[-1] == b"data: [DONE]\n\n"


@pytest.mark.parametrize(
    "events",
    [
        [chunk({"content": "x"}), chunk({"content": "y"}, id="changed"), "[DONE]"],
        [chunk({"content": "x"}, system_fingerprint=1), "[DONE]"],
        [
            chunk(
                {"content": "x"},
                usage={
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                    "prompt_tokens_details": {"cached_tokens": True},
                },
            ),
            "[DONE]",
        ],
        [
            chunk(
                {
                    "tool_calls": [
                        {"index": 0, "id": "one", "function": {"name": "read", "arguments": "{}"}}
                    ]
                }
            ),
            chunk({"tool_calls": [{"index": 0, "id": "different"}]}, finish="tool_calls"),
            "[DONE]",
        ],
    ],
)
async def test_stream_semantic_changes_are_rejected(events):
    with pytest.raises(CGError):
        await collect(wire(*events))


@pytest.mark.parametrize(
    "status,content_type", [(500, "text/event-stream"), (200, "application/json")]
)
async def test_stream_failure_releases_permit(status, content_type):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                status, content=b"SECRET", headers={"content-type": content_type}
            )
        )
    ) as client:
        limiter = asyncio.Semaphore(1)
        adapter = HttpOllamaAdapter(Settings(), client=client, limiter=limiter)
        with pytest.raises(CGError) as caught:
            async for _ in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            ):
                pass
        assert caught.value.code == ErrorCode.UPSTREAM_ERROR and "SECRET" not in str(caught.value)
        assert not limiter.locked() and not client.is_closed


async def test_stream_deadline_and_cancel_close_transport_release_permit():
    upstream = HeldStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        limiter = asyncio.Semaphore(1)
        adapter = HttpOllamaAdapter(Settings(llm_timeout_seconds=1), client=client, limiter=limiter)
        request_ = ProviderRequest(
            model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
        )
        stream = adapter.stream(request_)
        await anext(stream)
        with pytest.raises(CGError) as caught:
            await anext(stream)
        assert (
            caught.value.code == ErrorCode.LLM_TIMEOUT and upstream.closed and not limiter.locked()
        )


async def test_stream_consumer_cancel_closes_upstream():
    upstream = HeldStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        limiter = asyncio.Semaphore(1)
        adapter = HttpOllamaAdapter(Settings(), client=client, limiter=limiter)
        stream = adapter.stream(
            ProviderRequest(
                model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
            )
        )
        await anext(stream)
        consumer = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        consumer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer
        assert upstream.closed and not limiter.locked()


async def test_stream_deadline_does_not_cancel_consumer_between_pulls():
    upstream = HeldStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(llm_timeout_seconds=1), client=client)
        stream = adapter.stream(
            ProviderRequest(
                model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
            )
        )
        try:
            await anext(stream)
            await asyncio.sleep(1.05)
            with pytest.raises(CGError) as caught:
                await anext(stream)
            assert caught.value.code == ErrorCode.LLM_TIMEOUT
        finally:
            await stream.aclose()


class WireFragments(httpx.AsyncByteStream):
    def __init__(self, fragments):
        self.fragments = fragments
        self.closed = False
        self.reads = 0

    async def __aiter__(self):
        for fragment in self.fragments:
            self.reads += 1
            yield fragment

    async def aclose(self):
        self.closed = True


def literal_wire(*events, ending=b"\n"):
    """Real UTF-8 literals, unlike json.dumps' default ASCII escapes."""
    return b"".join(
        b"data: "
        + (
            event.encode()
            if isinstance(event, str)
            else json.dumps(event, ensure_ascii=False).encode("utf-8")
        )
        + ending * 2
        for event in events
    )


@pytest.mark.parametrize("ending", [b"\n", b"\r", b"\r\n"])
@pytest.mark.parametrize("text", ["a\u0085b", "a\u2028b", "a\u2029b", "café Привіт 😀\r\n"])
async def test_strict_wire_literal_unicode_and_fragmented_crlf(ending, text):
    raw = literal_wire(chunk({"content": text}, finish="stop"), "[DONE]", ending=ending)
    upstream = WireFragments([bytes([byte]) for byte in raw])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        parts = [
            part
            async for part in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            )
        ]
        assert json.loads(parts[0].decode()[6:])["choices"][0]["delta"]["content"] == text
        assert parts[-1] == b"data: [DONE]\n\n" and upstream.closed
        assert adapter.limiter._value == 2


async def test_strict_wire_preserves_literal_unicode_raw_tool_fragments():
    arguments = ' { "value" : "é\u0085\u2028\u2029😀" } '
    raw = literal_wire(
        chunk(
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "native😀",
                        "type": "function",
                        "function": {"name": "readé", "arguments": arguments[:12]},
                    }
                ]
            }
        ),
        chunk(
            {"tool_calls": [{"index": 0, "function": {"arguments": arguments[12:]}}]},
            finish="tool_calls",
        ),
        "[DONE]",
    )
    upstream = WireFragments([bytes([byte]) for byte in raw])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        parts = [
            part
            async for part in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            )
        ]
        calls = [
            call
            for part in parts[:-1]
            for choice in json.loads(part.decode()[6:])["choices"]
            for call in choice["delta"].get("tool_calls", [])
        ]
        assert "".join(call["function"]["arguments"] for call in calls) == arguments
        assert calls[0]["id"] == "native😀" and calls[0]["function"]["name"] == "readé"
        assert parts[-1] == b"data: [DONE]\n\n" and upstream.closed


@pytest.mark.parametrize("kind", ["content", "arguments"])
@pytest.mark.parametrize("bad", [b"\xff", b"\xc3(", b"\xed\xa0\x80", b"\xf0\x9f"])
@pytest.mark.parametrize("started", [False, True])
async def test_strict_wire_malformed_utf8_public_error_cleanup(tmp_path, kind, bad, started):
    from tests.api.test_chat import chat, harness

    if kind == "content":
        event = chunk({"content": "MARK"}, finish="stop")
    else:
        event = chunk(
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "native",
                        "type": "function",
                        "function": {"name": "read", "arguments": "MARK"},
                    }
                ]
            },
            finish="tool_calls",
        )
    malformed = literal_wire(event, "[DONE]").replace(b"MARK", bad)
    if bad == b"\xf0\x9f":
        malformed = malformed[: malformed.index(bad)] + bad  # Truncated UTF-8 at actual EOF.
    prefix = literal_wire(chunk({"content": "already visible"})) if started else b""
    upstream = WireFragments([prefix, malformed] if started else [malformed])

    async def handle(_):
        return httpx.Response(200, stream=upstream, headers={"content-type": "text/event-stream"})

    async with harness(tmp_path, handle) as (app, _, calls):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            result = await client.post(
                "/v1/chat/completions", json=chat("ollama/fixture", stream=True)
            )
        assert result.status_code == (200 if started else 502)
        if started:
            assert "already visible" in result.text and "event: error\n" in result.text
            assert '"code":"upstream_error"' in result.text
        else:
            assert result.json()["error"]["code"] == "upstream_error"
        assert "[DONE]" not in result.text and '"finish_reason":"stop"' not in result.text
        assert '"finish_reason":"tool_calls"' not in result.text and "\ufffd" not in result.text
        assert len(calls) == 1 and upstream.closed
        assert not app.state.admission.leases and app.state.provider.limiter._value == 2


async def test_strict_wire_line_buffer_rejects_before_consuming_remainder(monkeypatch):
    import app.providers.sse as sse

    monkeypatch.setattr(sse, "MAX_REQUEST_BYTES", 128)
    upstream = WireFragments([b":" + b"x" * 80, b"x" * 80, b"unread"])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, stream=upstream, headers={"content-type": "text/event-stream"}
            )
        )
    ) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        with pytest.raises(CGError) as caught:
            async for _ in adapter.stream(
                ProviderRequest(
                    model="fixture", messages=[{"role": "user", "content": "hello"}], stream=True
                )
            ):
                pass
        assert caught.value.code == ErrorCode.UPSTREAM_ERROR and upstream.reads == 2
        assert upstream.closed and adapter.limiter._value == 2


async def test_strict_wire_multiline_event_limit_includes_joined_newlines(monkeypatch):
    import app.providers.sse as sse

    pretty = json.dumps(chunk({"content": "ok"}, finish="stop"), indent=2)
    monkeypatch.setattr(sse, "MAX_REQUEST_BYTES", len(pretty.encode()) - 1)
    raw = b"".join(b"data: " + line.encode() + b"\n" for line in pretty.split("\n"))
    raw += b"\ndata: [DONE]\n\n"
    with pytest.raises(CGError) as caught:
        await collect(raw)
    assert caught.value.code == ErrorCode.UPSTREAM_ERROR


@pytest.mark.parametrize("text", ["a\u0085b", "a\u2028b", "a\u2029b", "café Привіт 😀"])
async def test_strict_wire_valid_unicode_public_response_preserved(tmp_path, text):
    from tests.api.test_chat import chat, harness

    raw = literal_wire(chunk({"content": text}, finish="stop"), "[DONE]")
    upstream = WireFragments([bytes([byte]) for byte in raw])

    async def handle(_):
        return httpx.Response(200, stream=upstream, headers={"content-type": "text/event-stream"})

    async with harness(tmp_path, handle) as (app, client, calls):
        result = await client.post("/v1/chat/completions", json=chat("ollama/fixture", stream=True))
        assert result.status_code == 200 and result.content.endswith(b"data: [DONE]\n\n")
        events = [
            json.loads(event[6:])
            for event in result.text.split("\n\n")
            if event.startswith("data: {")
        ]
        assert events[0]["choices"][0]["delta"]["content"] == text
        assert events[0]["model"] == "ollama/fixture"
        assert len(calls) == 1 and upstream.closed
        assert not app.state.admission.leases and app.state.provider.limiter._value == 2


@pytest.mark.parametrize("started", [False, True])
@pytest.mark.parametrize("kind", ["content", "arguments"])
@pytest.mark.parametrize("bad", ["\ud800", "\udfff"])
async def test_strict_wire_escaped_unpaired_scalars_public_error(tmp_path, kind, bad, started):
    from tests.api.test_chat import chat, harness

    if kind == "content":
        event = chunk({"content": bad}, finish="stop")
    else:
        event = chunk(
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "native",
                        "type": "function",
                        "function": {"name": "read", "arguments": '{ "value": "' + bad + '" }'},
                    }
                ]
            },
            finish="tool_calls",
        )
    prefix = wire(chunk({"content": "already visible"})) if started else b""
    upstream = WireFragments([prefix, wire(event, "[DONE]")])

    async def handle(_):
        return httpx.Response(200, stream=upstream, headers={"content-type": "text/event-stream"})

    async with harness(tmp_path, handle) as (app, client, calls):
        result = await client.post("/v1/chat/completions", json=chat("ollama/fixture", stream=True))
        assert result.status_code == (200 if started else 502)
        assert '"code":"upstream_error"' in result.text
        assert "[DONE]" not in result.text and '"finish_reason":"stop"' not in result.text
        assert '"finish_reason":"tool_calls"' not in result.text
        assert len(calls) == 1 and upstream.closed
        assert not app.state.admission.leases and app.state.provider.limiter._value == 2
