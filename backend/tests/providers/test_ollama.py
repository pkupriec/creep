import asyncio
import json

import httpx
import pytest

from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import ProviderRequest
from app.providers.ollama import HttpOllamaAdapter


def request(**overrides):
    return ProviderRequest.model_validate(
        {"model": "fixture", "messages": [{"role": "user", "content": "hello"}], **overrides}
    )


def completion(**overrides):
    return {
        "id": "c",
        "object": "chat.completion",
        "created": 1,
        "model": "fixture",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "hello"},
                "finish_reason": "stop",
            }
        ],
        **overrides,
    }


async def test_json_preserves_profile_metadata_and_owned_client():
    bodies = []

    async def handle(req):
        bodies.append(json.loads(req.content))
        return httpx.Response(200, json=completion(system_fingerprint="known"))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    adapter = HttpOllamaAdapter(Settings(), client=client)
    result = await adapter.complete(request(temperature=0.3, stop=["END"], max_tokens=9))
    assert result.model == "fixture" and result.choices[0].message.content == "hello"
    assert bodies[0]["temperature"] == 0.3 and bodies[0]["stop"] == ["END"]
    assert bodies[0]["max_tokens"] == 9 and "reasoning_effort" not in bodies[0]
    await adapter.close()
    assert not client.is_closed
    await client.aclose()
    owned = HttpOllamaAdapter(Settings())
    await owned.close()
    assert owned.client.is_closed


@pytest.mark.parametrize(
    "status,code",
    [
        (404, ErrorCode.UNKNOWN_MODEL),
        (500, ErrorCode.UPSTREAM_ERROR),
        (401, ErrorCode.UPSTREAM_ERROR),
    ],
)
async def test_sanitized_http_errors_without_retry(status, code):
    calls = []

    async def handle(req):
        calls.append(req)
        return httpx.Response(status, text="SECRET endpoint token prompt")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        with pytest.raises(CGError) as caught:
            await adapter.complete(request())
        assert caught.value.code == code and "SECRET" not in str(caught.value)
        assert len(calls) == 1


@pytest.mark.parametrize(
    "error,code",
    [
        (httpx.ReadTimeout("SECRET"), ErrorCode.LLM_TIMEOUT),
        (httpx.ConnectError("SECRET"), ErrorCode.OLLAMA_UNAVAILABLE),
    ],
)
async def test_transport_errors(error, code):
    async def handle(req):
        raise error

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(CGError) as caught:
            await HttpOllamaAdapter(Settings(), client=client).complete(request())
        assert caught.value.code == code and "SECRET" not in str(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        completion(extra_semantic=1),
        {"not": "a completion"},
        completion(choices=[]),
        completion(system_fingerprint=9),
    ],
)
async def test_malformed_upstream_is_not_silently_normalized(payload):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=payload))
    ) as client:
        with pytest.raises(CGError, match="Invalid upstream"):
            await HttpOllamaAdapter(Settings(), client=client).complete(request())


async def test_shared_limiter_bounds_graph_and_direct_and_releases_cancel():
    gate = asyncio.Event()
    started = asyncio.Queue()
    active = 0
    peak = 0

    async def handle(req):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        started.put_nowait(req)
        try:
            await gate.wait()
            return httpx.Response(200, json=completion())
        finally:
            active -= 1

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        limiter = asyncio.Semaphore(2)
        graph = HttpOllamaAdapter(Settings(), client=client, limiter=limiter)
        direct = HttpOllamaAdapter(Settings(), client=client, limiter=limiter)
        tasks = [
            asyncio.create_task((graph if i % 2 else direct).complete(request())) for i in range(5)
        ]
        await asyncio.wait_for(started.get(), 1)
        await asyncio.wait_for(started.get(), 1)
        await asyncio.sleep(0)
        assert started.empty() and peak == 2
        tasks[0].cancel()
        await asyncio.gather(tasks[0], return_exceptions=True)
        await asyncio.wait_for(started.get(), 1)
        gate.set()
        await asyncio.gather(*tasks[1:])
        assert peak == 2 and limiter._value == 2


async def test_models_health_and_strict_inventory():
    async def handle(req):
        assert req.url.path == "/v1/models"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [{"id": "fixture", "object": "model", "created": 0, "owned_by": "library"}],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        assert await adapter.models() == ("fixture",)
        assert await adapter.health()


@pytest.mark.parametrize("bad", ["\ud800", "\udfff"])
async def test_models_rejects_unencodable_unicode_ids(bad):
    payload = {
        "object": "list",
        "data": [{"id": "model" + bad, "object": "model", "created": 0, "owned_by": "ollama"}],
    }
    calls = []

    async def handle(req):
        calls.append(req)
        return httpx.Response(200, content=json.dumps(payload).encode("utf-8"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        with pytest.raises(CGError) as caught:
            await adapter.models()
        assert caught.value.code == ErrorCode.UPSTREAM_ERROR
        assert len(calls) == 1 and adapter.limiter._value == 2


async def test_models_preserves_supplementary_unicode_id():
    model_id = "model😀"

    async def handle(req):
        return httpx.Response(
            200,
            content=json.dumps(
                {
                    "object": "list",
                    "data": [
                        {"id": model_id, "object": "model", "created": 0, "owned_by": "ollama"}
                    ],
                }
            ).encode("utf-8"),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        assert await HttpOllamaAdapter(Settings(), client=client).models() == (model_id,)


async def test_tools_and_multiturn_history_preserve_raw_strings_and_usage():
    raw = '{ "file": "test.txt" }'
    tool_call = {"id": "native", "type": "function", "function": {"name": "read", "arguments": raw}}
    history = [
        {"role": "system", "content": "Constraint"},
        {"role": "user", "content": "Read"},
        {"role": "assistant", "tool_calls": [tool_call]},
        {"role": "tool", "tool_call_id": "native", "name": "read", "content": "exact\ncontents"},
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read",
                "parameters": {"type": "object", "properties": {"file": {"type": "string"}}},
            },
        }
    ]

    async def handle(req):
        body = json.loads(req.content)
        assert body["messages"] == history and body["tools"] == tools
        assert body["parallel_tool_calls"] is False and body["tool_choice"] == "auto"
        return httpx.Response(
            200,
            json=completion(
                choices=[
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{**tool_call, "index": 0}],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                usage={
                    "prompt_tokens": 2,
                    "completion_tokens": 3,
                    "total_tokens": 5,
                    "prompt_tokens_details": {"cached_tokens": 1},
                },
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        result = await adapter.complete(
            request(messages=history, tools=tools, tool_choice="auto", parallel_tool_calls=False)
        )
        assert result.choices[0].message.tool_calls[0].function.arguments == raw
        assert result.choices[0].finish_reason == "tool_calls"
        assert result.usage.total_tokens == 5


@pytest.mark.parametrize(
    "raw", ['{"id":"one","id":"two"}', '{"count":NaN}', '"scalar"', "{invalid"]
)
async def test_nonstandard_json_sanitizes_and_does_not_retry(raw):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=raw))
    ) as client:
        with pytest.raises(CGError) as caught:
            await HttpOllamaAdapter(Settings(), client=client).complete(request())
        assert caught.value.code == ErrorCode.UPSTREAM_ERROR


async def test_health_reports_unavailable_without_leaking_transport_error():
    async def handle(req):
        raise httpx.ConnectError("private URL")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        assert not await HttpOllamaAdapter(Settings(), client=client).health()


def scalar_payload(field, value):
    payload = completion()
    message = payload["choices"][0]["message"]
    if field in {"id", "model"}:
        payload[field] = value
    elif field in {"content", "name"}:
        message[field] = value
    elif field == "text_part":
        message["content"] = [{"type": "text", "text": value}]
    else:
        message["tool_calls"] = [
            {
                "id": value if field == "tool_id" else "native",
                "type": "function",
                "function": {
                    "name": value if field == "tool_name" else "read",
                    "arguments": '{ "value" : "' + value + '" }' if field == "arguments" else "{}",
                },
            }
        ]
        payload["choices"][0]["finish_reason"] = "tool_calls"
    return payload


@pytest.mark.parametrize("bad", ["\ud800", "\udfff"])
@pytest.mark.parametrize(
    "field", ["id", "model", "content", "name", "text_part", "tool_id", "tool_name", "arguments"]
)
async def test_normalized_unicode_scalars_fail_at_provider_boundary(field, bad):
    raw = json.dumps(scalar_payload(field, bad)).encode("utf-8")
    calls = []

    async def handle(req):
        calls.append(req)
        return httpx.Response(200, content=raw)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = HttpOllamaAdapter(Settings(), client=client)
        with pytest.raises(CGError) as caught:
            await adapter.complete(request())
        assert caught.value.code == ErrorCode.UPSTREAM_ERROR and caught.value.status_code == 502
        assert len(calls) == 1 and adapter.limiter._value == 2 and not client.is_closed


@pytest.mark.parametrize("field", ["content", "tool_name", "tool_id", "arguments"])
async def test_normalized_unicode_scalars_public_upstream_error_not_storage_error(tmp_path, field):
    from tests.api.test_chat import chat, harness

    async def handle(_):
        return httpx.Response(200, content=json.dumps(scalar_payload(field, "\ud800")).encode())

    async with harness(tmp_path, handle) as (app, _, calls):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            result = await client.post("/v1/chat/completions", json=chat("ollama/fixture"))
        assert result.status_code == 502
        assert result.json()["error"]["code"] == "upstream_error"
        assert len(calls) == 1 and not app.state.admission.leases
        assert app.state.provider.limiter._value == 2


async def test_normalized_valid_unicode_pairs_raw_arguments_and_metadata_preserved():
    raw_arguments = r' { "value" : "\ud83d\ude00" } '
    payload = scalar_payload("tool_name", "readé😀")
    payload["id"] = "response😀"
    payload["choices"][0]["message"]["content"] = "é\u0085\u2028\u2029😀"
    call = payload["choices"][0]["message"]["tool_calls"][0]
    call["id"] = "native😀"
    call["function"]["arguments"] = raw_arguments
    payload["system_fingerprint"] = "known"
    payload["usage"] = {
        "prompt_tokens": 1,
        "completion_tokens": 2,
        "total_tokens": 3,
        "prompt_tokens_details": {"cached_tokens": 0},
    }
    raw = json.dumps(payload).encode()
    assert b"\\ud83d\\ude00" in raw
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=raw))
    ) as client:
        result = await HttpOllamaAdapter(Settings(), client=client).complete(request())
        assert (
            result.id == "response😀"
            and result.choices[0].message.content == "é\u0085\u2028\u2029😀"
        )
        call = result.choices[0].message.tool_calls[0]
        assert call.id == "native😀" and call.function.name == "readé😀"
        assert call.function.arguments == raw_arguments and result.usage.total_tokens == 3


async def test_normalized_valid_unicode_public_json_response(tmp_path):
    from tests.api.test_chat import chat, harness

    text = "é\u0085\u2028\u2029😀"
    raw_arguments = r' { "value" : "\ud83d\ude00" } '
    payload = scalar_payload("arguments", "valid")
    payload["choices"][0]["message"]["content"] = text
    payload["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = raw_arguments

    async def handle(_):
        return httpx.Response(200, content=json.dumps(payload).encode())

    async with harness(tmp_path, handle) as (app, client, calls):
        result = await client.post("/v1/chat/completions", json=chat("ollama/fixture"))
        assert result.status_code == 200 and result.json()["model"] == "ollama/fixture"
        message = result.json()["choices"][0]["message"]
        assert message["content"] == text
        assert message["tool_calls"][0]["function"]["arguments"] == raw_arguments
        assert len(calls) == 1 and not app.state.admission.leases
        assert app.state.provider.limiter._value == 2


async def live_probe(mode="all"):
    """Explicit opt-in local probe; no executor, downloads, token or saved trace.

    Run from the repository root with locked uv and import paths as documented
    in the worker handoff. all proves JSON/SSE/default-thinking tool continuation;
    sse checks the independently implemented stream boundary while JSON's shared
    factory gate is open. Exceptions intentionally make the command fail nonzero.
    """
    if mode not in {"all", "sse"}:
        raise ValueError("Live probe mode must be all or sse")
    adapter = HttpOllamaAdapter(
        Settings(ollama_base_url="http://127.0.0.1:11434/v1", llm_timeout_seconds=60)
    )
    base = request(
        model="gemma4:12b",
        messages=[{"role": "user", "content": "Reply READY."}],
        temperature=0.0,
        max_tokens=2048,
    )
    schemas = [
        {
            "type": "function",
            "function": {
                "name": "smoke_probe",
                "parameters": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    "required": ["value"],
                },
            },
        }
    ]
    tool_request = request(
        model="gemma4:12b",
        tools=schemas,
        tool_choice="required",
        messages=[{"role": "user", "content": "Call smoke_probe with value READY."}],
        temperature=0.0,
        max_tokens=2048,
    )
    report = {"mode": mode, "model": "gemma4:12b", "tools_executed": 0}
    try:
        assert "gemma4:12b" in await adapter.models()
        if mode == "all":
            ordinary = await adapter.complete(base)
            assert ordinary.choices[0].message.content == "READY"
            report["json_text_finish"] = ordinary.choices[0].finish_reason
            tool_response = await adapter.complete(tool_request)
            calls = tool_response.choices[0].message.tool_calls
            assert tool_response.choices[0].finish_reason == "tool_calls" and len(calls or []) == 1
            assert calls[0].function.name == "smoke_probe"
            assert json.loads(calls[0].function.arguments) == {"value": "READY"}
            report["json_tool_finish"] = tool_response.choices[0].finish_reason
            resumed_body = tool_request.model_dump(mode="json")
            resumed_body["tool_choice"] = "auto"
            resumed_body["messages"] += [
                tool_response.choices[0].message.model_dump(mode="json", exclude_none=True),
                {"role": "tool", "tool_call_id": calls[0].id, "content": "READY"},
            ]
            resumed = ProviderRequest.model_validate(resumed_body)
            final = await adapter.complete(resumed)
            assert final.choices[0].finish_reason in {"stop", "length"}
            assert not final.choices[0].message.tool_calls and final.choices[0].message.content
            report["json_tool_result_finish"] = final.choices[0].finish_reason
        for label, req in (("text", base), ("tool", tool_request)):
            parts = [part async for part in adapter.stream(req.model_copy(update={"stream": True}))]
            assert parts[-1] == b"data: [DONE]\n\n"
            chunks = [json.loads(part.decode()[6:]) for part in parts[:-1]]
            assert all(
                "reasoning" not in choice["delta"] for item in chunks for choice in item["choices"]
            )
            finishes = [
                choice["finish_reason"]
                for item in chunks
                for choice in item["choices"]
                if "finish_reason" in choice
            ]
            assert finishes == ["stop" if label == "text" else "tool_calls"]
            report[f"sse_{label}_chunks"] = len(chunks)
            report[f"sse_{label}_finish"] = finishes[0]
        try:
            await adapter.complete(base.model_copy(update={"model": "cg-smoke-does-not-exist"}))
        except CGError as error:
            assert error.code == ErrorCode.UNKNOWN_MODEL
            report["unknown_model_status"] = error.status_code
        else:
            raise AssertionError("Unknown model was substituted")
        print(json.dumps(report, sort_keys=True))
    finally:
        await adapter.close()
