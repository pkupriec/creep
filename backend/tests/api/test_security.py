import json

import httpx
import pytest
from fastapi import Request
from pydantic import SecretStr
from test_chat import chat, graph, harness, publish

from app.api.security import authorization
from app.contracts.config import MAX_REQUEST_BYTES, MAX_TOOL_RESULT_BYTES, Settings
from app.contracts.errors import CGError


async def test_bearer_covers_all_surfaces_and_sse_without_token_leaks(tmp_path, caplog):
    token = "synthetic-only-cg-token"
    async with harness(tmp_path, api_token=SecretStr(token)) as (app, client, calls):
        for method, path in [
            ("GET", "/api/graphs"),
            ("GET", "/v1/models"),
            ("POST", "/api/runs"),
            ("POST", "/v1/chat/completions"),
            ("GET", "/api/runs/unknown/events"),
            ("POST", "/api/runs/unknown/tool-results"),
        ]:
            response = await client.request(method, path, json=chat())
            assert response.status_code == 401 and token not in response.text
        assert (await client.get("/health/ready")).status_code == 200
        client.headers["Authorization"] = "Bearer " + token
        await publish(client, graph())
        response = await client.post("/v1/chat/completions", json=chat())
        run_id = response.headers["x-cg-run-id"]
        run = await app.state.repository.get_run(run_id, app.state.settings.caller_namespace())
        assert token not in run.model_dump_json() and not calls[0].get("api_token")
        assert token not in (await client.get(f"/api/runs/{run_id}")).text
        client.headers["Authorization"] = "Bearer wrong"
        assert (await client.get(f"/api/runs/{run_id}/events")).status_code == 401
        assert token not in caplog.text


async def test_utf8_bearer_byte_comparison_and_duplicate_authorization():
    settings = Settings(api_token=SecretStr("synthetic-ключ"))
    check = authorization(settings)
    scope = {"type": "http", "headers": [(b"authorization", "Bearer synthetic-ключ".encode())]}
    assert await check(Request(scope)) == settings.caller_namespace()
    scope["headers"].append(scope["headers"][0])
    with pytest.raises(CGError):
        await check(Request(scope))


@pytest.mark.parametrize(
    "raw",
    [
        '{"model":"ollama/fixture","model":"cg/g","messages":[]}',
        '{"model":"ollama/fixture","messages":[{"role":"user","content":"x"}],"temperature":NaN}',
        '{"model":"ollama/fixture","messages":[{"role":"user","content":"\\ud800"}]}',
        json.dumps(chat(seed=1)),
        json.dumps(chat(n=2)),
        json.dumps(chat(reasoning_effort="none")),
    ],
)
async def test_strict_http_profile_rejects_without_inference(tmp_path, raw):
    async with harness(tmp_path) as (_, client, calls):
        response = await client.post("/v1/chat/completions", content=raw)
        assert response.status_code == 400 and "error" in response.json()
        assert "detail" not in response.json() and not calls


async def test_chunked_body_and_tool_result_sizes_before_effects(tmp_path):
    async with harness(tmp_path) as (_, client, calls):

        async def chunks():
            yield b" " * MAX_REQUEST_BYTES
            yield b" "

        response = await client.post("/v1/chat/completions", content=chunks())
        assert response.status_code == 413 and not calls
        too_big = chat(
            "ollama/fixture",
            messages=[
                {
                    "role": "tool",
                    "tool_call_id": "native",
                    "content": "x" * (MAX_TOOL_RESULT_BYTES + 1),
                }
            ],
        )
        response = await client.post("/v1/chat/completions", json=too_big)
        assert response.status_code == 413 and not calls


async def test_ready_reports_external_unavailability_separately(tmp_path):
    async with harness(tmp_path) as (app, client, _):

        async def unavailable():
            return False

        app.state.provider.health = unavailable
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "storage_ready": True, "ollama_available": False}
        app.state.storage_ready = False
        assert (await client.get("/health/ready")).status_code == 503


async def test_rotated_namespace_cannot_view_prior_run_or_resume_known_ids(tmp_path):
    from test_chat import CALL, TOOLS, completion, continuation

    async def handle(_):
        return httpx.Response(200, json=completion(None, calls=[CALL]))

    async with harness(tmp_path, handle, api_token=SecretStr("old-synthetic")) as (_, client, _):
        client.headers["Authorization"] = "Bearer old-synthetic"
        await publish(client, graph(tools=True))
        initial = chat(tools=TOOLS)
        first = await client.post("/v1/chat/completions", json=initial)
        id_ = first.headers["x-cg-run-id"]
    async with harness(tmp_path, handle, api_token=SecretStr("new-synthetic")) as (
        _,
        client,
        calls,
    ):
        client.headers["Authorization"] = "Bearer new-synthetic"
        assert (await client.get("/api/runs")).json()["total"] == 0
        for route in [f"/api/runs/{id_}", f"/api/runs/{id_}/events"]:
            assert (await client.get(route)).status_code == 404
        assert (
            await client.post("/v1/chat/completions", json=continuation(initial, first.json()))
        ).status_code == 409
        assert not calls
