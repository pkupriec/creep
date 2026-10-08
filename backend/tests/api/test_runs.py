import asyncio
import json

import httpx
import pytest
from test_chat import CALL, TOOLS, chat, completion, continuation, graph, harness, publish

from app.runtime.clock import SystemClock


class DeadlineClock(SystemClock):
    """Move UTC only after a recorded wait; wake timers at that same boundary."""

    def __init__(self, tool_wait_seconds=1800):
        self.instant = super().now()
        self.tool_wait_seconds = tool_wait_seconds
        self.claim_waiting = asyncio.Event()
        self.runtime_waiting = asyncio.Event()
        self.deadline_crossed = asyncio.Event()

    def now(self):
        return self.instant

    async def sleep(self, seconds):
        if seconds == 0.05:
            self.claim_waiting.set()
            await self.deadline_crossed.wait()
        elif seconds == self.tool_wait_seconds:
            self.runtime_waiting.set()
            await self.deadline_crossed.wait()
        else:
            await asyncio.sleep(seconds)

    def advance_to(self, deadline):
        self.instant = deadline
        self.deadline_crossed.set()


async def finished(client, run_id, status="completed"):
    async with asyncio.timeout(3):
        while True:
            detail = (await client.get(f"/api/runs/{run_id}")).json()
            if detail["run"]["status"] == status and (
                status != "waiting_tools" or detail["pending_tools"]
            ):
                return detail
            await asyncio.sleep(0.01)


async def test_ui_start_history_snapshot_optional_input_and_committed_event_replay(tmp_path):
    async with harness(tmp_path) as (_, client, _):
        value = graph(
            inputs=[{"id": "chat", "required": True}, {"id": "optional", "required": False}]
        )
        await client.post("/api/graphs", json=value)
        response = await client.post(
            "/api/runs", json={"graph_id": "g", "revision": 1, "inputs": {"chat": "named"}}
        )
        assert response.status_code == 202
        id_ = response.json()["run_id"]
        detail = await finished(client, id_)
        assert detail["snapshot"]["revision"] == 1 and detail["output"] == "final"
        assert detail["activations"][-1]["expected_ports"] == ["answer"]
        history = (
            await client.get("/api/runs?graph_id=g&status=completed&limit=1&offset=0")
        ).json()
        assert (
            history["total"] == 1
            and history["runs"][0]["graph_hash"] == detail["run"]["graph_hash"]
        )
        stream = await client.get(f"/api/runs/{id_}/events")
        ids = [int(line[4:]) for line in stream.text.splitlines() if line.startswith("id: ")]
        assert ids == sorted(set(ids)) and "event: run.completed" in stream.text
        replay = await client.get(
            f"/api/runs/{id_}/events", headers={"Last-Event-ID": str(ids[-2])}
        )
        assert [
            int(line[4:]) for line in replay.text.splitlines() if line.startswith("id: ")
        ] == ids[-1:]
        assert not (
            await client.get(f"/api/runs/{id_}/events", headers={"Last-Event-ID": str(ids[-1])})
        ).content


@pytest.mark.parametrize(
    "query", ["limit=0", "offset=-1", "status=bogus", "limit=1&limit=2", "extra=1"]
)
async def test_invalid_history_filter_standard_400(tmp_path, query):
    async with harness(tmp_path) as (_, client, _):
        response = await client.get("/api/runs?" + query)
        assert (
            response.status_code == 400 and response.json()["error"]["code"] == "invalid_parameter"
        )


async def test_ui_manual_results_resume_exact_owner_and_late_results_rejected(tmp_path):
    async def handle(body):
        result = next((m for m in body["messages"] if m["role"] == "tool"), None)
        return httpx.Response(
            200,
            json=completion(
                "manual accepted" if result else None, calls=None if result else [CALL]
            ),
        )

    async with harness(tmp_path, handle) as (_, client, calls):
        await client.post("/api/graphs", json=graph(tools=True))
        response = await client.post(
            "/api/runs",
            json={"graph_id": "g", "revision": 1, "inputs": {"chat": "x"}, "tools": TOOLS},
        )
        id_ = response.json()["run_id"]
        detail = await finished(client, id_, "waiting_tools")
        tool_id = detail["pending_tools"][0]["tool_call_id"]
        result = {"results": [{"tool_call_id": tool_id, "content": "manual content"}]}
        accepted = await client.post(f"/api/runs/{id_}/tool-results", json=result)
        assert accepted.status_code == 200 and accepted.json()["accepted_ids"] == [tool_id]
        assert (await finished(client, id_))["output"] == "manual accepted"
        replay = await client.post(f"/api/runs/{id_}/tool-results", json=result)
        assert replay.status_code == 200 and len(calls) == 2
        result["results"][0]["content"] = "changed"
        assert (await client.post(f"/api/runs/{id_}/tool-results", json=result)).status_code == 409


async def test_idempotent_cancel_rejects_pending_continuation_and_bad_event_cursor(tmp_path):
    async def handle(_):
        return httpx.Response(200, json=completion(None, calls=[CALL]))

    async with harness(tmp_path, handle) as (_, client, calls):
        await publish(client, graph(tools=True))
        first = await client.post("/v1/chat/completions", json=chat(tools=TOOLS))
        id_ = first.headers["x-cg-run-id"]
        for _ in range(2):
            response = await client.post(f"/api/runs/{id_}/cancel")
            assert response.json()["status"] == "cancelled"
        late = await client.post(
            "/v1/chat/completions", json=continuation(chat(tools=TOOLS), first.json())
        )
        assert late.status_code == 409 and len(calls) == 1
        assert (
            await client.get(f"/api/runs/{id_}/events", headers={"Last-Event-ID": "-1"})
        ).status_code == 400


async def test_ui_invalid_context_and_missing_input_have_zero_effects(tmp_path):
    async with harness(tmp_path) as (_, client, calls):
        await client.post("/api/graphs", json=graph())
        for extra in [{"inputs": {}}, {"inputs": {"chat": "x"}, "tools": TOOLS + TOOLS}]:
            response = await client.post(
                "/api/runs", json={"graph_id": "g", "revision": 1, **extra}
            )
            assert response.status_code == 400 and not calls
        assert (await client.get("/api/runs")).json()["total"] == 0


@pytest.mark.parametrize("expire", [False, True])
async def test_full_batch_partial_http_wait_fixed_deadline_and_exact_replay(tmp_path, expire):
    """Exercise full-batch contract even though unknown effects normally serialize."""
    from datetime import timedelta

    from app.api.runs import submission
    from app.contracts.api import ChatCompletionRequest, ChatCompletionResponse
    from app.contracts.interfaces import (
        ActivationKey,
        ActivationRecord,
        PortValue,
        ResponseEnvelope,
        ToolBatch,
        ToolCheckpoint,
        canonical_json,
    )

    async def handle(body):
        results = [m for m in body["messages"] if m["role"] == "tool"]
        assert [(m["tool_call_id"], m["content"]) for m in results] == [
            ("internal", "one"),
            ("internal-two", "two"),
        ]
        return httpx.Response(200, json=completion("full owner done"))

    clock = DeadlineClock(tool_wait_seconds=10) if expire else None
    async with harness(tmp_path, handle, clock=clock) as (app, client, calls):
        value = graph(tools=True)
        await client.post("/api/graphs", json=value)
        snapshot = await app.state.graphs.load_snapshot("g", 1)
        context = ChatCompletionRequest.model_validate(chat(tools=TOOLS))
        submitted = submission(
            app.state.settings,
            app.state.validator,
            snapshot,
            "anonymous",
            {"chat": "question"},
            context,
        )
        store, bridge, clock = app.state.repository, app.state.bridge, app.state.clock
        await store.create_run(submitted, "partial", clock.now())
        cp = await store.load_checkpoint("partial", "anonymous")
        wire = ChatCompletionResponse.model_validate(
            completion(None, calls=[CALL, {**CALL, "id": "internal-two"}])
        )
        key = ActivationKey(run_id="partial", scope_key="", iteration=0, node_id="think")
        activation = ActivationRecord(
            activation_id="owner",
            key=ActivationKey(run_id="partial", scope_key="", iteration=0, node_id="think"),
            status="waiting_tools",
            inputs=(
                PortValue(
                    target=key,
                    target_port="question",
                    source_node_id="i",
                    source_iteration=0,
                    value_json='"question"',
                ),
            ),
            messages_json=canonical_json(
                [wire.choices[0].message.model_dump(mode="json", exclude_none=True)]
            ),
        )
        input_activation = ActivationRecord(
            activation_id="input",
            key=ActivationKey(run_id="partial", scope_key="", iteration=0, node_id="i"),
            status="completed",
            inputs=(),
            messages_json="[]",
            payload_json='"question"',
        )
        output_activation = ActivationRecord(
            activation_id="output",
            key=ActivationKey(run_id="partial", scope_key="", iteration=0, node_id="o"),
            status="pending",
            inputs=(),
            messages_json="[]",
        )
        mapped = bridge.map_calls(activation, wire)
        cp = cp.model_copy(
            update={
                "run": cp.run.model_copy(update={"status": "waiting_tools"}),
                "activations": (
                    input_activation,
                    activation.model_copy(update={"provider_round": 1}),
                    output_activation,
                ),
                "pending_tools": mapped,
            }
        )
        await store.save_checkpoint(cp, cp.run.state_version)
        cp = await store.load_checkpoint("partial", "anonymous")
        external = wire.model_dump(mode="json")
        for call, mapping in zip(
            external["choices"][0]["message"]["tool_calls"], mapped, strict=True
        ):
            call["id"] = mapping.external_id
        external["model"] = "cg/g"
        envelope = ResponseEnvelope(
            run_id="partial",
            batch_id="batch",
            response_sequence=1,
            completion_json=canonical_json(external),
        )
        now = clock.now()
        batch = ToolBatch(
            batch_id="batch",
            run_id="partial",
            sequence=1,
            status="open",
            external_ids=tuple(m.external_id for m in mapped),
            prepared_at=now,
            expires_at=now + timedelta(seconds=10),
            envelope=envelope,
        )
        cp = cp.model_copy(
            update={
                "pending_tools": tuple(
                    m.model_copy(update={"batch_id": "batch", "status": "pending"}) for m in mapped
                ),
                "batches": (batch,),
                "responses": (envelope,),
            }
        )
        await store.checkpoint_batch(
            ToolCheckpoint(checkpoint=cp, batch=batch), cp.run.state_version
        )
        await app.state.runtime.recover()
        partial = {
            **chat(tools=TOOLS),
            "messages": [
                external["choices"][0]["message"],
                {"role": "tool", "tool_call_id": mapped[0].external_id, "content": "one"},
            ],
        }
        waiter = asyncio.create_task(client.post("/v1/chat/completions", json=partial))
        try:
            async with asyncio.timeout(2):
                while True:
                    cp = await store.load_checkpoint("partial", "anonymous")
                    if cp.pending_tools[0].status == "accepted":
                        break
                    await asyncio.sleep(0.01)
            assert not waiter.done() and not calls and cp.batches[0].expires_at == batch.expires_at
            if expire:
                await asyncio.wait_for(clock.claim_waiting.wait(), 2)
                await asyncio.wait_for(clock.runtime_waiting.wait(), 2)
                assert cp.run.status == "waiting_tools" and cp.batches[0].status == "open"
                assert cp.pending_tools[0].result == "one" and cp.pending_tools[1].result is None
                clock.advance_to(batch.expires_at)
                timed_out = await asyncio.wait_for(waiter, 3)
                assert timed_out.status_code == 504
                assert timed_out.json()["error"]["code"] == "tool_wait_timeout"
                failed = await store.load_checkpoint("partial", "anonymous")
                assert failed.run.status == "failed"
                assert json.loads(failed.run.error_json)["code"] == "tool_wait_timeout"
                assert failed.batches[0].expires_at == batch.expires_at
                assert failed.batches[0].status == "terminal"
                assert failed.responses == (envelope,) and failed.run.output_json is None
                assert failed.run.upstream_attempts == cp.run.upstream_attempts and not calls
                late = await client.post("/v1/chat/completions", json=partial)
                assert late.status_code == 409 and late.json()["error"]["code"] == "run_terminal"
                assert (await store.load_checkpoint("partial", "anonymous")) == failed
                assert not calls
                return
            wrong = {"results": [{"tool_call_id": mapped[0].external_id, "content": "changed"}]}
            assert (
                await client.post("/api/runs/partial/tool-results", json=wrong)
            ).status_code == 409
            accepted = await client.post(
                "/api/runs/partial/tool-results",
                json={"results": [{"tool_call_id": mapped[1].external_id, "content": "two"}]},
            )
            assert accepted.json()["missing_ids"] == []
            final = await asyncio.wait_for(waiter, 3)
            assert final.status_code == 200, final.text
            assert (
                final.status_code == 200
                and final.json()["choices"][0]["message"]["content"] == "full owner done"
            )
            replay = await client.post("/v1/chat/completions", json=partial)
            assert replay.json() == final.json() and len(calls) == 1
            assert (await store.load_checkpoint("partial", "anonymous")).batches[
                0
            ].expires_at == batch.expires_at
        finally:
            if not waiter.done():
                waiter.cancel()
                await asyncio.gather(waiter, return_exceptions=True)


async def test_new_late_submission_after_saved_timeout_returns_409_without_inference(tmp_path):
    clock = DeadlineClock()

    async def handle(_):
        return httpx.Response(200, json=completion(None, calls=[CALL]))

    async with harness(tmp_path, handle, clock=clock) as (app, client, calls):
        await publish(client, graph(tools=True))
        initial = chat(tools=TOOLS)
        first = await client.post("/v1/chat/completions", json=initial)
        run_id = first.headers["x-cg-run-id"]
        before = await app.state.repository.load_checkpoint(run_id, "anonymous")
        assert before.run.status == "waiting_tools" and before.batches[0].status == "open"
        await asyncio.wait_for(clock.runtime_waiting.wait(), 2)
        clock.advance_to(before.batches[0].expires_at)
        await finished(client, run_id, "failed")
        failed = await app.state.repository.load_checkpoint(run_id, "anonymous")
        assert json.loads(failed.run.error_json)["code"] == "tool_wait_timeout"
        assert failed.batches[0].expires_at == before.batches[0].expires_at
        assert failed.responses == before.responses and failed.run.output_json is None
        late = await client.post("/v1/chat/completions", json=continuation(initial, first.json()))
        assert late.status_code == 409 and late.json()["error"]["code"] == "run_terminal"
        assert len(calls) == 1
        assert (await app.state.repository.load_checkpoint(run_id, "anonymous")) == failed


async def test_history_offset_beyond_sqlite_integer_range_is_empty_page(tmp_path):
    async with harness(tmp_path) as (_, client, _):
        offset = 2**64
        response = await client.get(f"/api/runs?offset={offset}")
        assert response.status_code == 200
        assert response.json() == {"runs": [], "total": 0, "limit": 20, "offset": offset}
