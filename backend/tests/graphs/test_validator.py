"""Executable graph topology and input contracts, independent of inference."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.errors import CGError
from app.contracts.graph import Graph
from app.contracts.interfaces import GraphSnapshot
from app.graphs.validator import GraphValidator


def make_graph():
    return {
        "schema_version": 1,
        "id": "test",
        "name": "Test",
        "revision": 1,
        "base_model": "USER_INSTALLED_MODEL",
        "inputs": [{"id": "chat", "required": True}],
        "nodes": [
            {"id": "input", "type": "input", "input_id": "chat"},
            {
                "id": "a",
                "type": "llm",
                "system_prompt": "Analyze",
                "tools_enabled": False,
                "generation": {},
            },
            {
                "id": "b",
                "type": "llm",
                "system_prompt": "Critique",
                "tools_enabled": True,
                "generation": {},
            },
            {"id": "output", "type": "output"},
        ],
        "edges": [
            {
                "id": "ia",
                "source": "input",
                "target": "a",
                "target_port": "question",
                "kind": "forward",
            },
            {"id": "ab", "source": "a", "target": "b", "target_port": "draft", "kind": "forward"},
            {
                "id": "bo",
                "source": "b",
                "target": "output",
                "target_port": "answer",
                "kind": "forward",
            },
        ],
        "loops": [],
        "output_node_id": "output",
    }


def loop_graph():
    value = make_graph()
    value["edges"].append(
        {
            "id": "ba",
            "source": "b",
            "target": "a",
            "target_port": "critique",
            "kind": "feedback",
            "loop_id": "refine",
            "initial_value": None,
        }
    )
    value["loops"] = [
        {
            "id": "refine",
            "node_ids": ["a", "b"],
            "controller_node_id": "b",
            "continue_value": "continue",
            "exit_value": "stop",
        }
    ]
    return value


def codes(value):
    return {issue.code for issue in GraphValidator().validate(Graph.model_validate(value)).errors}


def test_compile_lexical_ports_seeded_loop_and_final_identity():
    graph = Graph.model_validate(loop_graph())
    plan = GraphValidator().compile(GraphSnapshot.from_graph(graph))
    assert plan.forward_order == ("input", "a", "b", "output")
    assert plan.final_llm_node_id == "b"
    assert next(p.ordered_ports for p in plan.ports if p.node_id == "a") == ("critique", "question")
    assert plan.loops[0].members == ("a", "b")
    assert plan.loops[0].inbound_edge_ids == ("ia",)
    assert plan.loops[0].feedback_edge_ids == ("ba",)
    assert plan.loops[0].exit_edge_ids == ("bo",)
    graph.name = "Later mutation"
    assert plan.snapshot.graph().name == "Test"


def test_passthrough_graph_requires_no_llm():
    value = make_graph()
    value["nodes"] = [value["nodes"][0], value["nodes"][-1]]
    value["edges"] = [
        {
            "id": "io",
            "source": "input",
            "target": "output",
            "target_port": "answer",
            "kind": "forward",
        }
    ]
    plan = GraphValidator().compile(GraphSnapshot.from_graph(Graph.model_validate(value)))
    assert plan.final_llm_node_id is None


def test_inputs_presence_null_and_unknown_are_distinct():
    value = make_graph()
    value["inputs"].append({"id": "context", "required": False})
    graph = Graph.model_validate(value)
    validator = GraphValidator()
    assert json.loads(validator.prepare_inputs(graph, '{"chat":null}')) == {
        "chat": None,
        "context": None,
    }
    with pytest.raises(CGError) as exc:
        validator.prepare_inputs(graph, "{}")
    assert exc.value.status_code == 400
    with pytest.raises(CGError):
        validator.prepare_inputs(graph, '{"chat":"hello","unknown":1}')
    for invalid in ["[]", '{"chat":NaN}', '{"chat":"one","chat":"two"}']:
        with pytest.raises(CGError):
            validator.prepare_inputs(graph, invalid)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda g: g["edges"][0].update(source="missing"), "unknown_node"),
        (lambda g: g["edges"].append(dict(g["edges"][0], id="duplicate")), "duplicate_port"),
        (
            lambda g: g["edges"].append(
                {
                    "id": "cycle",
                    "source": "b",
                    "target": "a",
                    "target_port": "back",
                    "kind": "forward",
                }
            ),
            "forward_cycle",
        ),
        (
            lambda g: g["nodes"].append(
                {
                    "id": "orphan",
                    "type": "llm",
                    "system_prompt": "",
                    "generation": {},
                    "tools_enabled": False,
                }
            ),
            "unreachable_node",
        ),
        (lambda g: g["nodes"][0].update(input_id="unknown"), "unknown_input"),
        (
            lambda g: g["edges"].append(
                {
                    "id": "out",
                    "source": "output",
                    "target": "a",
                    "target_port": "bad",
                    "kind": "forward",
                }
            ),
            "output_not_terminal",
        ),
    ],
)
def test_invalid_topologies_report_local_identity(mutation, expected):
    value = make_graph()
    mutation(value)
    report = GraphValidator().validate(Graph.model_validate(value))
    assert not report.valid
    assert expected in {issue.code for issue in report.errors}
    assert any(issue.node_id or issue.edge_id for issue in report.errors)
    with pytest.raises(CGError):
        GraphValidator().compile(GraphSnapshot.from_graph(Graph.model_validate(value)))


def test_feedback_seed_absent_rejected_but_present_null_accepted():
    value = loop_graph()
    assert not codes(value)
    del value["edges"][-1]["initial_value"]
    with pytest.raises(ValidationError):
        Graph.model_validate(value)


def test_feedback_from_noncontroller_member_is_legal():
    value = loop_graph()
    value["edges"][-1]["source"] = "a"
    assert not codes(value)


def test_input_member_is_valid_when_immutable_and_controller_remains_final():
    value = loop_graph()
    value["loops"][0]["node_ids"].append("input")
    assert not codes(value)
    value["edges"].append(
        {
            "id": "bad",
            "source": "a",
            "target": "input",
            "target_port": "value",
            "kind": "feedback",
            "loop_id": "refine",
            "initial_value": None,
        }
    )
    assert "input_has_ports" in codes(value)


def test_forward_fan_in_requires_every_provider_and_preserves_lexical_order():
    value = make_graph()
    value["edges"].append(
        {"id": "ib", "source": "input", "target": "b", "target_port": "question", "kind": "forward"}
    )
    plan = GraphValidator().compile(GraphSnapshot.from_graph(Graph.model_validate(value)))
    assert next(p.ordered_ports for p in plan.ports if p.node_id == "b") == ("draft", "question")


def test_undeclared_full_graph_cycle_is_reported():
    value = loop_graph()
    value["loops"] = []
    assert {"unknown_loop", "undeclared_cycle"} <= codes(value)


@pytest.mark.parametrize("target", ["input", "missing"])
def test_invalid_feedback_target_reports_error_without_crashing(target):
    value = loop_graph()
    value["edges"][-1]["target"] = target
    assert codes(value)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda g: g.update(loops=[]), "unknown_loop"),
        (lambda g: g["edges"][-1].update(source="input"), "feedback_scope"),
        (lambda g: g["edges"][2].update(source="a"), "loop_output_bypass"),
        (lambda g: g["loops"][0].update(controller_node_id="a"), "controller_not_terminal"),
    ],
)
def test_invalid_loop_boundaries(mutation, expected):
    value = loop_graph()
    mutation(value)
    assert expected in codes(value)


def test_collapsed_scope_cycle_rejected_even_when_forward_nodes_are_a_dag():
    value = loop_graph()
    value["nodes"].insert(
        3, {"id": "c", "type": "llm", "system_prompt": "", "tools_enabled": False, "generation": {}}
    )
    value["edges"] = [e for e in value["edges"] if e["id"] not in {"ab", "bo"}]
    value["edges"] += [
        {"id": "ac", "source": "a", "target": "c", "target_port": "data", "kind": "forward"},
        {"id": "cb", "source": "c", "target": "b", "target_port": "data", "kind": "forward"},
        {"id": "bo", "source": "b", "target": "output", "target_port": "answer", "kind": "forward"},
    ]
    assert "scope_cycle" in codes(value)


def test_two_disjoint_loops_compile_and_coordinates_do_not_schedule():
    value = loop_graph()
    extra = deepcopy(loop_graph())
    for node in extra["nodes"][1:3]:
        node["id"] += "2"
        value["nodes"].insert(-1, node)
    value["nodes"].insert(
        -1,
        {
            "id": "join",
            "type": "llm",
            "system_prompt": "Synthesize",
            "tools_enabled": False,
            "generation": {},
        },
    )
    value["edges"][2].update(target="join", target_port="first")
    value["edges"] += [
        {
            "id": "ia2",
            "source": "input",
            "target": "a2",
            "target_port": "question",
            "kind": "forward",
        },
        {"id": "a2b2", "source": "a2", "target": "b2", "target_port": "draft", "kind": "forward"},
        {
            "id": "b2a2",
            "source": "b2",
            "target": "a2",
            "target_port": "critique",
            "kind": "feedback",
            "loop_id": "refine2",
            "initial_value": "seed",
        },
        {
            "id": "b2join",
            "source": "b2",
            "target": "join",
            "target_port": "second",
            "kind": "forward",
        },
        {
            "id": "jo",
            "source": "join",
            "target": "output",
            "target_port": "answer",
            "kind": "forward",
        },
    ]
    value["loops"].append(
        {
            "id": "refine2",
            "node_ids": ["a2", "b2"],
            "controller_node_id": "b2",
            "continue_value": "again",
            "exit_value": "done",
        }
    )
    validator = GraphValidator()
    plan = validator.compile(GraphSnapshot.from_graph(Graph.model_validate(value)))
    for node in value["nodes"]:
        node["position"] = {"x": -500.0, "y": 10000.0}
    moved = validator.compile(GraphSnapshot.from_graph(Graph.model_validate(value)))
    assert plan.forward_order == moved.forward_order
    assert len(plan.loops) == 2
    assert plan.final_llm_node_id == "join"


def test_examples_are_valid_executable_graphs():
    examples = Path(__file__).resolve().parents[3] / "examples"
    for name in ("synthesis", "feedback", "multiple-inputs"):
        graph = Graph.model_validate_json((examples / f"{name}.json").read_text())
        assert graph.base_model == "USER_INSTALLED_MODEL"
        assert GraphValidator().validate(graph).valid
