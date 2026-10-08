import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from test_loops import loop_graph
from test_scheduler import (
    Provider,
    create_runtime,
    edge,
    graph,
    input_node,
    llm,
    node_request,
    output_node,
    response,
    submission,
)

from app.contracts.api import ForcedToolChoice, ToolResult
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import (
    ContinuationRoute,
    PendingTool,
    ResponseEnvelope,
    ToolBatch,
    ToolCheckpoint,
    canonical_arguments_hash,
    canonical_json,
    raw_text_hash,
)
from app.graphs.validator import GraphValidator
from app.runtime.admission import BoundedAdmissionController
from app.runtime.clock import SystemClock
from app.runtime.engine import AsyncGraphRuntime
from app.storage.events import DurableEventBus
from app.storage.repository import SQLiteRunRepository

TOOLS = [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["cancelled", "failed", "interrupted"])
async def test_terminal_failure_rejects_saved_tool_envelope_before_delivery(tmp_path, status):
    async def handler(request):
        return response(
            None,
            [
                {
                    "id": "internal",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        )

    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        run = await runtime.submit(submission(value, tools=TOOLS))
        checkpoint = await wait_until(repository, run.run_id, lambda cp: bool(cp.responses))
        if status == "cancelled":
            await runtime.cancel(run.run_id, "anonymous")
        else:
            code = ErrorCode.INTERRUPTED if status == "interrupted" else ErrorCode.UPSTREAM_ERROR
            await repository.terminalize(
                run.run_id,
                status,
                CGError(code, "terminal before delivery").payload().error,
                runtime.clock.now(),
            )
        with pytest.raises(CGError):
            await runtime.await_response(run.run_id, "anonymous")
        assert (await repository.get_run(run.run_id, "anonymous")).status == status
        assert (
            await repository.load_checkpoint(run.run_id, "anonymous")
        ).responses == checkpoint.responses
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["cancelled", "expired", "interrupted"])
async def test_pending_delivery_waiter_rechecks_terminal_failure(tmp_path, monkeypatch, reason):
    async def handler(request):
        return response(
            None,
            [
                {
                    "id": "internal",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        )

    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    blocked = asyncio.Event()
    deliver = asyncio.Event()
    original = repository.load_checkpoint

    async def gated_read(run_id, namespace):
        if asyncio.current_task().get_name() == "pending-delivery":
            blocked.set()
            await deliver.wait()
        return await original(run_id, namespace)

    try:
        run = await runtime.submit(submission(value, tools=TOOLS))
        saved = await wait_until(repository, run.run_id, lambda cp: bool(cp.responses))
        monkeypatch.setattr(repository, "load_checkpoint", gated_read)
        waiter = asyncio.create_task(
            runtime.await_response(run.run_id, "anonymous"), name="pending-delivery"
        )
        await asyncio.wait_for(blocked.wait(), 2)
        if reason == "cancelled":
            await runtime.cancel(run.run_id, "anonymous")
            expected = ErrorCode.CANCELLED
        elif reason == "expired":
            expected = ErrorCode.TOOL_WAIT_TIMEOUT
            await repository.terminalize(
                run.run_id,
                "failed",
                CGError(expected, "expired").payload().error,
                saved.batches[0].expires_at + timedelta(seconds=1),
            )
        else:
            expected = ErrorCode.INTERRUPTED
            await repository.terminalize(
                run.run_id,
                "interrupted",
                CGError(expected, "interrupted").payload().error,
                runtime.clock.now(),
            )
        deliver.set()
        with pytest.raises(CGError) as error:
            await asyncio.wait_for(waiter, 2)
        assert error.value.code == expected
    finally:
        deliver.set()
        await runtime.shutdown()
        await repository.close()


class Bridge:
    """Contract fixture: exposes conservatively one call, never executes it."""

    def __init__(self, repository, clock):
        self.repository = repository
        self.clock = clock

    def map_calls(self, activation, completion):
        return tuple(
            PendingTool(
                external_id="cg_" + uuid.uuid4().hex,
                run_id=activation.key.run_id,
                activation_id=activation.activation_id,
                node_id=activation.key.node_id,
                provider_round=activation.provider_round + 1,
                call_ordinal=ordinal,
                internal_id=call.id,
                name=call.function.name,
                arguments=call.function.arguments,
                arguments_hash=raw_text_hash(call.function.arguments),
                canonical_arguments_hash=canonical_arguments_hash(call.function.arguments),
                status="unexposed",
            )
            for ordinal, call in enumerate(completion.choices[0].message.tool_calls)
        )

    async def prepare_batch(self, run_id, namespace):
        checkpoint = await self.repository.load_checkpoint(run_id, namespace)
        call = next(tool for tool in checkpoint.pending_tools if tool.status == "unexposed")
        batch_id = uuid.uuid4().hex
        completion = response(
            None,
            [
                {
                    "id": call.external_id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments},
                }
            ],
        )
        completion.model = "cg/" + checkpoint.run.snapshot.graph_id
        completion.id = "completion-" + batch_id
        envelope = ResponseEnvelope(
            run_id=run_id,
            batch_id=batch_id,
            response_sequence=len(checkpoint.responses) + 1,
            completion_json=completion.model_dump_json(),
        )
        batch = ToolBatch(
            batch_id=batch_id,
            run_id=run_id,
            sequence=envelope.response_sequence,
            status="open",
            external_ids=(call.external_id,),
            prepared_at=self.clock.now(),
            expires_at=self.clock.now()
            + timedelta(seconds=checkpoint.run.policy.tool_wait_timeout_seconds),
            envelope=envelope,
        )
        pending = call.model_copy(update={"status": "pending", "batch_id": batch_id})
        checkpoint = checkpoint.model_copy(
            update={
                "pending_tools": tuple(
                    pending if tool.external_id == call.external_id else tool
                    for tool in checkpoint.pending_tools
                ),
                "batches": checkpoint.batches + (batch,),
                "responses": checkpoint.responses + (envelope,),
            }
        )
        await self.repository.checkpoint_batch(
            ToolCheckpoint(checkpoint=checkpoint, batch=batch), checkpoint.run.state_version
        )
        return envelope


async def wait_until(repository, run_id, predicate):
    for _ in range(300):
        checkpoint = await repository.load_checkpoint(run_id, "anonymous")
        if predicate(checkpoint):
            return checkpoint
        await asyncio.sleep(0.01)
    raise AssertionError("Expected durable transition did not occur")


async def tool_runtime(tmp_path, provider, settings=None, clock=None):
    settings = settings or Settings()
    repository = SQLiteRunRepository(tmp_path / "runs.sqlite")
    await repository.initialize()
    clock = clock or SystemClock()
    bridge = Bridge(repository, clock)
    runtime = AsyncGraphRuntime(
        settings,
        repository,
        GraphValidator(),
        provider,
        bridge,
        DurableEventBus(repository),
        BoundedAdmissionController(settings.max_active_runs, settings.max_queued_runs),
        clock,
    )
    return runtime, repository, bridge


async def accept(repository, runtime, envelope, content="result"):
    call = envelope.completion().choices[0].message.tool_calls[0]
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id=envelope.run_id,
        batch_id=envelope.batch_id,
        results=(ToolResult(tool_call_id=call.id, content=content),),
    )
    acceptance = await repository.accept_results(
        route, raw_text_hash(canonical_json(route.model_dump())), runtime.clock.now()
    )
    await runtime.resume(acceptance)
    return acceptance, route


@pytest.mark.asyncio
async def test_quiescent_serial_batches_owner_history_and_exact_response_association(tmp_path):
    sibling = asyncio.Event()
    calls = {"a": 0, "b": 0}

    async def handler(request):
        node = node_request(request)
        if node == "s":
            return response("synthesis")
        calls[node] += 1
        if calls[node] == 1:
            if node == "b":
                await sibling.wait()
            return response(
                None,
                [
                    {
                        "id": "same",
                        "type": "function",
                        "function": {
                            "name": "read",
                            "arguments": json.dumps({"owner": node, "index": index}),
                        },
                    }
                    for index in range(2)
                ],
            )
        results = [message for message in request.messages if message.role == "tool"]
        assert len(results) == 2
        assert all(message.content.startswith(node) for message in results)
        return response(node + " payload")

    value = graph(nodes=[input_node("i"), llm("a", True), llm("b", True), llm("s"), output_node()])
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(value, tools=TOOLS, client={"model": "cg/g", "parallel_tool_calls": False})
        )
        checkpoint = await wait_until(
            repository,
            run.run_id,
            lambda cp: any(item.status == "waiting_tools" for item in cp.activations),
        )
        assert not checkpoint.responses
        assert any(item.status == "running" for item in checkpoint.activations)
        sibling.set()
        first = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        claims = []
        response_sequence = 0
        seen = set()
        for _ in range(4):
            batch = await asyncio.wait_for(
                runtime.await_response(run.run_id, "anonymous", response_sequence), 3
            )
            call = batch.completion().choices[0].message.tool_calls[0]
            assert call.id not in seen
            seen.add(call.id)
            owner = json.loads(call.function.arguments)["owner"]
            acceptance, route = await accept(repository, runtime, batch, owner + " result")
            claims.append((acceptance.claim.claim_id, route))
            response_sequence = batch.response_sequence
        final = await asyncio.wait_for(
            runtime.await_response(run.run_id, "anonymous", response_sequence), 3
        )
        assert final.completion().choices[0].message.content == "synthesis"
        assert calls == {"a": 2, "b": 2}
        for index, (id_, route) in enumerate(claims):
            claim = await repository.get_claim(id_)
            assert claim.envelope.response_sequence == index + 2
            assert claim.envelope != first
            replay = await repository.accept_results(
                route, raw_text_hash(canonical_json(route.model_dump())), runtime.clock.now()
            )
            assert replay.kind == "replay" and replay.claim.envelope == claim.envelope
        assert calls == {"a": 2, "b": 2}
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.tool_rounds == 4 and checkpoint.run.node_executions == 3
        assert checkpoint.run.upstream_attempts == 5
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("choice", ["required", {"type": "function", "function": {"name": "read"}}])
async def test_restart_original_ids_and_closed_batch_before_resume(tmp_path, choice):
    executions = 0

    async def handler(request):
        nonlocal executions
        executions += 1
        if executions == 1:
            assert request.tool_choice == (
                choice if isinstance(choice, str) else ForcedToolChoice.model_validate(choice)
            )
            return response(
                None,
                [
                    {
                        "id": "internal",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            )
        assert request.tool_choice == "auto"
        assert request.messages[-1].role == "tool" and request.messages[-1].content == "fixture"
        return response("resumed")

    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    run = await runtime.submit(
        submission(value, tools=TOOLS, client={"model": "cg/g", "tool_choice": choice})
    )
    batch = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
    await runtime.shutdown()
    call = batch.completion().choices[0].message.tool_calls[0]
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id=run.run_id,
        batch_id=batch.batch_id,
        results=(ToolResult(tool_call_id=call.id, content="fixture"),),
    )
    acceptance = await repository.accept_results(
        route, raw_text_hash("closed-before-restart"), datetime.now(UTC)
    )
    assert acceptance.kind == "ready"
    await repository.close()
    # This represents a crash after accept commit and before resume notification.
    later = SystemClock()
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler), clock=later)
    try:
        await runtime.recover()
        await asyncio.gather(runtime.resume(acceptance), runtime.resume(acceptance))
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous", 1), 3)
        assert result.completion().choices[0].message.content == "resumed"
        assert executions == 2
        replay = await repository.accept_results(
            route, raw_text_hash("closed-before-restart"), datetime.now(UTC)
        )
        assert replay.kind == "replay" and replay.claim.envelope == result
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_controller_json_final_survives_closed_batch_recovery_and_exact_replay(tmp_path):
    payload = '123 "escaped"\nnull'
    controller_calls = 0

    async def handler(request):
        nonlocal controller_calls
        if node_request(request) == "draft":
            return response("draft")
        controller_calls += 1
        if controller_calls == 1:
            return response(
                None,
                [
                    {
                        "id": "original",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            )
        assert request.messages[-1].role == "tool"
        assert request.messages[-1].tool_call_id == "original"
        emitted = request.response_format.json_schema.schema_["properties"]["payload"]
        assert {key: value for key, value in emitted.items() if key != "$id"} == {"const": payload}
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    provider = Provider(handler)
    value = loop_graph()
    next(node for node in value.nodes if node.id == "critique").tools_enabled = True
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    run = await runtime.submit(
        submission(
            value,
            tools=TOOLS,
            client={
                "model": "cg/g",
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "answer", "strict": True, "schema": {"const": payload}},
                },
            },
        )
    )
    batch = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
    await runtime.shutdown()
    call = batch.completion().choices[0].message.tool_calls[0]
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id=run.run_id,
        batch_id=batch.batch_id,
        results=(ToolResult(tool_call_id=call.id, content="saved"),),
    )
    request_hash = raw_text_hash("controller-json-replay")
    accepted = await repository.accept_results(route, request_hash, datetime.now(UTC))
    assert accepted.kind == "ready"
    await repository.close()
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous", 1), 3)
        assert json.loads(final.completion().choices[0].message.content) == payload
        saved = await repository.load_checkpoint(run.run_id, "anonymous")
        assert saved.run.output_json == canonical_json(payload)
        assert saved.responses[-1] == final
        assert (
            await repository.accept_results(route, request_hash, datetime.now(UTC))
        ).claim.envelope == final
        assert controller_calls == 2 and len(provider.requests) == 3
    finally:
        await runtime.shutdown()
        await repository.close()

    # Reconstructed completed runs return the exact saved JSON without inference.
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert (await runtime.await_response(run.run_id, "anonymous", 1)) == final
        replay = await repository.accept_results(route, request_hash, datetime.now(UTC))
        assert replay.kind == "replay" and replay.claim.envelope == final
        assert controller_calls == 2 and len(provider.requests) == 3
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_cancel_late_results_and_initial_disconnect_preserves_exposure(tmp_path):
    async def handler(request):
        return response(
            None,
            [
                {
                    "id": "internal",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        )

    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(submission(value, tools=TOOLS))
        batch = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert (await runtime.detach_initial(run.run_id, "anonymous")).status == "waiting_tools"
        assert (await runtime.await_response(run.run_id, "anonymous")) == batch
        assert (await runtime.cancel(run.run_id, "anonymous")).status == "cancelled"
        with pytest.raises(CGError):
            await accept(repository, runtime, batch)
        assert (await runtime.cancel(run.run_id, "anonymous")).status == "cancelled"
    finally:
        await runtime.shutdown()
        await repository.close()


class FakeClock:
    def __init__(self):
        self.elapsed = 0.0
        self.waits = []

    def now(self):
        return datetime(2026, 10, 3, tzinfo=UTC) + timedelta(seconds=self.elapsed)

    def monotonic(self):
        return self.elapsed

    async def sleep(self, seconds):
        if seconds <= 0:
            return
        future = asyncio.get_running_loop().create_future()
        self.waits.append((self.elapsed + seconds, future))
        await future

    def advance(self, seconds):
        self.elapsed += seconds
        for deadline, future in self.waits:
            if deadline <= self.elapsed and not future.done():
                future.set_result(None)


@pytest.mark.asyncio
@pytest.mark.parametrize("active_timeout", [True, False])
async def test_active_timeout_cancels_inference_with_fake_clock(tmp_path, active_timeout):
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def handler(request):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    clock = FakeClock()
    settings = Settings(
        run_active_timeout_seconds=2 if active_timeout else 100,
        llm_timeout_seconds=100 if active_timeout else 2,
    )
    runtime, repository = await create_runtime(tmp_path, Provider(handler), settings, clock=clock)
    try:
        run = await runtime.submit(submission(graph(), settings))
        await started.wait()
        for _ in range(10):
            await asyncio.sleep(0)
        clock.advance(3)
        checkpoint = await wait_until(repository, run.run_id, lambda cp: cp.run.status == "failed")
        assert json.loads(checkpoint.run.error_json)["code"] == (
            "run_timeout" if active_timeout else "llm_timeout"
        )
        assert checkpoint.run.active_elapsed_seconds == 3
        await asyncio.wait_for(cancelled.wait(), 1)
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_fixed_wait_excludes_active_time_and_partial_expiry(tmp_path):
    async def handler(request):
        return response(
            None,
            [
                {
                    "id": "internal",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        )

    clock = FakeClock()
    settings = Settings(run_active_timeout_seconds=2, tool_wait_timeout_seconds=10)
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler), settings, clock)
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        run = await runtime.submit(submission(value, settings, tools=TOOLS))
        before = await wait_until(repository, run.run_id, lambda cp: bool(cp.responses))
        clock.advance(5)
        await asyncio.sleep(0.02)
        waiting = await repository.load_checkpoint(run.run_id, "anonymous")
        assert waiting.run.status == "waiting_tools"
        assert waiting.run.active_elapsed_seconds == before.run.active_elapsed_seconds == 0
        clock.advance(6)
        failed = await wait_until(repository, run.run_id, lambda cp: cp.run.status == "failed")
        assert json.loads(failed.run.error_json)["code"] == "tool_wait_timeout"
        assert failed.run.active_elapsed_seconds == 0
        with pytest.raises(CGError) as error:
            await runtime.await_response(run.run_id, "anonymous")
        assert error.value.code == ErrorCode.TOOL_WAIT_TIMEOUT
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_stale_open_frontier_does_not_expire_accepted_closed_batch(tmp_path):
    executions = 0

    async def handler(request):
        nonlocal executions
        executions += 1
        if executions == 1:
            return response(
                None,
                [
                    {
                        "id": "internal",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            )
        return response("after downtime")

    clock = FakeClock()
    settings = Settings(tool_wait_timeout_seconds=10)
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler), settings, clock)
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    run = await runtime.submit(submission(value, settings, tools=TOOLS))
    stale = await wait_until(repository, run.run_id, lambda cp: bool(cp.responses))
    await runtime.shutdown()
    call = stale.responses[0].completion().choices[0].message.tool_calls[0]
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id=run.run_id,
        batch_id=stale.batches[0].batch_id,
        results=(ToolResult(tool_call_id=call.id, content="result"),),
    )
    clock.advance(9)
    acceptance = await repository.accept_results(route, raw_text_hash("pre-expiry"), clock.now())
    accepted = await repository.load_checkpoint(run.run_id, "anonymous")
    await repository.save_checkpoint(
        accepted.model_copy(update={"run": accepted.run.model_copy(update={"status": "running"})}),
        accepted.run.state_version,
    )
    clock.advance(100)
    await repository.close()
    recovered, repository, _ = await tool_runtime(tmp_path, Provider(handler), settings, clock)
    try:
        await recovered.recover()
        # A scheduler holding an older open frontier must reload the closed DB state.
        await recovered._wait_tools(stale, "anonymous")
        completed = await wait_until(
            repository, run.run_id, lambda cp: cp.run.status == "completed"
        )
        assert completed.responses[-1].completion().choices[0].message.content == "after downtime"
        assert executions == 2
        assert completed.run.active_elapsed_seconds == 0
        assert (
            await repository.get_claim(acceptance.claim.claim_id)
        ).envelope == completed.responses[-1]
    finally:
        await recovered.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_queued_recovery_interrupts_uncertain_attempt_without_rerun(tmp_path):
    entered = asyncio.Event()
    calls = 0

    async def hanging(request):
        nonlocal calls
        calls += 1
        entered.set()
        await asyncio.Event().wait()

    settings = Settings(max_active_runs=1, max_queued_runs=1)
    runtime, repository = await create_runtime(tmp_path, Provider(hanging), settings)
    value = graph(
        nodes=[input_node("i"), llm("a"), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    first = await runtime.submit(submission(value, settings))
    await entered.wait()
    queued = await runtime.submit(submission(value, settings))
    with pytest.raises(CGError) as overflow:
        await runtime.submit(submission(value, settings))
    assert overflow.value.status_code == 429
    assert (await repository.get_run(queued.run_id, "anonymous")).status == "queued"
    await runtime.shutdown()
    assert (await repository.get_run(first.run_id, "anonymous")).status == "interrupted"
    assert (await repository.get_run(queued.run_id, "anonymous")).status == "queued"
    await repository.close()

    async def finish(request):
        nonlocal calls
        calls += 1
        return response("recovered queued")

    runtime, repository = await create_runtime(tmp_path, Provider(finish), settings)
    try:
        await runtime.recover()
        result = await asyncio.wait_for(runtime.await_response(queued.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == "recovered queued"
        assert calls == 2
        assert (await repository.get_run(first.run_id, "anonymous")).upstream_attempts == 1
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_waiting_tools_keeps_admission_slot_and_queue_cancel_releases_it(tmp_path):
    async def handler(request):
        return response(
            None,
            [
                {
                    "id": "internal",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        )

    settings = Settings(max_active_runs=1, max_queued_runs=1)
    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler), settings)
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        first = await runtime.submit(submission(value, settings, tools=TOOLS))
        await asyncio.wait_for(runtime.await_response(first.run_id, "anonymous"), 3)
        queued = await runtime.submit(submission(value, settings, tools=TOOLS))
        with pytest.raises(CGError):
            await runtime.submit(submission(value, settings, tools=TOOLS))
        assert (await repository.get_run(queued.run_id, "anonymous")).status == "queued"
        await runtime.cancel(queued.run_id, "anonymous")
        next_run = await runtime.submit(submission(value, settings, tools=TOOLS))
        await runtime.cancel(first.run_id, "anonymous")
        await asyncio.wait_for(runtime.await_response(next_run.run_id, "anonymous"), 3)
        assert (await repository.get_run(next_run.run_id, "anonymous")).status == "waiting_tools"
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_required_controller_tools_reset_per_loop_activation_then_allow_control(tmp_path):
    from test_loops import loop_graph

    value = loop_graph()
    value.nodes[2].tools_enabled = True
    iterations = 0

    async def handler(request):
        nonlocal iterations
        if node_request(request) == "draft":
            assert not request.tools and request.tool_choice is None
            return response("draft")
        if request.messages[-1].role != "tool":
            assert request.tool_choice == "required"
            return response(
                None,
                [
                    {
                        "id": "internal",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            )
        assert request.tool_choice == "auto" and request.messages[-1].content == "fixture"
        assert request.response_format.type == "json_schema"
        iterations += 1
        return response(
            json.dumps(
                {
                    "payload": "finished",
                    "control": {"decision": "continue" if iterations == 1 else "stop"},
                }
            )
        )

    provider = Provider(handler)
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(value, tools=TOOLS, client={"model": "cg/g", "tool_choice": "required"})
        )
        cursor = 0
        for _ in range(2):
            batch = await asyncio.wait_for(
                runtime.await_response(run.run_id, "anonymous", cursor), 3
            )
            await accept(repository, runtime, batch, "fixture")
            cursor = batch.response_sequence
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous", cursor), 3)
        assert final.completion().choices[0].message.content == "finished"
        saved = await repository.get_run(run.run_id, "anonymous")
        assert (
            saved.node_executions == 4 and saved.upstream_attempts == 6 and saved.tool_rounds == 2
        )
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("choice", ["required", {"type": "function", "function": {"name": "read"}}])
async def test_required_tool_cannot_be_satisfied_by_plain_text(tmp_path, choice):
    async def handler(request):
        return response("no call")

    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    value = graph(
        nodes=[input_node("i"), llm("a", True), output_node()],
        edges=[edge("i", "a", "question"), edge("a", "o", "answer")],
    )
    try:
        run = await runtime.submit(
            submission(value, tools=TOOLS, client={"model": "cg/g", "tool_choice": choice})
        )
        with pytest.raises(CGError) as failed:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert failed.value.code.value == "upstream_error"
        assert (await repository.get_run(run.run_id, "anonymous")).output_json is None
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_none_disables_tools_throughout_graph(tmp_path):
    async def handler(request):
        assert not request.tools
        assert request.tool_choice == "none"
        return response("no tool")

    runtime, repository, _ = await tool_runtime(tmp_path, Provider(handler))
    value = graph(nodes=[input_node("i"), llm("a", True), llm("b", True), llm("s"), output_node()])
    try:
        run = await runtime.submit(
            submission(value, tools=TOOLS, client={"model": "cg/g", "tool_choice": "none"})
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == "no tool"
        assert not (await repository.load_checkpoint(run.run_id, "anonymous")).pending_tools
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_invalid_controller_final_after_tool_recovery_never_seals_success(tmp_path):
    calls = 0

    async def handler(request):
        nonlocal calls
        if node_request(request) == "draft":
            return response("draft")
        calls += 1
        if calls == 1:
            return response(
                None,
                [
                    {
                        "id": "original",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    }
                ],
            )
        assert request.messages[-1].role == "tool"
        assert request.messages[-1].tool_call_id == "original"
        return response('{"payload":{"value":3},"control":{"decision":"stop"}}')

    value = loop_graph()
    next(node for node in value.nodes if node.id == "critique").tools_enabled = True
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "",
        "$defs": {"Text": {"type": "string"}},
        "type": "object",
        "properties": {"value": {"$ref": "#/$defs/Text"}},
        "required": ["value"],
    }
    provider = Provider(handler)
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    run = await runtime.submit(
        submission(
            value,
            tools=TOOLS,
            client={
                "model": "cg/g",
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "answer", "schema": schema},
                },
            },
        )
    )
    batch = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
    await runtime.shutdown()
    call = batch.completion().choices[0].message.tool_calls[0]
    route = ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id=run.run_id,
        batch_id=batch.batch_id,
        results=(ToolResult(tool_call_id=call.id, content="saved"),),
    )
    request_hash = raw_text_hash("invalid-final-after-recovery")
    accepted = await repository.accept_results(route, request_hash, datetime.now(UTC))
    assert accepted.kind == "ready"
    await repository.close()
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        with pytest.raises(CGError) as failure:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous", 1), 3)
        assert failure.value.code == ErrorCode.UPSTREAM_ERROR
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "failed" and checkpoint.run.output_json is None
        assert checkpoint.responses == (batch,)
        assert (await repository.get_claim(accepted.claim.claim_id)).envelope is None
        with pytest.raises(CGError):
            await repository.accept_results(route, request_hash, datetime.now(UTC))
        with pytest.raises(CGError):
            await runtime.await_response(run.run_id, "anonymous")
        assert calls == 2 and len(provider.requests) == 3
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository, _ = await tool_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        with pytest.raises(CGError) as failure:
            await runtime.await_response(run.run_id, "anonymous")
        assert failure.value.code == ErrorCode.UPSTREAM_ERROR
        assert calls == 2 and len(provider.requests) == 3
    finally:
        await runtime.shutdown()
        await repository.close()
