import asyncio
import json
from contextlib import asynccontextmanager

import httpx
import pytest

from app.contracts.config import Settings
from app.main import create_app
from app.providers.ollama import HttpOllamaAdapter


def graph(id_="g", *, tools=False, inputs=None):
    return {
        "schema_version": 1,
        "id": id_,
        "name": "Fixture",
        "revision": 1,
        "base_model": "fixture",
        "inputs": inputs or [{"id": "chat", "required": True}],
        "nodes": [
            {"id": "i", "type": "input", "input_id": "chat"},
            {
                "id": "think",
                "type": "llm",
                "system_prompt": "think",
                "tools_enabled": tools,
                "generation": {},
            },
            {"id": "o", "type": "output"},
        ],
        "edges": [
            {
                "id": "it",
                "source": "i",
                "target": "think",
                "target_port": "question",
                "kind": "forward",
            },
            {
                "id": "to",
                "source": "think",
                "target": "o",
                "target_port": "answer",
                "kind": "forward",
            },
        ],
        "loops": [],
        "output_node_id": "o",
    }


def completion(content="final", *, calls=None, finish=None):
    return {
        "id": "upstream",
        "object": "chat.completion",
        "created": 1,
        "model": "fixture",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    **({"tool_calls": calls} if calls else {}),
                },
                "finish_reason": finish or ("tool_calls" if calls else "stop"),
            }
        ],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
    }


@asynccontextmanager
async def harness(tmp_path, handle=None, *, clock=None, models_payload=None, **settings_values):
    calls = []

    async def upstream(request):
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json=models_payload
                or {
                    "object": "list",
                    "data": [
                        {"id": "fixture", "object": "model", "created": 0, "owned_by": "ollama"}
                    ],
                },
            )
        body = json.loads(request.content)
        calls.append(body)
        return await handle(body) if handle else httpx.Response(200, json=completion())

    settings = Settings(data_dir=str(tmp_path), **settings_values)
    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as wire:
        provider = HttpOllamaAdapter(settings, client=wire)
        app = create_app(settings, provider=provider, clock=clock)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield app, client, calls


async def publish(client, value):
    assert (await client.post("/api/graphs", json=value)).status_code == 201
    assert (
        await client.post(f"/api/graphs/{value['id']}/publish", json={"expected_revision": 1})
    ).status_code == 200


def chat(model="cg/g", **values):
    return {"model": model, "messages": [{"role": "user", "content": "question"}], **values}


async def test_composed_graph_and_direct_json_and_draft_models(tmp_path):
    async with harness(tmp_path) as (_, client, calls):
        assert (await client.get("/health/ready")).json()["storage_ready"]
        await client.post("/api/graphs", json=graph("draft"))
        await publish(client, graph())
        ids = [item["id"] for item in (await client.get("/v1/models")).json()["data"]]
        assert ids == ["cg/g", "ollama/fixture"]
        response = await client.post("/v1/chat/completions", json=chat())
        assert response.status_code == 200
        assert response.headers["x-cg-run-id"]
        assert response.json()["model"] == "cg/g"
        direct = await client.post("/v1/chat/completions", json=chat("ollama/fixture"))
        assert direct.status_code == 200 and direct.json()["model"] == "ollama/fixture"
        assert "x-cg-run-id" not in direct.headers
        assert calls[-1]["model"] == "fixture"
        assert (await client.get("/api/runs")).json()["total"] == 1


@pytest.mark.parametrize("bad", ["\ud800", "\udfff"])
async def test_composed_models_rejects_unencodable_inventory_ids(tmp_path, bad):
    payload = {
        "object": "list",
        "data": [{"id": "model" + bad, "object": "model", "created": 0, "owned_by": "ollama"}],
    }
    async with harness(tmp_path, models_payload=payload) as (_, client, calls):
        result = await client.get("/v1/models")
        assert result.status_code == 502
        assert result.json()["error"]["code"] == "upstream_error"
        assert calls == []


async def test_composed_models_preserves_supplementary_inventory_id(tmp_path):
    model_id = "model😀"
    payload = {
        "object": "list",
        "data": [{"id": model_id, "object": "model", "created": 0, "owned_by": "ollama"}],
    }
    async with harness(tmp_path, models_payload=payload) as (_, client, calls):
        result = await client.get("/v1/models")
        assert result.status_code == 200
        assert result.json()["data"] == [
            {"id": "ollama/" + model_id, "object": "model", "created": 0, "owned_by": "ollama"}
        ]
        assert calls == []


async def test_missing_required_input_before_provider_and_independent_turns(tmp_path):
    async with harness(tmp_path) as (_, client, calls):
        await publish(
            client,
            graph(
                "extra",
                inputs=[{"id": "chat", "required": True}, {"id": "other", "required": True}],
            ),
        )
        failed = await client.post("/v1/chat/completions", json=chat("cg/extra"))
        assert failed.status_code == 400 and not calls
        await publish(client, graph())
        first, second = await asyncio.gather(
            *[client.post("/v1/chat/completions", json=chat()) for _ in range(2)]
        )
        assert first.headers["x-cg-run-id"] != second.headers["x-cg-run-id"]


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
        },
    }
]
CALL = {
    "id": "internal",
    "type": "function",
    "function": {"name": "read", "arguments": '{"path": "fixture"}'},
}


def continuation(initial, answer, content="read result", **overrides):
    return {
        **initial,
        "messages": [
            *initial["messages"],
            answer["choices"][0]["message"],
            {
                "role": "tool",
                "tool_call_id": answer["choices"][0]["message"]["tool_calls"][0]["id"],
                "content": content,
            },
        ],
        **overrides,
    }


async def test_graph_tools_replay_changed_content_and_compressed_history(tmp_path):
    async def handle(body):
        if not any(message["role"] == "tool" for message in body["messages"]):
            return httpx.Response(200, json=completion(None, calls=[CALL]))
        tool = next(m for m in body["messages"] if m["role"] == "tool")
        if tool["tool_call_id"].startswith("cg_"):
            return httpx.Response(200, json=completion("new turn final"))
        assert tool["tool_call_id"] == "internal" and tool["content"] == "read result"
        return httpx.Response(200, json=completion("owner final"))

    async with harness(tmp_path, handle) as (_, client, calls):
        await publish(client, graph(tools=True))
        initial = chat(tools=TOOLS, parallel_tool_calls=False)
        first = await client.post("/v1/chat/completions", json=initial)
        answer = first.json()
        id_ = answer["choices"][0]["message"]["tool_calls"][0]["id"]
        assert id_.startswith("cg_") and id_ != "internal"
        compressed = continuation(initial, answer)
        compressed["messages"] = compressed["messages"][1:]
        second = await client.post("/v1/chat/completions", json=compressed)
        assert (
            second.status_code == 200
            and second.json()["choices"][0]["message"]["content"] == "owner final"
        )
        count = len(calls)
        replay_a, replay_b = await asyncio.gather(
            *[client.post("/v1/chat/completions", json=compressed) for _ in range(2)]
        )
        assert replay_a.json() == second.json() == replay_b.json() and len(calls) == count
        changed = continuation(initial, answer, "changed")
        assert (await client.post("/v1/chat/completions", json=changed)).status_code == 409
        newest = {
            **initial,
            "messages": [
                *compressed["messages"],
                second.json()["choices"][0]["message"],
                {"role": "user", "content": "question"},
            ],
        }
        new = await client.post("/v1/chat/completions", json=newest)
        assert new.status_code == 200 and new.headers["x-cg-run-id"] != first.headers["x-cg-run-id"]


async def test_continuation_mixed_new_turn_unknown_id_and_cross_model(tmp_path):
    async def handle(_):
        return httpx.Response(200, json=completion(None, calls=[CALL]))

    async with harness(tmp_path, handle) as (_, client, calls):
        await publish(client, graph(tools=True))
        initial = chat(tools=TOOLS)
        answer = (await client.post("/v1/chat/completions", json=initial)).json()
        resumed = continuation(initial, answer)
        resumed["messages"].append({"role": "user", "content": "new turn"})
        assert (await client.post("/v1/chat/completions", json=resumed)).status_code == 409
        wrong = continuation(initial, answer, model="ollama/fixture")
        assert (await client.post("/v1/chat/completions", json=wrong)).status_code == 409
        unknown = continuation(initial, answer)
        unknown["messages"] = [{"role": "tool", "tool_call_id": "unknown", "content": "x"}]
        assert (await client.post("/v1/chat/completions", json=unknown)).status_code == 409
        assert len(calls) == 1


def sse(content="wire", *, malformed=False):
    base = {"id": "stream", "object": "chat.completion.chunk", "created": 1, "model": "fixture"}
    events = [
        {**base, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]},
        {**base, "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}]},
    ]
    if not malformed:
        events.append({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "length"}]})
    return b"".join(("data: " + json.dumps(event) + "\n\n").encode() for event in events) + (
        b"data: [DONE]\n\n" if not malformed else b""
    )


def stream_events(response):
    return [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ") and line != "data: [DONE]"
    ]


async def test_direct_sse_namespace_length_and_post_start_error(tmp_path):
    async def handle(body):
        assert body["stream"] and body["model"] == "fixture"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=sse(malformed=body.get("max_tokens") == 1),
        )

    async with harness(tmp_path, handle) as (app, client, _):
        good = await client.post("/v1/chat/completions", json=chat("ollama/fixture", stream=True))
        assert good.status_code == 200 and good.text.endswith("data: [DONE]\n\n")
        chunks = stream_events(good)
        assert all(c["model"] == "ollama/fixture" for c in chunks)
        assert chunks[-1]["choices"][0]["finish_reason"] == "length"
        failed = await client.post(
            "/v1/chat/completions", json=chat("ollama/fixture", stream=True, max_tokens=1)
        )
        assert failed.status_code == 200 and "event: error" in failed.text
        assert "[DONE]" not in failed.text and '"finish_reason":"stop"' not in failed.text
        assert not app.state.admission.leases


@pytest.mark.parametrize("stream", [False, True])
async def test_unknown_physical_model_never_substituted(tmp_path, stream):
    async def handle(body):
        assert body["model"] == "missing"
        return httpx.Response(404, text="secret raw provider failure")

    async with harness(tmp_path, handle) as (app, client, calls):
        failed = await client.post(
            "/v1/chat/completions", json=chat("ollama/missing", stream=stream)
        )
        assert failed.status_code == 404 and failed.json()["error"]["code"] == "unknown_model"
        assert "secret" not in failed.text and len(calls) == 1
        assert not app.state.admission.leases


async def test_graph_sse_tool_indices_raw_arguments_done_and_usage(tmp_path):
    async def handle(_):
        return httpx.Response(200, json=completion(None, calls=[CALL]))

    async with harness(tmp_path, handle) as (_, client, _):
        await publish(client, graph(tools=True))
        response = await client.post("/v1/chat/completions", json=chat(tools=TOOLS, stream=True))
        chunks = stream_events(response)
        call = chunks[1]["choices"][0]["delta"]["tool_calls"][0]
        assert call["index"] == 0 and call["id"].startswith("cg_")
        assert call["function"]["arguments"] == CALL["function"]["arguments"]
        assert chunks[-1]["choices"][0]["finish_reason"] == "tool_calls"
        assert response.text.endswith("data: [DONE]\n\n")
        assert '"content":"think"' not in response.text


async def test_graph_post_start_failure_has_error_not_success(tmp_path):
    async def handle(_):
        return httpx.Response(500, text="private failure")

    async with harness(tmp_path, handle) as (_, client, _):
        await publish(client, graph())
        response = await client.post("/v1/chat/completions", json=chat(stream=True))
        assert response.status_code == 200 and "event: error" in response.text
        assert "[DONE]" not in response.text and "private" not in response.text


async def test_direct_multiturn_and_native_tools_forwarded_without_graph_history(tmp_path):
    async with harness(tmp_path) as (_, client, calls):
        body = chat(
            "ollama/fixture",
            tools=TOOLS,
            messages=[
                {"role": "system", "content": "constraints"},
                {"role": "user", "content": "read"},
                {"role": "assistant", "tool_calls": [{**CALL, "id": "cg_not_a_graph_mapping"}]},
                {
                    "role": "tool",
                    "tool_call_id": "cg_not_a_graph_mapping",
                    "content": "raw\nresult",
                },
            ],
        )
        response = await client.post("/v1/chat/completions", json=body)
        assert response.status_code == 200
        for sent, received in zip(body["messages"], calls[0]["messages"], strict=True):
            assert all(received[key] == value for key, value in sent.items())
        assert (await client.get("/api/runs")).json()["total"] == 0


async def test_direct_active_timeout_before_stream_headers_is_504(tmp_path):
    async def handle(_):
        await asyncio.Event().wait()

    async with harness(tmp_path, handle, run_active_timeout_seconds=1, llm_timeout_seconds=5) as (
        app,
        client,
        _,
    ):
        response = await client.post(
            "/v1/chat/completions", json=chat("ollama/fixture", stream=True)
        )
        assert response.status_code == 504 and response.json()["error"]["code"] == "run_timeout"
        assert not app.state.admission.leases


async def test_forced_tool_multiple_nodes_rejected_before_admission(tmp_path):
    async with harness(tmp_path) as (app, client, calls):
        value = graph(tools=True)
        value["nodes"].insert(
            2,
            {
                "id": "second",
                "type": "llm",
                "system_prompt": "second",
                "tools_enabled": True,
                "generation": {},
            },
        )
        value["edges"][1]["target"] = "second"
        value["edges"].append(
            {
                "id": "final",
                "source": "second",
                "target": "o",
                "target_port": "answer",
                "kind": "forward",
            }
        )
        await publish(client, value)
        response = await client.post(
            "/v1/chat/completions",
            json=chat(tools=TOOLS, tool_choice={"type": "function", "function": {"name": "read"}}),
        )
        assert (
            response.status_code == 400
            and response.json()["error"]["code"] == "unsupported_tool_choice"
        )
        assert not calls and not app.state.admission.leases


@pytest.mark.parametrize("stream", [False, True])
async def test_direct_native_tool_round_json_and_fragmented_sse(tmp_path, stream):
    native = {**CALL, "id": "native-id"}

    async def handle(body):
        if any(m["role"] == "tool" for m in body["messages"]):
            assert body["messages"][-1]["content"] == "raw\nresult"
            if stream:
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"}, content=sse("direct final")
                )
            return httpx.Response(200, json=completion("direct final"))
        if not stream:
            return httpx.Response(200, json=completion(None, calls=[native]))
        base = {
            "id": "native-stream",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "fixture",
        }
        deltas = [
            {"role": "assistant"},
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "native-id",
                        "type": "function",
                        "function": {"name": "read", "arguments": '{"path": '},
                    }
                ]
            },
            {"tool_calls": [{"index": 0, "function": {"arguments": '"fixture"}'}}]},
            {},
        ]
        events = [
            {
                **base,
                "choices": [
                    {"index": 0, "delta": delta, "finish_reason": "tool_calls" if i == 3 else None}
                ],
            }
            for i, delta in enumerate(deltas)
        ]
        raw = b"".join(("data: " + json.dumps(e) + "\n\n").encode() for e in events)
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=raw + b"data: [DONE]\n\n"
        )

    async with harness(tmp_path, handle) as (app, client, calls):
        initial = chat("ollama/fixture", tools=TOOLS, stream=stream)
        first = await client.post("/v1/chat/completions", json=initial)
        assert first.status_code == 200 and "x-cg-run-id" not in first.headers
        if stream:
            chunks = stream_events(first)
            fragments = [
                f
                for c in chunks
                for choice in c["choices"]
                for f in choice["delta"].get("tool_calls", [])
            ]
            assert fragments[0]["id"] == "native-id" and all(f["index"] == 0 for f in fragments)
            assert (
                "".join(f["function"].get("arguments", "") for f in fragments)
                == CALL["function"]["arguments"]
            )
            assert chunks[-1]["choices"][0]["finish_reason"] == "tool_calls"
        else:
            assert first.json()["choices"][0]["message"]["tool_calls"] == [native]
        continued = {
            **initial,
            "messages": [
                *initial["messages"],
                {"role": "assistant", "tool_calls": [native]},
                {"role": "tool", "tool_call_id": "native-id", "content": "raw\nresult"},
            ],
        }
        final = await client.post("/v1/chat/completions", json=continued)
        assert final.status_code == 200 and "direct final" in final.text
        assert len(calls) == 2 and not app.state.admission.leases
        assert (await client.get("/api/runs")).json()["total"] == 0


async def test_graph_final_stream_usage_and_json_payload_equivalence(tmp_path):
    async with harness(tmp_path) as (_, client, _):
        await publish(client, graph())
        streamed = await client.post(
            "/v1/chat/completions", json=chat(stream=True, stream_options={"include_usage": True})
        )
        nonstreamed = await client.post("/v1/chat/completions", json=chat())
        chunks = stream_events(streamed)
        payload = "".join(
            choice["delta"].get("content", "") for c in chunks for choice in c["choices"]
        )
        assert payload == nonstreamed.json()["choices"][0]["message"]["content"]
        assert chunks[-1]["choices"] == [] and chunks[-1]["usage"] == nonstreamed.json()["usage"]
        assert streamed.text.endswith("data: [DONE]\n\n")
