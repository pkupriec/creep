import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest

from app.contracts.api import ChatCompletionRequest, ChatCompletionResponse, ToolResult
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import Graph
from app.contracts.interfaces import (
    ActivationKey,
    ActivationRecord,
    ContinuationRoute,
    GraphSnapshot,
    NewRunRoute,
    ResponseEnvelope,
    RunContext,
    RunPolicy,
    RunSubmission,
    ToolBatch,
    ToolCheckpoint,
    canonical_json,
)
from app.graphs.validator import GraphValidator
from app.storage.events import DurableEventBus
from app.storage.repository import SQLiteRunRepository
from app.tools.bridge import DurableToolBridge, canonical_request_hash

NOW = datetime(2026, 10, 4, tzinfo=UTC)


class Clock:
    def __init__(self):
        self.time = NOW

    def now(self):
        return self.time

    def monotonic(self):
        return (self.time - NOW).total_seconds()

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)


def response(calls=1):
    return ChatCompletionResponse.model_validate(
        {
            "id": "provider",
            "created": 1,
            "model": "fixture",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "same" if ordinal == 0 else "same" + str(ordinal),
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{ "x": 1, "y": 2 }',
                                },
                            }
                            for ordinal in range(calls)
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
        }
    )


def submission(namespace="anonymous"):
    graph = Graph.model_validate(
        {
            "schema_version": 1,
            "id": "g",
            "name": "Graph",
            "revision": 1,
            "base_model": "fixture",
            "inputs": [{"id": "chat", "required": True}],
            "nodes": [
                {"id": "i", "type": "input", "input_id": "chat"},
                {
                    "id": "a",
                    "type": "llm",
                    "system_prompt": "Analyze",
                    "tools_enabled": True,
                    "generation": {},
                },
                {
                    "id": "b",
                    "type": "llm",
                    "system_prompt": "Analyze",
                    "tools_enabled": True,
                    "generation": {},
                },
                {"id": "o", "type": "output"},
            ],
            "edges": [
                {"id": "ia", "source": "i", "target": "a", "target_port": "q", "kind": "forward"},
                {"id": "ab", "source": "a", "target": "b", "target_port": "q", "kind": "forward"},
                {
                    "id": "bo",
                    "source": "b",
                    "target": "o",
                    "target_port": "answer",
                    "kind": "forward",
                },
            ],
            "loops": [],
            "output_node_id": "o",
        }
    )
    request = ChatCompletionRequest(
        model="cg/g", messages=[{"role": "user", "content": "question"}]
    )
    return RunSubmission(
        plan=GraphValidator().compile(GraphSnapshot.from_graph(graph)),
        context=RunContext(namespace=namespace, messages_json="[]", tools_json="[]"),
        inputs_json='{"chat":"question"}',
        policy=RunPolicy(
            client_request_json=canonical_json(request.model_dump(mode="json")),
            max_node_executions=10,
            max_tool_rounds=5,
            active_timeout_seconds=100,
            tool_wait_timeout_seconds=10,
        ),
    )


@pytest.fixture
async def fixture(tmp_path):
    repository = SQLiteRunRepository(tmp_path / "runs.sqlite")
    await repository.initialize()
    clock = Clock()
    bridge = DurableToolBridge(Settings(), repository, DurableEventBus(repository), clock)
    await repository.create_run(submission(), "r", NOW)
    try:
        yield repository, bridge, clock
    finally:
        await repository.close()


async def add_calls(repository, bridge, node="a", count=1, run_id="r"):
    checkpoint = await repository.load_checkpoint(run_id, "anonymous")
    activation = ActivationRecord(
        activation_id=run_id + node,
        key=ActivationKey(run_id=run_id, scope_key="", iteration=0, node_id=node),
        status="waiting_tools",
        inputs=(),
        messages_json="[]",
    )
    mappings = bridge.map_calls(activation, response(count))
    activation = activation.model_copy(update={"provider_round": 1})
    await repository.save_checkpoint(
        checkpoint.model_copy(
            update={
                "run": checkpoint.run.model_copy(update={"status": "waiting_tools"}),
                "activations": checkpoint.activations + (activation,),
                "pending_tools": checkpoint.pending_tools + mappings,
            }
        ),
        checkpoint.run.state_version,
    )
    return mappings


def continuation(envelope, content="result", **overrides):
    message = envelope.completion().choices[0].message.model_dump(mode="json", exclude_none=True)
    return ChatCompletionRequest.model_validate(
        {
            "model": "cg/g",
            "messages": [
                {"role": "user", "content": "question"},
                message,
                {
                    "role": "tool",
                    "tool_call_id": message["tool_calls"][0]["id"],
                    "content": content,
                },
            ],
            **overrides,
        }
    )


async def finish(repository, run_id="r"):
    checkpoint = await repository.load_checkpoint(run_id, "anonymous")
    envelope = ResponseEnvelope(
        run_id=run_id,
        batch_id=None,
        response_sequence=len(checkpoint.responses) + 1,
        completion_json=canonical_json(
            {
                "id": "final",
                "created": 1,
                "model": "cg/g",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "answer"},
                        "finish_reason": "stop",
                    }
                ],
            }
        ),
    )
    completed = tuple(
        item.model_copy(update={"status": "completed", "payload_json": '"answer"', "ended_at": NOW})
        for item in checkpoint.activations
    )
    output = ActivationRecord(
        activation_id="output",
        key=ActivationKey(run_id=run_id, scope_key="", iteration=0, node_id="o"),
        status="completed",
        inputs=(),
        messages_json="[]",
        payload_json='"answer"',
        ended_at=NOW,
    )
    await repository.complete_run(
        checkpoint.model_copy(
            update={
                "run": checkpoint.run.model_copy(
                    update={"status": "completed", "ended_at": NOW, "output_json": '"answer"'}
                ),
                "activations": completed + (output,),
                "responses": checkpoint.responses + (envelope,),
            }
        ),
        envelope,
        checkpoint.run.state_version,
    )
    return envelope


async def test_unique_owner_mapping_raw_args_and_round(fixture):
    repository, bridge, _ = fixture
    a = await add_calls(repository, bridge, count=2)
    b = await add_calls(repository, bridge, node="b")
    assert len({item.external_id for item in a + b}) == 3
    assert all(item.external_id.startswith("cg_") for item in a + b)
    assert [item.call_ordinal for item in a] == [0, 1]
    assert all(item.provider_round == 1 for item in a + b)
    assert a[0].internal_id == b[0].internal_id == "same"
    assert a[0].arguments == '{ "x": 1, "y": 2 }'


async def test_serial_exposure_idempotence_and_first_next_response(fixture):
    repository, bridge, _ = fixture
    calls = await add_calls(repository, bridge, count=2)
    first = await bridge.prepare_batch("r", "anonymous")
    assert first == await bridge.prepare_batch("r", "anonymous")
    assert len(first.completion().choices[0].message.tool_calls) == 1
    req = continuation(first)
    route = await bridge.classify(req, "anonymous")
    accepted = await bridge.accept(route, canonical_request_hash(req))
    assert accepted.kind == "ready"
    assert (await bridge.accept(route, canonical_request_hash(req))).kind == "joined"
    second = await bridge.prepare_batch("r", "anonymous")
    assert await bridge.await_response(accepted.claim.claim_id) == second
    assert second.completion().choices[0].message.tool_calls[0].id == calls[1].external_id
    assert (await bridge.accept(route, canonical_request_hash(req))).claim.envelope == second
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    assert checkpoint.run.tool_rounds == 2
    assert checkpoint.activations[0].status == "waiting_tools"


async def test_restart_exact_final_replay_and_changed_result(fixture):
    repository, bridge, clock = fixture
    await add_calls(repository, bridge)
    exposed = await bridge.prepare_batch("r", "anonymous")
    # A new bridge/repository connection must use the same opaque mappings.
    await repository.close()
    restored = SQLiteRunRepository(repository.database_path)
    await restored.initialize()
    try:
        resumed = DurableToolBridge(Settings(), restored, DurableEventBus(restored), clock)
        req = continuation(exposed)
        route = await resumed.classify(req, "anonymous")
        acceptance = await resumed.accept(route, canonical_request_hash(req))
        final = await finish(restored)
        assert await resumed.await_response(acceptance.claim.claim_id) == final
        replay = await resumed.accept(route, canonical_request_hash(req))
        assert replay.kind == "replay" and replay.claim.envelope == final
        assert isinstance(
            await resumed.classify(continuation(exposed), "anonymous"), ContinuationRoute
        )
        changed = continuation(exposed, "CHANGED")
        with pytest.raises(CGError, match="differs"):
            await resumed.accept(
                await resumed.classify(changed, "anonymous"), canonical_request_hash(changed)
            )
    finally:
        await restored.close()


async def test_echo_canonical_arguments_and_conflicting_echo(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    exposed = await bridge.prepare_batch("r", "anonymous")
    req = continuation(exposed)
    req.messages[1].tool_calls[0].function.arguments = '{"y":2,"x":1}'
    assert isinstance(await bridge.classify(req, "anonymous"), ContinuationRoute)
    saved = await repository.load_checkpoint("r", "anonymous")
    assert saved.pending_tools[0].arguments == '{ "x": 1, "y": 2 }'
    req.messages[1].tool_calls[0].function.arguments = '{"x":99,"y":2}'
    with pytest.raises(CGError):
        await bridge.classify(req, "anonymous")


def test_canonical_request_hash_defaults_stream_policy_raw_strings():
    base = {"model": "cg/g", "messages": [{"role": "user", "content": "hello"}]}
    implicit = ChatCompletionRequest.model_validate(base)
    explicit = ChatCompletionRequest.model_validate(
        {
            **base,
            "stream": False,
            "parallel_tool_calls": True,
            "n": 1,
            "tools": None,
            "temperature": None,
        }
    )
    assert canonical_request_hash(implicit) == canonical_request_hash(explicit)
    for override in ({"stream": True}, {"parallel_tool_calls": False}, {"temperature": 0.2}):
        changed = ChatCompletionRequest.model_validate({**base, **override})
        assert canonical_request_hash(changed) != canonical_request_hash(implicit)


async def test_concurrent_preparation_and_acceptance_share_one_exposure_and_claim(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    one, two = await asyncio.gather(
        bridge.prepare_batch("r", "anonymous"), bridge.prepare_batch("r", "anonymous")
    )
    assert one == two
    req = continuation(one)
    route = await bridge.classify(req, "anonymous")
    first, second = await asyncio.gather(
        bridge.accept(route, canonical_request_hash(req)),
        bridge.accept(route, canonical_request_hash(req)),
    )
    assert {first.kind, second.kind} == {"ready", "joined"}
    assert first.claim.claim_id == second.claim.claim_id
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    assert checkpoint.run.tool_rounds == len(checkpoint.responses) == 1


async def test_late_cancelled_results_and_oversize_manual_results(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    req = continuation(await bridge.prepare_batch("r", "anonymous"))
    route = await bridge.classify(req, "anonymous")
    huge = route.model_copy(
        update={
            "results": (
                ToolResult(
                    tool_call_id=route.results[0].tool_call_id, content="x" * (1024 * 1024 + 1)
                ),
            )
        }
    )
    with pytest.raises(CGError) as caught:
        await bridge.accept(huge, "a" * 64)
    assert caught.value.code == ErrorCode.REQUEST_TOO_LARGE
    await repository.terminalize("r", "cancelled", None, NOW)
    with pytest.raises(CGError) as caught:
        await bridge.accept(route, canonical_request_hash(req))
    assert caught.value.code == ErrorCode.RUN_TERMINAL


async def test_invalid_unicode_tool_result_is_sanitized(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    req = continuation(await bridge.prepare_batch("r", "anonymous"), "\ud800")
    with pytest.raises(CGError) as caught:
        await bridge.classify(req, "anonymous")
    assert caught.value.code == ErrorCode.INVALID_PARAMETER


async def test_closed_old_batch_nonexact_request_cannot_bind_latest_response(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge, count=2)
    first = await bridge.prepare_batch("r", "anonymous")
    req = continuation(first)
    route = await bridge.classify(req, "anonymous")
    accepted = await bridge.accept(route, canonical_request_hash(req))
    second = await bridge.prepare_batch("r", "anonymous")
    changed = req.model_copy(update={"stream": True})
    with pytest.raises(CGError) as caught:
        await bridge.accept(route, canonical_request_hash(changed))
    assert caught.value.code == ErrorCode.CONTINUATION_CONFLICT
    assert await bridge.await_response(accepted.claim.claim_id) == second


async def test_compressed_tool_only_history_routes_saved_owner(fixture):
    repository, bridge, _ = fixture
    calls = await add_calls(repository, bridge)
    await bridge.prepare_batch("r", "anonymous")
    req = ChatCompletionRequest(
        model="cg/g",
        messages=[
            {"role": "system", "content": "Summary"},
            {"role": "tool", "tool_call_id": calls[0].external_id, "content": "file contents"},
        ],
    )
    route = await bridge.classify(req, "anonymous")
    assert route.run_id == "r" and route.results[0].content == "file contents"


@pytest.mark.parametrize("physical_id", ["native-id", "cg_unknown_physical"])
async def test_direct_physical_tool_ids_forward_without_graph_namespace(fixture, physical_id):
    _, bridge, _ = fixture
    req = ChatCompletionRequest(
        model="ollama/fixture",
        messages=[
            {"role": "user", "content": "question"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": physical_id,
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": physical_id, "content": "result"},
        ],
    )
    before = req.model_dump_json()
    assert isinstance(await bridge.classify(req, "anonymous"), NewRunRoute)
    assert req.model_dump_json() == before


async def test_known_graph_ids_cannot_resume_direct_model_but_old_history_is_ignored(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    req = continuation(await bridge.prepare_batch("r", "anonymous"))
    req.model = "ollama/fixture"
    with pytest.raises(CGError) as caught:
        await bridge.classify(req, "anonymous")
    assert caught.value.code == ErrorCode.CONTINUATION_CONFLICT
    body = req.model_dump(mode="json")
    body["messages"].extend(
        [{"role": "assistant", "content": "old final"}, {"role": "user", "content": "new turn"}]
    )
    req = ChatCompletionRequest.model_validate(body)
    assert isinstance(await bridge.classify(req, "anonymous"), NewRunRoute)


@pytest.mark.parametrize("arguments", ['{"x":1,"x":2}', '{"x":NaN}', "[]", "not json"])
async def test_invalid_raw_arguments_fail_before_exposure(fixture, arguments):
    _, bridge, _ = fixture
    activation = ActivationRecord(
        activation_id="a",
        key=ActivationKey(run_id="r", scope_key="", iteration=0, node_id="a"),
        status="running",
        inputs=(),
        messages_json="[]",
    )
    result = response()
    result.choices[0].message.tool_calls[0].function.arguments = arguments
    with pytest.raises(CGError) as caught:
        bridge.map_calls(activation, result)
    assert caught.value.code == ErrorCode.UPSTREAM_ERROR


@pytest.mark.parametrize("change", ["model", "namespace", "unknown", "mixed", "duplicate"])
async def test_routing_conflicts(fixture, change):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    req = continuation(await bridge.prepare_batch("r", "anonymous"))
    namespace = "anonymous"
    if change == "model":
        req.model = "cg/other"
    elif change == "namespace":
        namespace = "different"
    elif change == "unknown":
        req.messages[-1].tool_call_id = "cg_unknown"
    elif change == "mixed":
        req.messages.append(type(req.messages[0])(role="user", content="new question"))
    else:
        req.messages.append(req.messages[-1])
    with pytest.raises(CGError):
        await bridge.classify(req, namespace)


async def test_new_identical_questions_and_closed_historical_segment(fixture):
    repository, bridge, _ = fixture
    req = ChatCompletionRequest(model="cg/g", messages=[{"role": "user", "content": "same"}])
    assert isinstance(await bridge.classify(req, "anonymous"), NewRunRoute)
    assert isinstance(await bridge.classify(req, "anonymous"), NewRunRoute)
    await add_calls(repository, bridge)
    envelope = await bridge.prepare_batch("r", "anonymous")
    old = continuation(envelope)
    await bridge.accept(await bridge.classify(old, "anonymous"), canonical_request_hash(old))
    final = await finish(repository)
    old.messages.append(final.completion().choices[0].message)
    old.messages.append(type(req.messages[0])(role="user", content="same"))
    assert isinstance(await bridge.classify(old, "anonymous"), NewRunRoute)


async def test_ttl_and_cancel_reject_late_and_do_not_extend(fixture):
    repository, bridge, clock = fixture
    await add_calls(repository, bridge)
    envelope = await bridge.prepare_batch("r", "anonymous")
    before = await repository.load_checkpoint("r", "anonymous")
    clock.time += timedelta(seconds=5)
    assert await bridge.prepare_batch("r", "anonymous") == envelope
    assert (await repository.load_checkpoint("r", "anonymous")).batches[
        0
    ].expires_at == before.batches[0].expires_at
    clock.time += timedelta(seconds=5)
    req = continuation(envelope)
    with pytest.raises(CGError) as caught:
        await bridge.accept(await bridge.classify(req, "anonymous"), canonical_request_hash(req))
    assert caught.value.code == ErrorCode.TOOL_WAIT_TIMEOUT
    assert (await repository.get_run("r", "anonymous")).status == "failed"


async def test_cancellation_and_unquiescent_exposure(fixture):
    repository, bridge, _ = fixture
    await add_calls(repository, bridge)
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    activation = checkpoint.activations[0].model_copy(update={"status": "running"})
    await repository.save_checkpoint(
        checkpoint.model_copy(update={"activations": (activation,)}), checkpoint.run.state_version
    )
    with pytest.raises(CGError):
        await bridge.prepare_batch("r", "anonymous")
    await repository.terminalize("r", "cancelled", None, NOW)
    with pytest.raises(CGError):
        await bridge.prepare_batch("r", "anonymous")


async def test_partial_batch_claim_survives_until_first_subsequent_response(fixture):
    repository, bridge, clock = fixture
    calls = await add_calls(repository, bridge, count=2)
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    # Full-batch compatibility is tested even though unknown calls serialize by default.
    response_ = response(2).model_dump(mode="json")
    for call, mapping in zip(response_["choices"][0]["message"]["tool_calls"], calls, strict=True):
        call["id"] = mapping.external_id
    response_["model"] = "cg/g"
    envelope = ResponseEnvelope(
        run_id="r", batch_id="batch", response_sequence=1, completion_json=canonical_json(response_)
    )
    batch = ToolBatch(
        batch_id="batch",
        run_id="r",
        sequence=1,
        status="open",
        external_ids=tuple(c.external_id for c in calls),
        prepared_at=NOW,
        expires_at=NOW + timedelta(seconds=10),
        envelope=envelope,
    )
    await repository.checkpoint_batch(
        ToolCheckpoint(
            checkpoint=checkpoint.model_copy(
                update={
                    "pending_tools": tuple(
                        c.model_copy(update={"status": "pending", "batch_id": "batch"})
                        for c in calls
                    ),
                    "batches": (batch,),
                    "responses": (envelope,),
                }
            ),
            batch=batch,
        ),
        checkpoint.run.state_version,
    )
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id="r",
        batch_id="batch",
        results=(ToolResult(tool_call_id=calls[0].external_id, content="one"),),
    )
    partial = await bridge.accept(route, "a" * 64)
    assert partial.kind == "partial" and partial.missing_ids == (calls[1].external_id,)
    pending = asyncio.create_task(bridge.await_response(partial.claim.claim_id))
    await asyncio.sleep(0)
    assert not pending.done()
    route2 = route.model_copy(
        update={"results": (ToolResult(tool_call_id=calls[1].external_id, content="two"),)}
    )
    assert (await bridge.accept(route2, "b" * 64)).kind == "ready"
    clock.time += timedelta(seconds=20)
    final = await finish(repository)
    assert await asyncio.wait_for(pending, 1) == final
    assert (await repository.load_checkpoint("r", "anonymous")).batches[
        0
    ].expires_at == batch.expires_at


async def test_real_runtime_bridge_owner_round_and_internal_collision(tmp_path):
    from app.runtime.admission import BoundedAdmissionController
    from app.runtime.clock import SystemClock
    from app.runtime.engine import AsyncGraphRuntime

    class Provider:
        def __init__(self):
            self.requests = []

        async def complete(self, req):
            self.requests.append(req)
            results = [m for m in req.messages if m.role == "tool"]
            if results:
                return ChatCompletionResponse.model_validate(
                    {
                        "id": "provider-final",
                        "created": 1,
                        "model": "fixture",
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": "owner received "
                                    + ",".join(m.content for m in results),
                                },
                                "finish_reason": "stop",
                            }
                        ],
                    }
                )
            return response(2 if len(self.requests) == 1 else 1)

    repository = SQLiteRunRepository(tmp_path / "runtime.sqlite")
    await repository.initialize()
    clock = SystemClock()
    events = DurableEventBus(repository)
    bridge = DurableToolBridge(Settings(), repository, events, clock)
    provider = Provider()
    runtime = AsyncGraphRuntime(
        Settings(),
        repository,
        GraphValidator(),
        provider,
        bridge,
        events,
        BoundedAdmissionController(4, 20),
        clock,
    )
    original = submission()
    tools = [
        {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object"}}}
    ]
    policy = json.loads(original.policy.client_request_json)
    policy["tools"] = tools
    original = original.model_copy(
        update={
            "context": original.context.model_copy(update={"tools_json": canonical_json(tools)}),
            "policy": original.policy.model_copy(
                update={"client_request_json": canonical_json(policy)}
            ),
        }
    )
    try:
        run = await runtime.submit(original)
        envelope = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 2)
        first_claim = None
        for index in range(3):
            req = continuation(envelope, f"result{index}")
            accepted = await bridge.accept(
                await bridge.classify(req, "anonymous"), canonical_request_hash(req)
            )
            if first_claim is None:
                first_claim = accepted.claim.claim_id
            await runtime.resume(accepted)
            envelope = await asyncio.wait_for(bridge.await_response(accepted.claim.claim_id), 2)
            if index == 0:
                assert len(provider.requests) == 1
        assert envelope.completion().choices[0].message.content == "owner received result2"
        assert len(provider.requests) == 4
        owner_a_results = [m for m in provider.requests[1].messages if m.role == "tool"]
        owner_b_results = [m for m in provider.requests[3].messages if m.role == "tool"]
        assert [(m.tool_call_id, m.content) for m in owner_a_results] == [
            ("same", "result0"),
            ("same1", "result1"),
        ]
        assert [(m.tool_call_id, m.content) for m in owner_b_results] == [("same", "result2")]
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "completed" and checkpoint.run.tool_rounds == 3
        assert (await bridge.await_response(first_claim)).response_sequence == 2
    finally:
        await runtime.shutdown()
        await repository.close()
