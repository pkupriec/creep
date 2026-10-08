import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest

from app.contracts.api import ToolResult
from app.contracts.errors import CGError
from app.contracts.graph import Graph
from app.contracts.interfaces import (
    ActivationKey,
    ActivationRecord,
    CompiledGraph,
    ContinuationRoute,
    GraphSnapshot,
    PendingTool,
    ResponseEnvelope,
    RunContext,
    RunPolicy,
    RunSubmission,
    ToolBatch,
    ToolCheckpoint,
    canonical_arguments_hash,
    canonical_json,
    raw_text_hash,
)
from app.storage.repository import SQLiteRunRepository

NOW = datetime(2026, 10, 3, tzinfo=UTC)


def submission():
    graph = Graph.model_validate_json(
        json.dumps(
            {
                "schema_version": 1,
                "id": "g",
                "name": "Graph",
                "revision": 1,
                "base_model": "test",
                "inputs": [{"id": "chat", "required": True}],
                "nodes": [
                    {"id": "i", "type": "input", "input_id": "chat"},
                    {"id": "o", "type": "output"},
                ],
                "edges": [
                    {
                        "id": "e",
                        "source": "i",
                        "target": "o",
                        "target_port": "answer",
                        "kind": "forward",
                    }
                ],
                "loops": [],
                "output_node_id": "o",
            }
        )
    )
    return RunSubmission(
        plan=CompiledGraph(
            snapshot=GraphSnapshot.from_graph(graph),
            forward_order=("i", "o"),
            ports=(),
            loops=(),
            output_node_id="o",
            final_llm_node_id=None,
        ),
        context=RunContext(namespace="anonymous", messages_json="[]", tools_json="[]"),
        inputs_json='{"chat":"question"}',
        policy=RunPolicy(
            client_request_json='{"model":"cg/g"}',
            max_node_executions=10,
            max_tool_rounds=5,
            active_timeout_seconds=100,
            tool_wait_timeout_seconds=10,
        ),
    )


def envelope(run_id="r", batch_id=None, sequence=1, calls=None):
    message = {"role": "assistant", "content": "answer"}
    if calls:
        message = {"role": "assistant", "content": None, "tool_calls": calls}
    return ResponseEnvelope(
        run_id=run_id,
        batch_id=batch_id,
        response_sequence=sequence,
        completion_json=canonical_json(
            {
                "id": f"completion-{sequence}",
                "created": 1,
                "model": "cg/g",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "tool_calls" if calls else "stop",
                    }
                ],
            }
        ),
    )


async def expose(repository, ids=("cg_a", "cg_b"), sequence=1):
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    owner = ActivationRecord(
        activation_id="owner",
        key=ActivationKey(run_id="r", scope_key="", iteration=0, node_id="i"),
        status="waiting_tools",
        inputs=(),
        messages_json="[]",
        provider_round=sequence,
    )
    checkpoint = checkpoint.model_copy(update={"activations": (owner,)})
    mappings = tuple(
        PendingTool(
            external_id=external_id,
            run_id="r",
            activation_id="owner",
            node_id="i",
            provider_round=sequence,
            call_ordinal=index,
            internal_id="same",
            name="read",
            arguments="{}",
            arguments_hash=raw_text_hash("{}"),
            canonical_arguments_hash=canonical_arguments_hash("{}"),
            batch_id=f"b{sequence}",
            status="pending",
        )
        for index, external_id in enumerate(ids)
    )
    saved = checkpoint.model_copy(
        update={
            "pending_tools": checkpoint.pending_tools
            + tuple(
                tool.model_copy(update={"status": "unexposed", "batch_id": None})
                for tool in mappings
            )
        }
    )
    await repository.save_checkpoint(saved, checkpoint.run.state_version)
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    response = envelope(
        batch_id=f"b{sequence}",
        sequence=sequence,
        calls=[
            {"id": external_id, "type": "function", "function": {"name": "read", "arguments": "{}"}}
            for external_id in ids
        ],
    )
    batch = ToolBatch(
        batch_id=f"b{sequence}",
        run_id="r",
        sequence=sequence,
        status="open",
        external_ids=ids,
        prepared_at=NOW,
        expires_at=NOW + timedelta(seconds=10),
        envelope=response,
    )
    checkpoint = checkpoint.model_copy(
        update={
            "run": checkpoint.run.model_copy(update={"status": "waiting_tools"}),
            "pending_tools": tuple(
                tool for tool in checkpoint.pending_tools if tool.external_id not in ids
            )
            + mappings,
            "batches": checkpoint.batches + (batch,),
            "responses": checkpoint.responses + (response,),
        }
    )
    await repository.checkpoint_batch(
        ToolCheckpoint(checkpoint=checkpoint, batch=batch), checkpoint.run.state_version
    )
    return batch


def route(ids=("cg_a",), values=("result",), batch="b1"):
    return ContinuationRoute(
        namespace="anonymous",
        model="cg/g",
        run_id="r",
        batch_id=batch,
        results=tuple(
            ToolResult(tool_call_id=id_, content=value)
            for id_, value in zip(ids, values, strict=True)
        ),
    )


def final_checkpoint(checkpoint, response):
    owner = tuple(
        item.model_copy(update={"status": "completed", "ended_at": NOW, "payload_json": '"answer"'})
        for item in checkpoint.activations
    )
    output = ActivationRecord(
        activation_id="output",
        key=ActivationKey(run_id="r", scope_key="", iteration=0, node_id="o"),
        status="completed",
        inputs=(),
        messages_json="[]",
        ended_at=NOW,
        payload_json='"answer"',
    )
    return checkpoint.model_copy(
        update={
            "run": checkpoint.run.model_copy(
                update={"status": "completed", "ended_at": NOW, "output_json": '"answer"'}
            ),
            "activations": owner + (output,),
            "responses": checkpoint.responses + (response,),
        }
    )


@pytest.fixture
async def repository(tmp_path):
    store = SQLiteRunRepository(tmp_path / "runs.sqlite")
    await store.initialize()
    await store.create_run(submission(), "r", NOW)
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_cas_snapshot_terminal_and_event_guards(repository):
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    changed = checkpoint.model_copy(
        update={
            "run": checkpoint.run.model_copy(
                update={
                    "status": "running",
                    "started_at": NOW,
                }
            )
        }
    )
    updated = await repository.save_checkpoint(changed, checkpoint.run.state_version)
    assert updated.state_version == checkpoint.run.state_version + 1
    with pytest.raises(CGError):
        await repository.save_checkpoint(changed, checkpoint.run.state_version)
    current = await repository.load_checkpoint("r", "anonymous")
    with pytest.raises(CGError):
        await repository.save_checkpoint(
            current.model_copy(
                update={"run": current.run.model_copy(update={"inputs_json": "{}"})}
            ),
            current.run.state_version,
        )
    cancelled = await repository.terminalize("r", "cancelled", None, NOW)
    failed = await repository.terminalize("r", "failed", None, NOW + timedelta(seconds=1))
    assert cancelled == failed
    with pytest.raises(CGError):
        await repository.save_checkpoint(current, current.run.state_version)
    events = await repository.read_events("r", "anonymous", 0)
    assert [event.event_id for event in events] == list(range(1, len(events) + 1))
    assert events[0].type == "run.queued" and events[-1].type == "run.cancelled"


@pytest.mark.asyncio
async def test_partial_duplicate_race_and_claim_sealing(repository):
    await expose(repository)
    first, duplicate = await asyncio.gather(
        *[repository.accept_results(route(), raw_text_hash("request-a"), NOW) for _ in range(2)]
    )
    assert {first.kind, duplicate.kind} == {"partial", "joined"}
    assert first.claim.claim_id == duplicate.claim.claim_id
    with pytest.raises(CGError):
        await repository.accept_results(route(values=("changed",)), raw_text_hash("changed"), NOW)
    second = await repository.accept_results(
        route(("cg_b",), ("other",)), raw_text_hash("request-b"), NOW
    )
    assert second.kind == "ready"
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    assert [tool.result for tool in checkpoint.pending_tools] == ["result", "other"]
    response = envelope(sequence=2)
    checkpoint = final_checkpoint(checkpoint, response)
    await repository.complete_run(checkpoint, response, checkpoint.run.state_version)
    for acceptance in (first, second):
        claim = await repository.get_claim(acceptance.claim.claim_id)
        assert claim.status == "completed" and claim.envelope == response
    replay = await repository.accept_results(route(), raw_text_hash("request-a"), NOW)
    assert replay.kind == "replay" and replay.claim.envelope == response
    with pytest.raises(CGError):
        await repository.accept_results(route(), raw_text_hash("new-request"), NOW)


@pytest.mark.asyncio
async def test_deadline_does_not_extend_and_late_results_fail(repository):
    batch = await expose(repository)
    await repository.accept_results(route(), raw_text_hash("a"), NOW + timedelta(seconds=9))
    with pytest.raises(CGError) as error:
        await repository.accept_results(
            route(("cg_b",), ("b",)), raw_text_hash("b"), batch.expires_at
        )
    assert error.value.code.value == "tool_wait_timeout"
    assert (await repository.get_run("r", "anonymous")).status == "failed"


@pytest.mark.asyncio
async def test_activation_claim_is_unique_and_stale_attempt_rejected(repository):
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    key = ActivationKey(run_id="r", scope_key="", iteration=0, node_id="i")
    activation = ActivationRecord(
        activation_id="owner", key=key, status="ready", inputs=(), messages_json="[]"
    )
    checkpoint = checkpoint.model_copy(
        update={
            "activations": (activation,),
            "run": checkpoint.run.model_copy(update={"status": "running"}),
        }
    )
    await repository.save_checkpoint(checkpoint, checkpoint.run.state_version)
    claims = await asyncio.gather(
        *[repository.claim_activation(key, attempt, NOW) for attempt in ("a", "b")]
    )
    assert sum(claim is not None for claim in claims) == 1
    current = await repository.load_checkpoint("r", "anonymous")
    stale = current.activations[0].model_copy(update={"status": "completed", "attempt_id": "wrong"})
    with pytest.raises(CGError):
        await repository.save_checkpoint(
            current.model_copy(update={"activations": (stale,)}), current.run.state_version
        )


@pytest.mark.asyncio
async def test_recovery_retains_waits_interrupts_active_and_retention(tmp_path):
    path = tmp_path / "durable.sqlite"
    store = SQLiteRunRepository(path)
    await store.initialize()
    await store.create_run(submission(), "r", NOW)
    await expose(store)
    await store.create_run(submission(), "active", NOW)
    current = await store.load_checkpoint("active", "anonymous")
    await store.save_checkpoint(
        current.model_copy(update={"run": current.run.model_copy(update={"status": "running"})}),
        current.run.state_version,
    )
    await store.close()
    restored = SQLiteRunRepository(path)
    await restored.initialize()
    records = await restored.recover(NOW + timedelta(seconds=1))
    assert [(record.run_id, record.status) for record in records] == [("r", "waiting_tools")]
    assert (await restored.get_run("active", "anonymous")).status == "interrupted"
    assert (await restored.lookup_tools(("cg_a",)))[0].status == "pending"
    assert await restored.cleanup_history(NOW + timedelta(days=1)) == 1
    assert (await restored.get_run("r", "anonymous")).status == "waiting_tools"
    await restored.close()


@pytest.mark.asyncio
async def test_response_and_claim_sealing_rollback_is_atomic(repository, monkeypatch):
    await expose(repository, ids=("cg_a",))
    acceptance = await repository.accept_results(route(), raw_text_hash("claim"), NOW)
    checkpoint = await repository.load_checkpoint("r", "anonymous")
    result = envelope(sequence=2)
    proposed = final_checkpoint(checkpoint, result)
    original = repository._seal_claims

    def fail_after_response_write(*arguments):
        raise RuntimeError("Simulated crash before claim seal")

    monkeypatch.setattr(repository, "_seal_claims", fail_after_response_write)
    with pytest.raises(RuntimeError, match="Simulated crash"):
        await repository.complete_run(proposed, result, checkpoint.run.state_version)
    assert await repository.load_checkpoint("r", "anonymous") == checkpoint
    assert (await repository.get_claim(acceptance.claim.claim_id)).status == "pending"
    monkeypatch.setattr(repository, "_seal_claims", original)
    await repository.complete_run(proposed, result, checkpoint.run.state_version)
    assert (await repository.get_claim(acceptance.claim.claim_id)).envelope == result


@pytest.mark.asyncio
async def test_stale_frontier_cannot_overwrite_concurrently_accepted_result(repository):
    await expose(repository)
    stale = await repository.load_checkpoint("r", "anonymous")
    await repository.accept_results(route(), raw_text_hash("partial"), NOW)
    with pytest.raises(CGError):
        await repository.save_checkpoint(stale, stale.run.state_version)
    current = await repository.load_checkpoint("r", "anonymous")
    assert current.pending_tools[0].result == "result"
    assert current.pending_tools[1].result is None
    assert current.batches[0].expires_at == stale.batches[0].expires_at


@pytest.mark.asyncio
async def test_detachment_and_exposure_share_one_atomic_boundary(repository):
    await expose(repository, ids=("cg_a",))
    assert (await repository.cancel_if_unexposed("r", "anonymous", NOW)).status == "waiting_tools"
    await repository.create_run(submission(), "never-exposed", NOW)
    assert (
        await repository.cancel_if_unexposed("never-exposed", "anonymous", NOW)
    ).status == "cancelled"
    assert (await repository.get_run("r", "anonymous")).status == "waiting_tools"


@pytest.mark.asyncio
async def test_old_completed_claim_cannot_redeliver_after_cancellation(repository):
    await expose(repository, ids=("cg_a",))
    acceptance = await repository.accept_results(route(), raw_text_hash("first"), NOW)
    await expose(repository, ids=("cg_next",), sequence=2)
    assert (await repository.get_claim(acceptance.claim.claim_id)).status == "completed"
    await repository.terminalize("r", "cancelled", None, NOW)
    with pytest.raises(CGError):
        await repository.accept_results(route(), raw_text_hash("first"), NOW)


@pytest.mark.asyncio
async def test_owner_and_global_identity_constraints_rollback(repository):
    await expose(repository)
    current = await repository.load_checkpoint("r", "anonymous")
    await repository.create_run(submission(), "other", NOW)
    other = await repository.load_checkpoint("other", "anonymous")
    stolen = current.activations[0].model_copy(
        update={"key": ActivationKey(run_id="other", scope_key="", iteration=0, node_id="i")}
    )
    with pytest.raises(CGError):
        await repository.save_checkpoint(
            other.model_copy(update={"activations": (stolen,)}), other.run.state_version
        )
    assert await repository.load_checkpoint("other", "anonymous") == other
    assert (await repository.lookup_tools(("cg_a",)))[0].run_id == "r"


@pytest.mark.asyncio
async def test_expiry_transaction_cannot_fail_a_fully_accepted_batch(repository):
    await expose(repository, ids=("cg_a",))
    await repository.accept_results(route(), raw_text_hash("before-expiry"), NOW)
    from app.contracts.errors import ErrorCode

    error = CGError(ErrorCode.TOOL_WAIT_TIMEOUT, "stale expiry").payload().error
    run = await repository.terminalize("r", "failed", error, NOW + timedelta(days=1))
    assert run.status == "waiting_tools" and run.error_json is None
    assert (await repository.load_checkpoint("r", "anonymous")).batches[0].status == "closed"


@pytest.mark.asyncio
async def test_event_subscription_catches_committed_state_and_last_id(repository):
    from app.storage.events import DurableEventBus

    bus = DurableEventBus(repository)
    initial = await bus.read_after("r", "anonymous", 0)
    iterator = bus.subscribe("r", "anonymous", initial[-1].event_id)
    waiter = asyncio.create_task(anext(iterator))
    await asyncio.sleep(0)
    await repository.terminalize("r", "cancelled", None, NOW)
    await bus.notify("r")
    event = await asyncio.wait_for(waiter, 2)
    assert event.type == "run.cancelled" and event.event_id == initial[-1].event_id + 1
    assert (await bus.read_after("r", "anonymous", initial[-1].event_id)) == (event,)
    with pytest.raises(StopAsyncIteration):
        await anext(iterator)
