"""HTTP/SQLite acceptance with external Ollama HTTP simulated, never tools executed.

These deterministic checks complement real Hermes/Ollama/Windows smoke gates;
in-process application reconstruction is not a production process restart.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from starlette.requests import ClientDisconnect

from app.contracts.config import Settings
from app.main import create_app
from app.providers.ollama import HttpOllamaAdapter


def example(name):
    value = json.loads(
        (Path(__file__).resolve().parents[3] / "examples" / f"{name}.json").read_text(
            encoding="utf-8"
        )
    )
    value["base_model"] = "fixture"
    for node in value["nodes"]:
        if node["type"] == "llm":
            node["system_prompt"] = node["id"]
    return value


def answer(content="final", calls=None):
    return {
        "id": "wire",
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
                "finish_reason": "tool_calls" if calls else "stop",
            }
        ],
    }


@asynccontextmanager
async def session(path, handler, **settings_values):
    async def wire(request):
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"object": "list", "data": []})
        return await handler(json.loads(request.content))

    settings = Settings(data_dir=str(path), **settings_values)
    async with httpx.AsyncClient(transport=httpx.MockTransport(wire)) as external:
        app = create_app(settings, provider=HttpOllamaAdapter(settings, client=external))
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield app, client


async def publish(client, value):
    assert (await client.post("/api/graphs", json=value)).status_code == 201
    assert (
        await client.post(
            f"/api/graphs/{value['id']}/publish", json={"expected_revision": value["revision"]}
        )
    ).status_code == 200


def request(model="cg/synthesis", **overrides):
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "client constraint"},
            {"role": "user", "content": "question"},
        ],
        **overrides,
    }


def node(body):
    return next(
        (
            m["content"]
            for m in body["messages"]
            if m["role"] == "system" and m["content"] != "client constraint"
        ),
        "direct",
    )


async def test_a03_http_diamond_barrier_final_policy_and_snapshot_conflict(tmp_path):
    both, release = asyncio.Event(), asyncio.Event()
    started, bodies = set(), []

    async def handler(body):
        bodies.append(body)
        current = node(body)
        assert body["messages"][0]["content"] == "client constraint"
        if current in {"a", "b"}:
            started.add(current)
            if len(started) == 2:
                both.set()
            await release.wait()
            assert body["temperature"] == 0.2
            return httpx.Response(200, json=answer(current))
        assert started == {"a", "b"} and body["temperature"] == 0.8
        ports = json.loads(body["messages"][-1]["content"])["inputs"]
        assert [(p["port"], p["value"]) for p in ports] == [
            ("alternatives", "b"),
            ("correctness", "a"),
        ]
        return httpx.Response(200, json=answer("synthesis final"))

    async with session(tmp_path, handler) as (_, client):
        value = example("synthesis")
        await publish(client, value)
        pending = asyncio.create_task(
            client.post("/v1/chat/completions", json=request(temperature=0.8))
        )
        try:
            await asyncio.wait_for(both.wait(), 2)
            changed = {**value, "name": "edited"}
            assert (
                await client.put(
                    "/api/graphs/synthesis", json={"graph": changed, "expected_revision": 1}
                )
            ).status_code == 200
            assert (
                await client.put(
                    "/api/graphs/synthesis", json={"graph": value, "expected_revision": 1}
                )
            ).status_code == 409
        finally:
            release.set()
        response = await asyncio.wait_for(pending, 3)
        assert (
            response.status_code == 200
            and response.json()["choices"][0]["message"]["content"] == "synthesis final"
        )
        detail = (await client.get("/api/runs/" + response.headers["x-cg-run-id"])).json()
        assert detail["snapshot"]["name"] == value["name"] and len(bodies) == 3


@pytest.mark.parametrize("stream", [False, True])
async def test_a05_http_seed_two_continues_final_only(tmp_path, stream):
    iterations, previous = 0, []

    async def handler(body):
        nonlocal iterations
        ports = json.loads(body["messages"][-1]["content"])["inputs"]
        if node(body) == "draft":
            previous.append(next(p["value"] for p in ports if p["port"] == "previous_critique"))
            assert next(p["value"] for p in ports if p["port"] == "question") == "question"
            return httpx.Response(200, json=answer("internal draft"))
        iterations += 1
        assert body["response_format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json=answer(
                json.dumps(
                    {
                        "payload": f"critique-{iterations}"
                        if iterations < 3
                        else "final loop payload",
                        "control": {"decision": "continue" if iterations < 3 else "stop"},
                    }
                )
            ),
        )

    async with session(tmp_path, handler) as (_, client):
        await publish(client, example("feedback"))
        response = await client.post(
            "/v1/chat/completions", json=request("cg/feedback", stream=stream)
        )
        assert response.status_code == 200 and iterations == 3
        assert previous == [
            "No previous critique; write the initial draft.",
            "critique-1",
            "critique-2",
        ]
        assert "final loop payload" in response.text and "internal draft" not in response.text
        assert "control" not in response.text and "critique-1" not in response.text
        id_ = response.headers["x-cg-run-id"]
        detail = (await client.get(f"/api/runs/{id_}")).json()
        assert sorted(a["iteration"] for a in detail["activations"] if a["node_id"] == "draft") == [
            0,
            1,
            2,
        ]


async def test_a06_endless_control_returns_budget_error_not_final(tmp_path):
    async def handler(body):
        text = (
            "draft"
            if node(body) == "draft"
            else '{"payload":"again","control":{"decision":"continue"}}'
        )
        return httpx.Response(200, json=answer(text))

    async with session(tmp_path, handler, max_node_executions=7) as (_, client):
        await publish(client, example("feedback"))
        response = await client.post("/v1/chat/completions", json=request("cg/feedback"))
        assert response.status_code == 400 and response.json()["error"]["code"] == "budget_exceeded"
        history = (await client.get("/api/runs")).json()["runs"]
        assert history[0]["status"] == "failed"


TOOL = {"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}
COLLIDING = {
    "id": "same-internal",
    "type": "function",
    "function": {"name": "read", "arguments": "{}"},
}


async def test_a08_two_owner_collisions_private_results_and_replay_first_next(tmp_path):
    requests = []

    async def handler(body):
        current = node(body)
        requests.append((current, body))
        tools = [m for m in body["messages"] if m["role"] == "tool"]
        if current in {"a", "b"} and not tools:
            return httpx.Response(200, json=answer(None, [COLLIDING]))
        if current in {"a", "b"}:
            assert len(tools) == 1 and tools[0]["tool_call_id"] == "same-internal"
            assert tools[0]["content"] == "owner-" + current
            return httpx.Response(200, json=answer("payload-" + current))
        assert not tools
        return httpx.Response(200, json=answer("combined"))

    async with session(tmp_path, handler) as (app, client):
        await publish(client, example("synthesis"))
        initial = request(tools=[TOOL], parallel_tool_calls=False)
        first = await client.post("/v1/chat/completions", json=initial)
        seen, envelopes, resumes = [], [first.json()], []
        response = first
        for _ in range(2):
            call = response.json()["choices"][0]["message"]["tool_calls"][0]
            assert len(response.json()["choices"][0]["message"]["tool_calls"]) == 1
            assert call["id"] not in seen
            seen.append(call["id"])
            mapping = (await app.state.repository.lookup_tools((call["id"],)))[0]
            continued = {
                **initial,
                "messages": [
                    response.json()["choices"][0]["message"],
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": "owner-" + mapping.node_id,
                    },
                ],
            }
            resumes.append(continued)
            response = await client.post("/v1/chat/completions", json=continued)
            assert response.status_code == 200
            envelopes.append(response.json())
        assert response.json()["choices"][0]["message"]["content"] == "combined"
        count = len(requests)
        replay = await client.post("/v1/chat/completions", json=resumes[0])
        assert replay.json() == envelopes[1] and len(requests) == count


async def test_a10_http_reconstruct_waiting_original_ids_and_interrupted_active(tmp_path):
    started, block = asyncio.Event(), asyncio.Event()
    calls = []

    async def handler(body):
        calls.append(body)
        if node(body) == "slow":
            started.set()
            await block.wait()
        tools = [m for m in body["messages"] if m["role"] == "tool"]
        return httpx.Response(
            200, json=answer("restored" if tools else None, None if tools else [COLLIDING])
        )

    async with session(tmp_path, handler) as (_, client):
        value = example("synthesis")
        value["nodes"] = [n for n in value["nodes"] if n["id"] in {"input", "a", "output"}]
        value["edges"] = [
            value["edges"][0],
            {
                "id": "exit",
                "source": "a",
                "target": "output",
                "target_port": "answer",
                "kind": "forward",
            },
        ]
        await publish(client, value)
        initial = request(tools=[TOOL])
        first = await client.post("/v1/chat/completions", json=initial)
        waiting_id = first.headers["x-cg-run-id"]
        slow = {
            **value,
            "id": "slow",
            "nodes": [
                dict(n, system_prompt="slow") if n["type"] == "llm" else n for n in value["nodes"]
            ],
        }
        await client.post("/api/graphs", json=slow)
        active = await client.post(
            "/api/runs", json={"graph_id": "slow", "revision": 1, "inputs": {"chat": "x"}}
        )
        active_id = active.json()["run_id"]
        await asyncio.wait_for(started.wait(), 2)
    count = len(calls)
    async with session(tmp_path, handler) as (_, client):
        assert (await client.get(f"/api/runs/{active_id}")).json()["run"]["status"] == "interrupted"
        assert len(calls) == count
        assert (await client.get(f"/api/runs/{waiting_id}")).json()["run"][
            "status"
        ] == "waiting_tools"
        call = first.json()["choices"][0]["message"]["tool_calls"][0]
        resumed = {
            **initial,
            "messages": [
                first.json()["choices"][0]["message"],
                {"role": "tool", "tool_call_id": call["id"], "content": "read result"},
            ],
        }
        final = await client.post("/v1/chat/completions", json=resumed)
        assert final.status_code == 200 and final.headers["x-cg-run-id"] == waiting_id
        assert final.json()["choices"][0]["message"]["content"] == "restored"
        assert len(calls) == count + 1


async def test_a14_a16_shared_graph_direct_semaphore_and_queue_capacity(tmp_path):
    release, at_capacity = asyncio.Event(), asyncio.Event()
    concurrent = peak = count = 0

    async def handler(_):
        nonlocal concurrent, peak, count
        count += 1
        concurrent += 1
        peak = max(peak, concurrent)
        if concurrent == 2:
            at_capacity.set()
        try:
            await release.wait()
            return httpx.Response(200, json=answer("bounded"))
        finally:
            concurrent -= 1

    async with session(tmp_path, handler, max_active_runs=2, max_queued_runs=1) as (app, client):
        value = example("synthesis")
        await publish(client, value)
        graph_request = asyncio.create_task(client.post("/v1/chat/completions", json=request()))
        await asyncio.wait_for(at_capacity.wait(), 2)
        queued = asyncio.Event()
        original_acquire = app.state.admission.acquire

        async def acquire(job_id):
            lease = await original_acquire(job_id)
            if app.state.admission.queued:
                queued.set()
            return lease

        app.state.admission.acquire = acquire
        direct_request = asyncio.create_task(
            client.post("/v1/chat/completions", json=request("ollama/fixture"))
        )
        queued_request = asyncio.create_task(
            client.post("/v1/chat/completions", json=request("ollama/fixture"))
        )
        try:
            await asyncio.wait_for(queued.wait(), 2)
            rejected = await client.post(
                "/api/runs", json={"graph_id": "synthesis", "revision": 1, "inputs": {"chat": "x"}}
            )
            assert rejected.status_code == 429 and peak == 2
        finally:
            release.set()
        responses = await asyncio.wait_for(
            asyncio.gather(graph_request, direct_request, queued_request), 3
        )
        assert all(r.status_code == 200 for r in responses)
        assert peak == 2 and count == 5 and not app.state.admission.leases


async def asgi_post(app, body, send, disconnected):
    delivered = False

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": json.dumps(body).encode(), "more_body": False}
        await disconnected.wait()
        return {"type": "http.disconnect"}

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "server": ("test", 80),
        "client": ("test", 1),
    }
    await app(scope, receive, send)


async def test_initial_disconnect_cancels_unexposed_graph_but_streamed_tools_survive(tmp_path):
    started, release = asyncio.Event(), asyncio.Event()
    mode = "slow"

    async def handler(_):
        if mode == "slow":
            started.set()
            await release.wait()
        return httpx.Response(200, json=answer(None, [COLLIDING]))

    async with session(tmp_path, handler) as (app, client):
        await publish(client, example("synthesis"))
        disconnected = asyncio.Event()
        sent = []

        async def send(message):
            sent.append(message)

        task = asyncio.create_task(asgi_post(app, request(), send, disconnected))
        await asyncio.wait_for(started.wait(), 2)
        disconnected.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 2)
        assert (await client.get("/api/runs")).json()["runs"][0]["status"] == "cancelled"
        mode = "tools"

        async def broken_send(message):
            if message["type"] == "http.response.body":
                raise OSError("client closed")

        with pytest.raises(ClientDisconnect):
            await asgi_post(app, request(tools=[TOOL], stream=True), broken_send, asyncio.Event())
        history = (await client.get("/api/runs")).json()["runs"]
        exposed = next(r for r in history if r["status"] == "waiting_tools")
        detail = (await client.get("/api/runs/" + exposed["run_id"])).json()
        assert detail["pending_tools"] and len(app.state.admission.active) == 1


async def test_direct_asgi_send_failure_releases_inference_and_admission(tmp_path):
    base = {"id": "stream", "object": "chat.completion.chunk", "created": 1, "model": "fixture"}

    async def handler(_):
        data = (
            "data: "
            + json.dumps(
                {
                    **base,
                    "choices": [
                        {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                    ],
                }
            )
            + "\n\n"
        )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=data.encode()
        )

    async with session(tmp_path, handler) as (app, _):

        async def send(message):
            if message["type"] == "http.response.body":
                raise OSError("closed")

        with pytest.raises(ClientDisconnect):
            await asgi_post(app, request("ollama/fixture", stream=True), send, asyncio.Event())
        assert not app.state.admission.leases and app.state.provider.limiter._value == 2


async def test_continuation_disconnect_keeps_owner_and_exact_replay_running(tmp_path):
    resumed, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def handler(body):
        nonlocal calls
        calls += 1
        if any(m["role"] == "tool" for m in body["messages"]):
            resumed.set()
            await release.wait()
            return httpx.Response(200, json=answer("continuation survives"))
        return httpx.Response(200, json=answer(None, [COLLIDING]))

    async with session(tmp_path, handler) as (app, client):
        value = example("synthesis")
        value["nodes"] = [n for n in value["nodes"] if n["id"] in {"input", "a", "output"}]
        value["edges"] = [
            value["edges"][0],
            {
                "id": "exit",
                "source": "a",
                "target": "output",
                "target_port": "answer",
                "kind": "forward",
            },
        ]
        await publish(client, value)
        initial = request(tools=[TOOL])
        first = await client.post("/v1/chat/completions", json=initial)
        call = first.json()["choices"][0]["message"]["tool_calls"][0]
        continued = {
            **initial,
            "messages": [
                first.json()["choices"][0]["message"],
                {"role": "tool", "tool_call_id": call["id"], "content": "result"},
            ],
        }
        disconnected = asyncio.Event()

        async def send(_):
            pass

        waiter = asyncio.create_task(asgi_post(app, continued, send, disconnected))
        try:
            await asyncio.wait_for(resumed.wait(), 2)
            disconnected.set()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(waiter, 2)
            run_id = first.headers["x-cg-run-id"]
            assert (await client.get(f"/api/runs/{run_id}")).json()["run"]["status"] == "running"
        finally:
            release.set()
        replay = await client.post("/v1/chat/completions", json=continued)
        assert (
            replay.status_code == 200
            and replay.json()["choices"][0]["message"]["content"] == "continuation survives"
        )
        assert calls == 2 and not app.state.admission.leases
