"""Exercise the real graph router and file repository through HTTP."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, Header
from test_validator import loop_graph, make_graph

from app.api.graphs import create_graph_router
from app.contracts.config import MAX_REQUEST_BYTES, Settings
from app.contracts.errors import CGError, ErrorCode
from app.graphs.repository import FileGraphRepository
from app.graphs.validator import GraphValidator
from app.main import create_app
from app.providers.ollama import HttpOllamaAdapter


@pytest.fixture
def application(tmp_path):
    validator = GraphValidator()
    repository = FileGraphRepository(tmp_path, validator)

    async def authorize(authorization: str | None = Header(default=None)):
        if authorization != "Bearer test-only-token":
            raise CGError(ErrorCode.UNAUTHORIZED, "Authentication required.")

    app = FastAPI()
    app.include_router(create_graph_router(repository, validator, authorize))
    return app


def client(application):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="http://test",
        headers={"Authorization": "Bearer test-only-token"},
    )


@pytest.mark.asyncio
async def test_http_graph_lifecycle_and_conflict(application):
    async with client(application) as http:
        graph = make_graph()
        response = await http.post("/api/graphs", json=graph)
        assert response.status_code == 201
        assert response.json()["revision"] == 1
        assert (await http.post("/api/graphs", json=graph)).status_code == 409
        listing = (await http.get("/api/graphs")).json()
        assert listing == {
            "graphs": [{"id": "test", "name": "Test", "revision": 1, "published_revision": None}]
        }
        assert (await http.get("/api/graphs/test")).json()["base_model"] == "USER_INSTALLED_MODEL"
        assert (await http.post("/api/graphs/test/validate")).json()["valid"]
        publish = await http.post("/api/graphs/test/publish", json={"expected_revision": 1})
        assert publish.status_code == 200
        assert len(publish.json()["graph_hash"]) == 64
        graph["name"] = "Edited"
        saved = await http.put("/api/graphs/test", json={"graph": graph, "expected_revision": 1})
        assert saved.json()["revision"] == 2
        stale = await http.put("/api/graphs/test", json={"graph": graph, "expected_revision": 1})
        assert stale.status_code == 409
        assert (await http.get("/api/graphs/test")).json()["name"] == "Edited"


@pytest.mark.asyncio
async def test_invalid_draft_returns_local_validation_issues(application):
    graph = make_graph()
    graph["edges"][0]["source"] = "missing"
    async with client(application) as http:
        assert (await http.post("/api/graphs", json=graph)).status_code == 201
        report = (await http.post("/api/graphs/test/validate")).json()
        assert not report["valid"]
        assert any(issue["edge_id"] == "ia" for issue in report["errors"])
        assert (
            await http.post("/api/graphs/test/publish", json={"expected_revision": 1})
        ).status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/graphs", "get"),
        ("/api/graphs", "post"),
        ("/api/graphs/test", "get"),
        ("/api/graphs/test", "put"),
        ("/api/graphs/test/validate", "post"),
        ("/api/graphs/test/publish", "post"),
    ],
)
async def test_all_routes_use_injected_authorization(application, path, method):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://test"
    ) as http:
        response = await http.request(method, path)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_request_errors_are_sanitized_and_use_400_not_422(application):
    async with client(application) as http:
        for payload in [
            "invalid json",
            '{"id":"secret-token","schema_version":2}',
            '{"id":"one","id":"two"}',
        ]:
            response = await http.post("/api/graphs", content=payload)
            assert response.status_code == 400
            assert "secret-token" not in response.text
        assert (await http.get("/api/graphs/missing")).status_code == 404
        graph = make_graph()
        graph["id"] = "other"
        mismatch = await http.put("/api/graphs/test", json={"graph": graph, "expected_revision": 1})
        assert mismatch.status_code == 400
        too_big = await http.post("/api/graphs", content=b" " * (MAX_REQUEST_BYTES + 1))
        assert too_big.status_code == 413


@pytest.fixture
async def composed_application(tmp_path):
    upstream_requests = []

    async def upstream(request):
        upstream_requests.append(request)
        raise AssertionError("Graph management must not call inference")

    settings = Settings(data_dir=str(tmp_path), ollama_base_url="http://127.0.0.1:1/v1")
    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as wire:
        provider = HttpOllamaAdapter(settings, client=wire)
        app = create_app(settings, provider=provider)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                base_url="http://test",
            ) as http:
                yield app, http, upstream_requests


def graph_with_string(field, value):
    graph = loop_graph()
    if field == "prompt":
        graph["nodes"][1]["system_prompt"] = value
    elif field == "stop":
        graph["nodes"][1]["generation"]["stop"] = value
    elif field == "stop_array":
        graph["nodes"][1]["generation"]["stop"] = ["END", value]
    elif field == "seed":
        graph["edges"][-1]["initial_value"] = value
    elif field == "nested_seed":
        graph["edges"][-1]["initial_value"] = {"history": [None, {"data": value}]}
    elif field == "seed_key":
        graph["edges"][-1]["initial_value"] = {value: "present"}
    elif field == "continue_value":
        graph["loops"][0]["continue_value"] = value
    elif field == "exit_value":
        graph["loops"][0]["exit_value"] = value
    else:
        graph[field] = value
    return graph


@pytest.mark.parametrize("method", ["POST", "PUT"])
@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"], ids=["high", "low"])
@pytest.mark.parametrize(
    "field",
    [
        "prompt",
        "stop",
        "stop_array",
        "seed",
        "nested_seed",
        "seed_key",
        "name",
        "base_model",
        "continue_value",
        "exit_value",
    ],
)
async def test_composed_graph_rejects_unpaired_unicode_before_storage(
    composed_application, tmp_path, monkeypatch, caplog, method, surrogate, field
):
    app, http, upstream_requests = composed_application
    original = make_graph()
    assert (await http.post("/api/graphs", json=original)).status_code == 201
    stored = tmp_path / "graphs/test.json"
    before = stored.read_bytes()
    create = AsyncMock(wraps=app.state.graphs.create)
    save = AsyncMock(wraps=app.state.graphs.save)
    monkeypatch.setattr(app.state.graphs, "create", create)
    monkeypatch.setattr(app.state.graphs, "save", save)
    invalid = graph_with_string(field, "private-invalid" + surrogate)
    if method == "POST":
        invalid["id"] = "invalid"
        path, payload = "/api/graphs", invalid
    else:
        path, payload = "/api/graphs/test", {"graph": invalid, "expected_revision": 1}
    response = await http.request(method, path, content=json.dumps(payload))
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "message": "Invalid graph request body.",
            "type": "invalid_request_error",
            "code": "invalid_parameter",
        }
    }
    assert "private-invalid" not in response.text
    assert "private-invalid" not in caplog.text
    assert stored.read_bytes() == before
    assert not (tmp_path / "graphs/invalid.json").exists()
    assert (await http.get("/api/graphs/test")).json()["revision"] == 1
    assert (await http.post("/api/graphs/test/validate")).json()["valid"]
    create.assert_not_awaited()
    save.assert_not_awaited()
    assert not upstream_requests


@pytest.mark.parametrize(
    "field", ["prompt", "stop", "stop_array", "seed", "nested_seed", "seed_key"]
)
async def test_composed_graph_accepts_supplementary_unicode_round_trip(
    composed_application, tmp_path, field
):
    _, http, upstream_requests = composed_application
    # json.dumps writes the real supplementary character as an escaped surrogate
    # pair; the decoder must preserve it as a valid Unicode scalar value.
    graph = graph_with_string(field, "valid \U0001f680 \U0001d11e")
    wire = json.dumps(graph)
    assert "\\ud83d\\ude80" in wire and "\\ud834\\udd1e" in wire
    created = await http.post("/api/graphs", content=wire)
    assert created.status_code == 201
    assert (await http.post("/api/graphs/test/validate")).json()["valid"]
    assert (await http.get("/api/graphs/test")).json() == created.json()
    saved = await http.put(
        "/api/graphs/test", content=json.dumps({"graph": graph, "expected_revision": 1})
    )
    assert saved.status_code == 200 and saved.json()["revision"] == 2
    expected = dict(created.json(), revision=2)
    assert saved.json() == expected
    assert json.loads((tmp_path / "graphs/test.json").read_text(encoding="utf-8")) == expected
    published = await http.post("/api/graphs/test/publish", json={"expected_revision": 2})
    assert published.status_code == 200
    assert (await http.post("/api/graphs/test/validate")).json()["valid"]
    assert not upstream_requests
