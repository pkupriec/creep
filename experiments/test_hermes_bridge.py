"""RD1 regression cases. Actual Hermes tests are separately opt-in."""

import copy
import os

import pytest

from hermes_bridge import BridgeError, ResearchBridge, latest_segment, run_hermes


def request():
    return {"model": "cg/research", "messages": [{"role": "user", "content": "same"}]}


def continuation(initial, response, content="fixture-token"):
    value = copy.deepcopy(initial)
    value["messages"].append(response["choices"][0]["message"])
    value["messages"].extend(
        {"role": "tool", "tool_call_id": c["id"], "content": content}
        for c in response["choices"][0]["message"]["tool_calls"]
    )
    return value


def test_checkpoint_before_delivery_restart_and_owner_routing(tmp_path):
    path = tmp_path / "checkpoint.sqlite"
    bridge = ResearchBridge(path, tmp_path / "fixture.txt", owners=2)
    start = request()
    response = bridge.handle(start)
    calls = response["choices"][0]["message"]["tool_calls"]
    assert len({c["id"] for c in calls}) == 2
    mappings = bridge.mappings()
    assert {m["internal_id"] for m in mappings} == {"collision"}
    assert {m["owner"] for m in mappings} == {"a", "b"}
    bridge.close()
    restored = ResearchBridge(path, tmp_path / "fixture.txt", owners=2)
    completed = restored.handle(continuation(start, response))
    assert completed["choices"][0]["finish_reason"] == "stop"
    assert (
        completed["choices"][0]["message"]["content"]
        == "a:fixture-token | b:fixture-token"
    )
    assert all(len(n["results"]) == 1 for n in restored.state()["nodes"].values())
    assert restored.state()["status"] == "completed"


def test_replay_does_not_execute_again_and_changed_result_conflicts(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture")
    start = request()
    response = bridge.handle(start)
    resumed = continuation(start, response)
    final = bridge.handle(resumed)
    count = bridge.model_calls
    assert bridge.handle(resumed) == final
    assert bridge.model_calls == count
    resumed["messages"][-1]["content"] = "different"
    with pytest.raises(BridgeError, match="changed_result"):
        bridge.handle(resumed)


def test_identical_questions_have_distinct_run_and_tool_ids(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture")
    a, b = bridge.handle(request()), bridge.handle(request())
    assert (
        a["choices"][0]["message"]["tool_calls"][0]["id"]
        != b["choices"][0]["message"]["tool_calls"][0]["id"]
    )
    assert len({m["run_id"] for m in bridge.mappings()}) == 2


@pytest.mark.parametrize(
    "change,code",
    [
        ("unknown", "unknown_tool_id"),
        ("model", "namespace_model_mismatch"),
        ("namespace", "namespace_model_mismatch"),
        ("new_user", "mixed_new_turn"),
    ],
)
def test_invalid_continuations(tmp_path, change, code):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture")
    initial = request()
    resumed = continuation(initial, bridge.handle(initial))
    namespace = "anonymous"
    if change == "unknown":
        resumed["messages"][-1]["tool_call_id"] = "cg_unknown"
    elif change == "model":
        resumed["model"] = "cg/another"
    elif change == "namespace":
        namespace = "another"
    else:
        resumed["messages"].append({"role": "user", "content": "new turn"})
    with pytest.raises(BridgeError, match=code):
        bridge.handle(resumed, namespace=namespace)


def test_partial_batch_waits_and_never_reissues_delivered_calls(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture", owners=2)
    initial = request()
    resumed = continuation(initial, bridge.handle(initial))
    second = resumed["messages"].pop()
    partial = bridge.handle(resumed)
    assert partial["research_status"] == "waiting_tools"
    assert "tool_calls" not in partial["choices"][0]["message"]
    resumed["messages"].append(second)
    assert bridge.handle(resumed)["choices"][0]["finish_reason"] == "stop"


def test_parallel_false_serializes_owners(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture", owners=2)
    initial = request()
    initial["parallel_tool_calls"] = False
    first = bridge.handle(initial)
    assert len(first["choices"][0]["message"]["tool_calls"]) == 1
    resumed = continuation(initial, first)
    second = bridge.handle(resumed)
    assert len(second["choices"][0]["message"]["tool_calls"]) == 1
    assert (
        bridge.handle(continuation(resumed, second))["choices"][0]["finish_reason"]
        == "stop"
    )


def test_latest_segment_ignores_closed_historical_ids(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture")
    initial = request()
    old = continuation(initial, bridge.handle(initial))
    final = bridge.handle(old)
    old["messages"].append(final["choices"][0]["message"])
    old["messages"].append({"role": "user", "content": "same"})
    assert latest_segment(old["messages"]) == ([], False)
    assert bridge.handle(old)["choices"][0]["finish_reason"] == "tool_calls"


def test_cross_run_results_are_ambiguous(tmp_path):
    bridge = ResearchBridge(tmp_path / "db", tmp_path / "fixture")
    initial = request()
    a, b = bridge.handle(initial), bridge.handle(initial)
    resumed = continuation(initial, a)
    resumed["messages"].append(continuation(initial, b)["messages"][-1])
    with pytest.raises(BridgeError, match="ambiguous_runs"):
        bridge.handle(resumed)


def test_uncertain_active_execution_is_interrupted_after_restart(tmp_path):
    path = tmp_path / "db"
    bridge = ResearchBridge(path, tmp_path / "fixture")
    initial = request()
    response = bridge.handle(initial)
    state = bridge.state()
    state["status"] = "running"
    bridge.save(state)
    bridge.close()
    restored = ResearchBridge(path, tmp_path / "fixture")
    assert restored.state()["status"] == "interrupted"
    with pytest.raises(BridgeError, match="interrupted"):
        restored.handle(continuation(initial, response))
    assert restored.model_calls == 0


@pytest.mark.skipif(
    os.getenv("CG_RD1_HERMES") != "1",
    reason="Run real Hermes via documented isolated harness",
)
@pytest.mark.parametrize(
    "owners,stream,serial",
    [(1, False, False), (1, True, False), (2, True, False), (2, True, True)],
)
def test_actual_hermes_client(tmp_path, owners, stream, serial):
    result = run_hermes(tmp_path, owners=owners, stream=stream, serial_tools=serial)
    assert result["completed"]
    assert "fixture-token" in result["final_response"]
    assert result["tool_results"] == owners
    if serial:
        assert result["api_calls"] == 3
