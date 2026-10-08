import asyncio
import json

import pytest

from app.contracts.api import ChatCompletionResponse
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import Graph
from app.contracts.interfaces import (
    GraphSnapshot,
    RunContext,
    RunPolicy,
    RunSubmission,
    canonical_json,
)
from app.graphs.validator import GraphValidator
from app.runtime.admission import BoundedAdmissionController
from app.runtime.clock import SystemClock
from app.runtime.engine import AsyncGraphRuntime
from app.storage.events import DurableEventBus
from app.storage.repository import SQLiteRunRepository


def graph(nodes=None, edges=None, loops=None, inputs=None):
    return Graph.model_validate_json(
        json.dumps(
            {
                "schema_version": 1,
                "id": "g",
                "name": "Graph",
                "revision": 1,
                "base_model": "test",
                "inputs": inputs or [{"id": "chat", "required": True}],
                "nodes": nodes or [input_node("i"), llm("a"), llm("b"), llm("s"), output_node()],
                "edges": edges
                or [
                    edge("i", "a", "question"),
                    edge("i", "b", "question"),
                    edge("a", "s", "zeta"),
                    edge("b", "s", "alpha"),
                    edge("s", "o", "answer"),
                ],
                "loops": loops or [],
                "output_node_id": "o",
            }
        )
    )


def input_node(id_, input_id="chat"):
    return {"id": id_, "type": "input", "input_id": input_id}


def output_node():
    return {"id": "o", "type": "output"}


def llm(id_, tools=False):
    return {
        "id": id_,
        "type": "llm",
        "system_prompt": id_,
        "tools_enabled": tools,
        "generation": {},
    }


def edge(source, target, port):
    return {
        "id": source + "_" + target + "_" + port,
        "source": source,
        "target": target,
        "target_port": port,
        "kind": "forward",
    }


def submission(value, settings=None, inputs=None, tools=None, messages=None, client=None):
    settings = settings or Settings()
    validator = GraphValidator()
    snapshot = GraphSnapshot.from_graph(value)
    return RunSubmission(
        plan=validator.compile(snapshot),
        context=RunContext(
            namespace="anonymous",
            messages_json=canonical_json(
                messages
                or [
                    {"role": "system", "content": "client constraints"},
                    {"role": "user", "content": "question"},
                ]
            ),
            tools_json=canonical_json(tools or []),
        ),
        inputs_json=validator.prepare_inputs(
            value, canonical_json({"chat": "question"} if inputs is None else inputs)
        ),
        policy=RunPolicy(
            client_request_json=canonical_json(client or {"model": "cg/g"}),
            max_node_executions=settings.max_node_executions,
            max_tool_rounds=settings.max_tool_rounds,
            active_timeout_seconds=settings.run_active_timeout_seconds,
            tool_wait_timeout_seconds=settings.tool_wait_timeout_seconds,
        ),
    )


def response(content, tool_calls=None):
    return ChatCompletionResponse.model_validate(
        {
            "id": "upstream",
            "created": 1,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        **({"tool_calls": tool_calls} if tool_calls else {}),
                    },
                    "finish_reason": "tool_calls" if tool_calls else "stop",
                }
            ],
        }
    )


class Provider:
    def __init__(self, handler):
        self.handler = handler
        self.requests = []

    async def complete(self, request):
        self.requests.append(request)
        return await self.handler(request)


class NoTools:
    def map_calls(self, activation, response):
        raise AssertionError("Unexpected tools")

    async def prepare_batch(self, run_id, namespace):
        raise AssertionError("Unexpected batch")


async def create_runtime(tmp_path, provider, settings=None, bridge=None, clock=None):
    settings = settings or Settings()
    repository = SQLiteRunRepository(tmp_path / "runs.sqlite")
    await repository.initialize()
    runtime = AsyncGraphRuntime(
        settings,
        repository,
        GraphValidator(),
        provider,
        bridge or NoTools(),
        DurableEventBus(repository),
        BoundedAdmissionController(settings.max_active_runs, settings.max_queued_runs),
        clock or SystemClock(),
    )
    return runtime, repository


def node_request(request):
    return next(
        message.content
        for message in request.messages
        if message.role == "system" and message.content != "client constraints"
    )


@pytest.mark.asyncio
async def test_diamond_concurrent_start_all_input_barrier_and_stable_order(tmp_path):
    started = set()
    both = asyncio.Event()

    async def handler(request):
        node = node_request(request)
        assert request.messages[0].content == "client constraints"
        if node in {"a", "b"}:
            started.add(node)
            if len(started) == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 2)
            return response(node + " result")
        assert node == "s" and started == {"a", "b"}
        ports = json.loads(request.messages[-1].content)["inputs"]
        assert [(port["port"], port["value"]) for port in ports] == [
            ("alpha", "b result"),
            ("zeta", "a result"),
        ]
        return response("synthesis")

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(submission(graph()))
        answer = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert answer.completion().choices[0].message.content == "synthesis"
        saved = await repository.get_run(run.run_id, "anonymous")
        assert saved.status == "completed" and saved.node_executions == 3
        assert len(provider.requests) == 3
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_optional_null_and_passthrough_without_inference(tmp_path):
    async def handler(request):
        raise AssertionError("Passthrough must not infer")

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    value = graph(
        nodes=[input_node("i", "optional"), output_node()],
        edges=[edge("i", "o", "answer")],
        inputs=[{"id": "optional", "required": False}],
    )
    try:
        run = await runtime.submit(submission(value, inputs={}))
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 2)
        assert result.completion().choices[0].message.content == "null"
        assert (await repository.get_run(run.run_id, "anonymous")).node_executions == 0
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_failure_cancels_siblings_and_never_synthesizes(tmp_path):
    cancelled = asyncio.Event()

    async def handler(request):
        node = node_request(request)
        if node == "a":
            await asyncio.sleep(0.03)
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Required node failed")
        if node == "b":
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        raise AssertionError("Synthesis cannot start")

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(submission(graph()))
        with pytest.raises(CGError):
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 2)
        await asyncio.wait_for(cancelled.wait(), 1)
        assert (await repository.get_run(run.run_id, "anonymous")).status == "failed"
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_final_length_and_client_settings_preserved_in_durable_frontier(tmp_path):
    async def handler(request):
        assert request.temperature == 0.7 and request.max_tokens == 5
        result = response("truncated")
        result.choices[0].finish_reason = "length"
        return result

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    value = graph(
        nodes=[input_node("i"), llm("a"), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        run = await runtime.submit(
            submission(value, client={"model": "cg/g", "temperature": 0.7, "max_tokens": 5})
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].finish_reason == "length"
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert (
            next(item for item in checkpoint.activations if item.key.node_id == "a").finish_reason
            == "length"
        )
        assert result == checkpoint.responses[-1]
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("format_type", ["json_object", "json_schema"])
@pytest.mark.parametrize("finish", ["stop", "length"])
async def test_ordinary_final_formatted_content_is_not_encoded_twice(tmp_path, format_type, finish):
    content = '{"answer":"quoted \\"value\\"","reference":{"$ref":"#/literal"}}'
    requested = {"type": format_type}
    if format_type == "json_schema":
        requested["json_schema"] = {"name": "answer", "schema": {"type": "object"}}

    async def handler(request):
        assert request.response_format.type == format_type
        result = response(content)
        result.choices[0].finish_reason = finish
        return result

    value = graph(
        nodes=[input_node("i"), llm("a"), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(value, client={"model": "cg/g", "response_format": requested})
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == content
        assert result.completion().choices[0].finish_reason == finish
        assert isinstance(json.loads(content), dict)
        assert (await repository.load_checkpoint(run.run_id, "anonymous")).responses[-1] == result
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    ["hello", 'quoted "value"\nnext', "123", "null", '{"value":123}', None, 5, {"value": 123}],
)
async def test_no_llm_final_json_format_preserves_native_value_and_recovery(tmp_path, payload):
    async def handler(request):
        raise AssertionError("Input-output graph must not invoke inference")

    provider = Provider(handler)
    value = graph(nodes=[input_node("i"), output_node()], edges=[edge("i", "o", "answer")])
    client = {
        "model": "cg/g",
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": {"const": payload}},
        },
    }
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(submission(value, inputs={"chat": payload}, client=client))
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        actual = json.loads(final.completion().choices[0].message.content)
        assert actual == payload and type(actual) is type(payload)
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "completed"
        assert checkpoint.run.output_json == canonical_json(payload)
        assert checkpoint.responses[-1] == final and not provider.requests
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert (await runtime.await_response(run.run_id, "anonymous")) == final
        assert not provider.requests
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "requested,payload",
    [
        ({"type": "json_object"}, {"value": 'quoted "value"'}),
        ({"type": "text"}, '123 "quoted"'),
        (None, "null"),
    ],
)
async def test_no_llm_text_and_object_formats_keep_ordinary_behavior(tmp_path, requested, payload):
    async def handler(request):
        raise AssertionError("Input-output graph must not invoke inference")

    provider = Provider(handler)
    value = graph(nodes=[input_node("i"), output_node()], edges=[edge("i", "o", "answer")])
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(
                value,
                inputs={"chat": payload},
                client={"model": "cg/g", "response_format": requested},
            )
        )
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        expected = canonical_json(payload) if isinstance(payload, dict) else payload
        assert final.completion().choices[0].message.content == expected
        assert not provider.requests
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["hello", 3, None, []])
async def test_no_llm_json_object_rejects_non_object_without_coercion(tmp_path, payload):
    async def handler(request):
        raise AssertionError("Input-output graph must not invoke inference")

    provider = Provider(handler)
    value = graph(nodes=[input_node("i"), output_node()], edges=[edge("i", "o", "answer")])
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(
                value,
                inputs={"chat": payload},
                client={"model": "cg/g", "response_format": {"type": "json_object"}},
            )
        )
        with pytest.raises(CGError) as failure:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert failure.value.code == ErrorCode.INVALID_PARAMETER
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "failed"
        assert not checkpoint.responses and checkpoint.run.output_json is None
        assert not provider.requests
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        with pytest.raises(CGError) as recovered_failure:
            await runtime.await_response(run.run_id, "anonymous")
        assert recovered_failure.value.code == ErrorCode.INVALID_PARAMETER
        assert not provider.requests
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_missing_required_input_precedes_admission_and_identical_runs_stay_separate(tmp_path):
    async def handler(request):
        return response("answer")

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        accepted = submission(graph())
        with pytest.raises(CGError) as missing:
            await runtime.submit(accepted.model_copy(update={"inputs_json": "{}"}))
        assert missing.value.status_code == 400 and not provider.requests
        first, second = await asyncio.gather(runtime.submit(accepted), runtime.submit(accepted))
        assert first.run_id != second.run_id and first.snapshot == second.snapshot
        results = await asyncio.gather(
            runtime.await_response(first.run_id, "anonymous"),
            runtime.await_response(second.run_id, "anonymous"),
        )
        assert results[0].completion().id != results[1].completion().id
        assert len(provider.requests) == 6
        with pytest.raises(CGError):
            await repository.get_run(first.run_id, "different-caller")
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_snapshot_and_original_context_are_immutable_after_submit(tmp_path):
    gate = asyncio.Event()

    async def handler(request):
        await gate.wait()
        assert node_request(request) == "original"
        assert request.messages[0].content == "client constraints"
        return response("immutable")

    value = graph(
        nodes=[input_node("i"), llm("original"), output_node()],
        edges=[edge("i", "original", "question"), edge("original", "o", "answer")],
    )
    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        submitted = submission(value)
        run = await runtime.submit(submitted)
        value.nodes[1].system_prompt = "edited"
        value.revision = 2
        gate.set()
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        saved = await repository.get_run(run.run_id, "anonymous")
        assert saved.snapshot.graph_hash == submitted.plan.snapshot.graph_hash
        assert (
            saved.snapshot.revision == 1
            and saved.snapshot.graph().nodes[1].system_prompt == "original"
        )
        assert result.completion().choices[0].message.content == "immutable"
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_reducer_rebases_cas_conflict_without_repeating_provider(tmp_path, monkeypatch):
    async def handler(request):
        return response("answer")

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    original = repository.save_checkpoint
    injected = False

    async def race(checkpoint, expected_version):
        nonlocal injected
        if not injected and any(
            item.key.node_id == "a" and item.status == "completed"
            for item in checkpoint.activations
        ):
            injected = True
            authoritative = await repository.load_checkpoint(checkpoint.run.run_id, "anonymous")
            await original(
                authoritative.model_copy(
                    update={
                        "run": authoritative.run.model_copy(
                            update={
                                "active_elapsed_seconds": authoritative.run.active_elapsed_seconds
                                + 1
                            }
                        )
                    }
                ),
                authoritative.run.state_version,
            )
        return await original(checkpoint, expected_version)

    monkeypatch.setattr(repository, "save_checkpoint", race)
    value = graph(
        nodes=[input_node("i"), llm("a"), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        run = await runtime.submit(submission(value))
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert injected and len(provider.requests) == 1
        saved = await repository.get_run(run.run_id, "anonymous")
        assert saved.active_elapsed_seconds >= 1
        assert result.completion().choices[0].message.content == "answer"
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("native", [True, False])
@pytest.mark.parametrize("good", [True, False])
@pytest.mark.parametrize("constraint", ["const", "required", "local_ref"])
async def test_final_schema_constraints_are_enforced_before_success(
    tmp_path, native, good, constraint
):
    schemas = {
        "const": {"const": {"expected": 1}},
        "required": {"type": "object", "required": ["value"]},
        "local_ref": {
            "$defs": {"Text": {"type": "string"}},
            "type": "object",
            "properties": {"value": {"$ref": "#/$defs/Text"}},
            "required": ["value"],
        },
    }
    values = {
        "const": ({"expected": 1}, {"expected": 2}),
        "required": ({"value": "ok"}, {}),
        "local_ref": ({"value": "ok"}, {"value": 2}),
    }
    payload = values[constraint][0 if good else 1]
    raw_content = json.dumps(payload, indent=2)

    async def handler(request):
        return response(raw_content)

    provider = Provider(handler)
    nodes = (
        [input_node("i"), output_node()] if native else [input_node("i"), llm("a"), output_node()]
    )
    edges = (
        [edge("i", "o", "answer")]
        if native
        else [edge("i", "a", "question"), edge("a", "o", "answer")]
    )
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(
                graph(nodes=nodes, edges=edges),
                inputs={"chat": payload},
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "answer", "schema": schemas[constraint]},
                    },
                },
            )
        )
        if good:
            final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
            assert json.loads(final.completion().choices[0].message.content) == payload
            if not native:
                assert final.completion().choices[0].message.content == raw_content
            assert (await runtime.await_response(run.run_id, "anonymous")) == final
            checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
            assert checkpoint.run.status == "completed" and checkpoint.responses[-1] == final
        else:
            with pytest.raises(CGError) as failure:
                await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
            assert failure.value.code == (
                ErrorCode.INVALID_PARAMETER if native else ErrorCode.UPSTREAM_ERROR
            )
            checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
            assert checkpoint.run.status == "failed" and not checkpoint.responses
            assert checkpoint.run.output_json is None
        assert len(provider.requests) == (0 if native else 1)
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("native", [True, False])
@pytest.mark.parametrize(
    "schema",
    [
        {"type": 17},
        {"$schema": "https://example.invalid/unknown", "type": "object"},
        {"$ref": "#/$defs/missing"},
        {"$ref": "https://example.invalid/schema"},
    ],
)
async def test_final_schema_errors_are_sanitized_without_remote_retrieval(
    tmp_path, monkeypatch, native, schema
):
    fetched = []

    def forbidden_remote(*args, **kwargs):
        fetched.append(args)
        raise AssertionError("Remote schema retrieval is forbidden")

    monkeypatch.setattr("urllib.request.urlopen", forbidden_remote)

    async def handler(request):
        return response("{}")

    provider = Provider(handler)
    nodes = (
        [input_node("i"), output_node()] if native else [input_node("i"), llm("a"), output_node()]
    )
    edges = (
        [edge("i", "o", "answer")]
        if native
        else [edge("i", "a", "question"), edge("a", "o", "answer")]
    )
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(
                graph(nodes=nodes, edges=edges),
                inputs={"chat": {}},
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "answer", "schema": schema},
                    },
                },
            )
        )
        with pytest.raises(CGError) as failure:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert failure.value.code == (
            ErrorCode.INVALID_PARAMETER if native else ErrorCode.UPSTREAM_ERROR
        )
        assert "example.invalid" not in failure.value.message
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "failed" and not checkpoint.responses
        assert checkpoint.run.output_json is None and not fetched
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("content", ["not JSON", "[]", '"scalar"', None, '{"value":Infinity}'])
@pytest.mark.parametrize("finish", ["stop", "length"])
async def test_ordinary_provider_json_object_rejects_malformed_content(tmp_path, content, finish):
    async def handler(request):
        result = response(content)
        result.choices[0].finish_reason = finish
        return result

    value = graph(
        nodes=[input_node("i"), llm("a"), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(value, client={"model": "cg/g", "response_format": {"type": "json_object"}})
        )
        with pytest.raises(CGError) as failure:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert failure.value.code == ErrorCode.UPSTREAM_ERROR
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "failed" and not checkpoint.responses
    finally:
        await runtime.shutdown()
        await repository.close()
