"""G1 schemas are executable contracts, not scheduler acceptance evidence."""

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.contracts.api import (
    AssistantMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ToolResultsRequest,
)
from app.contracts.config import Settings
from app.contracts.errors import ERROR_STATUS, CGError, ErrorCode
from app.contracts.graph import Graph, Loop, controller_schema
from app.contracts.interfaces import (
    ActivationKey,
    ActivationRecord,
    CompiledGraph,
    GraphSnapshot,
    PendingTool,
    ProviderRequest,
    ResponseEnvelope,
    RunCheckpoint,
    RunContext,
    RunPolicy,
    RunRecord,
    ToolBatch,
    ToolCheckpoint,
    canonical_arguments_hash,
    canonical_hash,
    raw_text_hash,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def dev_wrapper():
    spec = importlib.util.spec_from_file_location("cg_dev_wrapper", ROOT / "scripts/dev.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_windows_smoke_wrapper_paths_environment_and_arguments(dev_wrapper, monkeypatch, capsys):
    calls = []
    original = {
        "CG_API_TOKEN": "fixture-private-value",
        "CG_SMOKE_MODEL": "installed:tag",
        "COMPOSE_FILE": "D:/Sources/creep/compose.yaml;D:/Sources/creep/override.yaml",
        "WSLENV": "EXISTING/u",
        "UNRELATED_SECRET": "not-forwarded",
    }
    monkeypatch.setattr(dev_wrapper, "os", SimpleNamespace(name="nt", environ=original))

    def run(command, **kwargs):
        calls.append((command, kwargs))
        if "wslpath" in command:
            assert "\\" not in command[-1]
            return SimpleNamespace(returncode=0, stdout="/mnt/d/" + command[-1].split("/")[-1])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(dev_wrapper.subprocess, "run", run)
    dev_wrapper.smoke_compose_windows("wsl.exe", ["--validate", "--file", "D:/custom.yaml"])
    command, kwargs = calls[-1]
    assert command[-3:] == ["--validate", "--file", "/mnt/d/custom.yaml"]
    assert calls[0][0][-1] == dev_wrapper.ROOT.as_posix()
    assert kwargs["env"]["COMPOSE_FILE"] == "/mnt/d/compose.yaml:/mnt/d/override.yaml"
    names = kwargs["env"]["WSLENV"].split(":")
    assert "CG_API_TOKEN/u" in names and "CG_SMOKE_MODEL/u" in names
    assert "UNRELATED_SECRET/u" not in names and "EXISTING/u" in names
    assert original["WSLENV"] == "EXISTING/u"
    assert "fixture-private-value" not in capsys.readouterr().out


@pytest.mark.parametrize("code,stdout,expected", [(37, "", 37), (0, "", 2)])
def test_windows_smoke_conversion_failure_is_controlled(
    dev_wrapper, monkeypatch, capsys, code, stdout, expected
):
    monkeypatch.setattr(
        dev_wrapper.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=code, stdout=stdout),
    )
    with pytest.raises(SystemExit) as error:
        dev_wrapper.smoke_compose_windows("wsl.exe", ["--validate"])
    assert error.value.code == expected
    output = capsys.readouterr()
    assert "WSL path conversion failed" in output.err
    assert "Traceback" not in output.err


def test_windows_smoke_helper_failure_propagates(dev_wrapper, monkeypatch):
    def run(command, **_kwargs):
        return SimpleNamespace(
            returncode=0 if "wslpath" in command else 23, stdout="/mnt/d/Sources/creep"
        )

    monkeypatch.setattr(dev_wrapper.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        dev_wrapper.smoke_compose_windows("wsl.exe", ["--validate"])
    assert error.value.code == 23


def test_smoke_cli_passthrough_preserves_hermes_options(dev_wrapper, monkeypatch):
    calls = []
    options = ["--model", "installed:tag", "--hermes-root", "D:/Hermes Root"]
    monkeypatch.setattr(sys, "argv", ["dev.py", "smoke-hermes", *options])
    monkeypatch.setattr(dev_wrapper, "backend", lambda *args: calls.append(args))
    dev_wrapper.main()
    assert calls == [("python", "scripts/smoke_hermes.py", *options)]


def test_non_smoke_targets_reject_extra_options(dev_wrapper, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["dev.py", "test-contract", "--unknown"])
    with pytest.raises(SystemExit) as error:
        dev_wrapper.main()
    assert error.value.code == 2


def authoritative_trace():
    return json.loads((ROOT / "experiments/hermes-traces.json").read_text(encoding="utf-8"))[
        "authoritative_final_experiment"
    ]


def actual_client_requests():
    requests = [
        item["client_request"]
        for item in authoritative_trace()["client_trace"]
        if "client_request" in item
    ]
    assert len(requests) == 3
    return requests


def actual_upstream_responses():
    responses = [
        json.loads(item["upstream_response_body_utf8"])
        for item in authoritative_trace()["upstream_trace"]
        if "upstream_response_body_utf8" in item
    ]
    assert len(responses) == 5
    return responses


@pytest.mark.parametrize(
    "client_request", actual_client_requests(), ids=["initial", "first-tool", "second-tool"]
)
def test_actual_hermes_requests_preserve_every_history_and_tool_field(client_request):
    original = deepcopy(client_request)
    parsed = ChatCompletionRequest.model_validate(client_request)
    assert parsed.model_dump(mode="json", by_alias=True, exclude_unset=True) == original
    assert client_request == original
    schema = json.loads((ROOT / "frontend/src/contracts/schema.json").read_text())
    Draft202012Validator({**schema, "$ref": "#/$defs/ChatCompletionRequest"}).validate(original)


@pytest.mark.parametrize(
    "response", actual_upstream_responses(), ids=[f"wire-{i}" for i in range(5)]
)
def test_actual_upstream_responses_normalize_only_known_metadata(response):
    original = deepcopy(response)
    parsed = ChatCompletionResponse.from_upstream(response)
    expected = deepcopy(original)
    expected.pop("system_fingerprint")
    expected["usage"].pop("prompt_tokens_details")
    for choice in expected["choices"]:
        for call in choice["message"].get("tool_calls", []):
            call.pop("index")
    assert parsed.model_dump(mode="json", exclude_unset=True) == expected
    assert response == original


@pytest.mark.parametrize("with_tools", [False, True], ids=["text", "native-tool"])
@pytest.mark.parametrize("reasoning", ["absent", "synthetic-provider-metadata", None])
def test_upstream_reasoning_metadata_is_private_and_preserves_semantics(with_tools, reasoning):
    response = deepcopy(actual_upstream_responses()[0])
    message = response["choices"][0]["message"]
    if not with_tools:
        message.pop("tool_calls", None)
        message["content"] = "READY"
        response["choices"][0]["finish_reason"] = "stop"
    expected = ChatCompletionResponse.from_upstream(response).model_dump(
        mode="json", exclude_unset=True
    )
    if reasoning != "absent":
        message["reasoning"] = reasoning
    if not with_tools and isinstance(reasoning, str) and reasoning != "absent":
        assert set(message) == {"content", "reasoning", "role"}
    original = deepcopy(response)
    parsed = ChatCompletionResponse.from_upstream(response)
    assert parsed.model_dump(mode="json", exclude_unset=True) == expected
    assert "reasoning" not in parsed.choices[0].message.model_dump()
    assert response == original


@pytest.mark.parametrize("reasoning", [{}, [], True, 1])
def test_upstream_reasoning_metadata_requires_strict_string_or_null(reasoning):
    response = deepcopy(actual_upstream_responses()[0])
    response["choices"][0]["message"]["reasoning"] = reasoning
    with pytest.raises(ValidationError):
        ChatCompletionResponse.from_upstream(response)


@pytest.mark.parametrize("reasoning", ["synthetic-provider-metadata", None])
def test_public_assistant_and_client_request_reject_reasoning_extension(reasoning):
    message = {"role": "assistant", "content": "READY", "reasoning": reasoning}
    with pytest.raises(ValidationError):
        AssistantMessage.model_validate(message)
    request = {"model": "ollama/gemma4:12b", "messages": [message]}
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(request)


@pytest.mark.parametrize(
    "path,value",
    [
        (("reasoning_effort",), "none"),
        (("choices", 0, "message", "reasoning_content"), "private"),
        (("choices", 0, "finish_reason"), "unknown"),
        (("choices", 0, "message", "tool_calls", 0, "function", "arguments"), {}),
        (("choices", 0, "message", "tool_calls", 0, "id"), ""),
        (("choices", 0, "message", "tool_calls", 0, "index"), 1),
        (("choices", 0, "message", "tool_calls", 0, "index"), "0"),
        (("system_fingerprint",), 1),
        (("usage", "prompt_tokens_details", "cached_tokens"), -1),
        (("usage", "prompt_tokens_details", "cached_tokens"), True),
        (("usage", "prompt_tokens_details", "unknown_counter"), 3),
        (("usage", "prompt_tokens"), "2109"),
        (("usage", "unknown_semantics"), True),
    ],
)
def test_upstream_boundary_rejects_unknown_or_malformed_semantics_and_metadata(path, value):
    response = deepcopy(actual_upstream_responses()[0])
    target = response
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises((ValidationError, ValueError)):
        ChatCompletionResponse.from_upstream(response)


def test_tool_message_name_keeps_client_profile_strict():
    request = deepcopy(actual_client_requests()[1])
    tool_message = next(message for message in request["messages"] if message["role"] == "tool")
    assert tool_message["name"] == "read_file"
    tool_message["unexpected_semantics"] = True
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(request)


def graph_dict():
    return {
        "schema_version": 1,
        "id": "synthesis",
        "name": "Synthesis",
        "revision": 1,
        "base_model": "installed:tag",
        "inputs": [{"id": "chat", "required": True}],
        "nodes": [
            {"id": "i", "type": "input", "input_id": "chat"},
            {
                "id": "a",
                "type": "llm",
                "system_prompt": "Synthesize.",
                "tools_enabled": True,
                "generation": {"temperature": 0.2},
            },
            {"id": "o", "type": "output"},
        ],
        "edges": [
            {
                "id": "ia",
                "source": "i",
                "target": "a",
                "target_port": "question",
                "kind": "forward",
            },
            {"id": "ao", "source": "a", "target": "o", "target_port": "answer", "kind": "forward"},
        ],
        "loops": [],
        "output_node_id": "o",
    }


def request_dict():
    return {
        "model": "cg/synthesis",
        "messages": [
            {"role": "system", "content": "Preserve this constraint."},
            {"role": "user", "content": [{"type": "text", "text": "Question"}]},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "cg_123",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{ "path": "x", "unicode": "é" }',
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "cg_123", "content": "exact\nresult"},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "additionalProperties": False,
                    },
                },
            }
        ],
    }


def test_graph_and_messages_round_trip_without_argument_rewrite():
    graph = Graph.model_validate(graph_dict())
    assert Graph.model_validate_json(graph.model_dump_json()) == graph
    source = request_dict()
    request = ChatCompletionRequest.model_validate(source)
    assert (
        request.messages[2].tool_calls[0].function.arguments
        == source["messages"][2]["tool_calls"][0]["function"]["arguments"]
    )
    assert request.model_dump(mode="json", exclude_unset=True) == source


@pytest.mark.parametrize("bad_id", ["../outside", "a/b", "..", "a\\b", "", " x", "x" * 65])
def test_graph_ids_are_allowlisted(bad_id):
    data = graph_dict()
    data["id"] = bad_id
    with pytest.raises(ValidationError):
        Graph.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [("schema_version", 2), ("revision", 0), ("revision", "1"), ("unknown", "semantic")],
)
def test_graph_rejects_version_coercion_and_extras(field, value):
    data = graph_dict()
    data[field] = value
    with pytest.raises(ValidationError):
        Graph.model_validate(data)


def test_feedback_seed_is_required_but_explicit_null_is_valid():
    data = graph_dict()
    data["loops"] = [
        {
            "id": "refine",
            "node_ids": ["a"],
            "controller_node_id": "a",
            "continue_value": "again",
            "exit_value": "done",
        }
    ]
    edge = {
        "id": "aa",
        "source": "a",
        "target": "a",
        "target_port": "previous",
        "kind": "feedback",
        "loop_id": "refine",
    }
    data["edges"].append(edge)
    with pytest.raises(ValidationError):
        Graph.model_validate(data)
    edge["initial_value"] = None
    assert Graph.model_validate(data).edges[-1].initial_value is None


def test_loop_values_are_distinct_and_members_disjoint():
    data = graph_dict()
    loop = {
        "id": "refine",
        "node_ids": ["a"],
        "controller_node_id": "a",
        "continue_value": "again",
        "exit_value": "again",
    }
    data["loops"] = [loop]
    with pytest.raises(ValidationError):
        Graph.model_validate(data)
    loop["exit_value"] = "done"
    data["loops"].append({**loop, "id": "other"})
    with pytest.raises(ValidationError):
        Graph.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("n", 2),
        ("reasoning_effort", "none"),
        ("seed", 12),
        ("temperature", -1),
        ("top_p", 2),
        ("max_tokens", 0),
    ],
)
def test_client_rejects_unsupported_semantics(field, value):
    data = request_dict()
    data[field] = value
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(data)


def test_text_function_and_streaming_profile():
    data = request_dict()
    data.update(
        stream=True,
        stream_options={"include_usage": True},
        n=1,
        tool_choice={"type": "function", "function": {"name": "read_file"}},
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": {"type": "object"}, "strict": True},
        },
    )
    assert ChatCompletionRequest.model_validate(data).n == 1
    data["messages"][1]["content"] = [{"type": "image_url", "image_url": {"url": "x"}}]
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(data)


def test_partial_results_are_nonempty_unique_and_keep_strings():
    result = ToolResultsRequest.model_validate(
        {"results": [{"tool_call_id": "cg_123", "content": '{ "value": 1 }'}]}
    )
    assert result.results[0].content == '{ "value": 1 }'
    with pytest.raises(ValidationError):
        ToolResultsRequest.model_validate({"results": []})
    with pytest.raises(ValidationError):
        ToolResultsRequest.model_validate(
            {
                "results": [
                    {"tool_call_id": "same", "content": "one"},
                    {"tool_call_id": "same", "content": "two"},
                ]
            }
        )


def test_configuration_defaults_secret_exclusion_and_namespace():
    settings = Settings.from_env({"CG_API_TOKEN": "synthetic-only"})
    assert settings.max_parallel_llm == 2
    assert settings.max_active_runs == 4 and settings.max_queued_runs == 20
    assert settings.tool_wait_timeout_seconds == 1800
    assert settings.ollama_base_url == "http://host.docker.internal:11434/v1"
    assert "synthetic-only" not in repr(settings)
    assert "synthetic-only" not in settings.model_dump_json()
    assert (
        settings.caller_namespace()
        == Settings.from_env({"CG_API_TOKEN": "synthetic-only"}).caller_namespace()
    )
    assert settings.caller_namespace() != Settings.from_env({}).caller_namespace()


@pytest.mark.parametrize(
    "name,value",
    [
        ("CG_MAX_PARALLEL_LLM", "0"),
        ("CG_MAX_ACTIVE_RUNS", "-1"),
        ("CG_MAX_QUEUED_RUNS", "0"),
        ("CG_TOOL_WAIT_TIMEOUT_SECONDS", "nan"),
        ("CG_HISTORY_RETENTION_DAYS", "bad"),
        ("OLLAMA_BASE_URL", "http://user:secret@server/v1"),
        ("WEB_CONCURRENCY", "2"),
    ],
)
def test_configuration_fails_on_invalid_limits_endpoint_or_workers(name, value):
    with pytest.raises(ValueError):
        Settings.from_env({name: value})


def test_every_error_has_exact_status_and_standard_envelope():
    assert set(ERROR_STATUS) == set(ErrorCode)
    error = CGError(ErrorCode.GRAPH_VALIDATION_FAILED, "Invalid graph")
    assert error.status_code == 400
    assert error.payload().model_dump() == {
        "error": {
            "message": "Invalid graph",
            "type": "invalid_request_error",
            "code": "graph_validation_failed",
        }
    }
    assert CGError(ErrorCode.QUEUE_FULL, "Full").status_code == 429
    assert CGError(ErrorCode.OLLAMA_UNAVAILABLE, "Unavailable").status_code == 503


def test_activation_identity_root_is_non_null_and_iteration_valid():
    key = ActivationKey(run_id="run_1", scope_key="", iteration=0, node_id="a")
    assert key.scope_key == ""
    with pytest.raises(ValidationError):
        ActivationKey(run_id="run_1", scope_key=None, iteration=0, node_id="a")
    with pytest.raises(ValidationError):
        ActivationKey(run_id="run_1", scope_key="", iteration=1, node_id="a")


def test_snapshot_is_immutable_and_hash_validates_content():
    graph = Graph.model_validate(graph_dict())
    snapshot = GraphSnapshot.from_graph(graph)
    graph.nodes[1].system_prompt = "Later edit"
    assert snapshot.graph().nodes[1].system_prompt == "Synthesize."
    loaded = snapshot.graph()
    loaded.nodes[1].system_prompt = "Detached edit"
    assert snapshot.graph().nodes[1].system_prompt == "Synthesize."
    with pytest.raises(ValidationError):
        snapshot.graph_hash = "0" * 64
    with pytest.raises(ValidationError):
        GraphSnapshot(
            graph_id="synthesis", revision=1, graph_json=snapshot.graph_json, graph_hash="0" * 64
        )


def test_canonical_hash_sorts_objects_but_preserves_raw_argument_result_strings():
    assert canonical_hash({"b": 2, "a": 1}) == canonical_hash({"a": 1, "b": 2})
    assert canonical_hash({"arguments": '{"a":1}'}) != canonical_hash({"arguments": '{ "a": 1 }'})
    assert canonical_hash([1, 2]) != canonical_hash([2, 1])


def test_generated_schema_validates_same_graph_and_rejects_missing_seed():
    schema = json.loads((ROOT / "frontend/src/contracts/schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(graph_dict())
    bad = graph_dict()
    bad["edges"].append(
        {
            "id": "aa",
            "source": "a",
            "target": "a",
            "target_port": "old",
            "kind": "feedback",
            "loop_id": "loop",
        }
    )
    assert list(validator.iter_errors(bad))


def test_generation_consistency_and_drift_detection(tmp_path):
    command = [sys.executable, str(ROOT / "scripts/export_contracts.py")]
    assert subprocess.run([*command, "--check"], cwd=ROOT, check=False).returncode == 0
    assert (
        subprocess.run([*command, "--output-root", str(tmp_path)], cwd=ROOT, check=False).returncode
        == 0
    )
    generated = tmp_path / "frontend/src/contracts/generated.ts"
    generated.write_text(generated.read_text() + "// drift\n")
    assert (
        subprocess.run(
            [*command, "--check", "--output-root", str(tmp_path)], cwd=ROOT, check=False
        ).returncode
        == 1
    )


def test_literal_integer_fields_reject_bool_and_float_coercion():
    for value in (True, 1.0):
        data = graph_dict()
        data["schema_version"] = value
        with pytest.raises(ValidationError):
            Graph.model_validate(data)
        request = request_dict()
        request["n"] = value
        with pytest.raises(ValidationError):
            ChatCompletionRequest.model_validate(request)


def test_immutable_context_requires_serialized_json():
    with pytest.raises(ValidationError):
        RunContext(namespace="anonymous", messages_json="not JSON", tools_json="[]")


def test_root_and_loop_scope_identifiers_are_safe():
    with pytest.raises(ValidationError):
        ActivationKey(run_id="r", scope_key="../scope", iteration=0, node_id="a")


def test_controller_schema_enforces_custom_values_without_reinterpreting_payload():
    loop = Loop(
        id="refine",
        node_ids=["a"],
        controller_node_id="a",
        continue_value="again",
        exit_value="done",
    )
    validator = Draft202012Validator(controller_schema(loop))
    validator.validate({"payload": None, "control": {"decision": "again"}})
    assert list(validator.iter_errors({"payload": "text", "control": {"decision": "continue"}}))
    assert list(validator.iter_errors({"payload": "text"}))


def test_input_output_only_plan_does_not_require_an_llm():
    data = graph_dict()
    data["nodes"] = [data["nodes"][0], data["nodes"][2]]
    data["edges"] = [
        {"id": "io", "source": "i", "target": "o", "target_port": "answer", "kind": "forward"}
    ]
    plan = CompiledGraph(
        snapshot=GraphSnapshot.from_graph(Graph.model_validate(data)),
        forward_order=("i", "o"),
        ports=(),
        loops=(),
        output_node_id="o",
        final_llm_node_id=None,
    )
    assert plan.final_llm_node_id is None


def test_internal_model_specific_generation_is_explicit_and_not_client_parameter():
    data = request_dict()
    data["model"] = "installed:tag"
    data["reasoning_effort"] = "none"
    assert ProviderRequest.model_validate(data).reasoning_effort == "none"
    data["model"] = "cg/synthesis"
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(data)


def test_hermes_argument_hash_normalizes_objects_only_without_rewriting_raw_string():
    raw = '{ "z": 2, "a": 1 }'
    assert canonical_arguments_hash(raw) == canonical_arguments_hash('{"a":1,"z":2}')
    assert raw == '{ "z": 2, "a": 1 }'


def checkpoint_fixture():
    created = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    run = RunRecord(
        run_id="run_1",
        snapshot=GraphSnapshot.from_graph(Graph.model_validate(graph_dict())),
        context=RunContext(namespace="anonymous", messages_json="[]", tools_json="[]"),
        inputs_json='{"chat":"Question"}',
        policy=RunPolicy(
            client_request_json=json.dumps(request_dict()),
            max_node_executions=100,
            max_tool_rounds=20,
            active_timeout_seconds=1800,
            tool_wait_timeout_seconds=1800,
        ),
        status="waiting_tools",
        state_version=2,
        created_at=created,
    )
    activation = ActivationRecord(
        activation_id="act_1",
        key=ActivationKey(run_id="run_1", scope_key="", iteration=0, node_id="a"),
        status="waiting_tools",
        inputs=(),
        messages_json="[]",
        provider_round=1,
    )
    args = '{ "path": "é" }'
    tool = PendingTool(
        external_id="cg_opaque",
        run_id="run_1",
        activation_id="act_1",
        node_id="a",
        provider_round=1,
        call_ordinal=0,
        internal_id="collision",
        name="read_file",
        arguments=args,
        arguments_hash=raw_text_hash(args),
        canonical_arguments_hash=canonical_arguments_hash(args),
        batch_id="batch_1",
        status="pending",
    )
    envelope = ResponseEnvelope(
        run_id="run_1",
        batch_id="batch_1",
        response_sequence=1,
        completion_json=json.dumps(
            {
                "id": "completion_1",
                "created": 1791050000,
                "model": "cg/synthesis",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "cg_opaque",
                                    "type": "function",
                                    "function": {"name": "read_file", "arguments": args},
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            }
        ),
    )
    batch = ToolBatch(
        batch_id="batch_1",
        run_id="run_1",
        sequence=1,
        status="open",
        external_ids=("cg_opaque",),
        prepared_at=created,
        expires_at=datetime(2026, 10, 3, 12, 30, tzinfo=UTC),
        envelope=envelope,
    )
    checkpoint = RunCheckpoint(
        run=run,
        activations=(activation,),
        loops=(),
        pending_tools=(tool,),
        batches=(batch,),
        responses=(envelope,),
        events_json=(),
    )
    return checkpoint, batch


def test_activation_length_finish_reason_survives_checkpoint_reload():
    checkpoint, _ = checkpoint_fixture()
    data = checkpoint.model_dump(mode="json")
    data["activations"][0]["finish_reason"] = "length"
    restored = RunCheckpoint.model_validate_json(json.dumps(data))
    assert restored.activations[0].finish_reason == "length"
    assert RunCheckpoint.model_validate_json(restored.model_dump_json()) == restored


def test_activation_without_provider_response_has_no_finish_reason():
    checkpoint, _ = checkpoint_fixture()
    assert checkpoint.activations[0].finish_reason is None
    data = checkpoint.model_dump(mode="json")
    del data["activations"][0]["finish_reason"]
    assert RunCheckpoint.model_validate_json(json.dumps(data)).activations[0].finish_reason is None


def test_activation_malformed_finish_reason_is_rejected():
    checkpoint, _ = checkpoint_fixture()
    data = checkpoint.model_dump(mode="json")
    data["activations"][0]["finish_reason"] = "truncated"
    with pytest.raises(ValidationError):
        RunCheckpoint.model_validate_json(json.dumps(data))


def test_tool_checkpoint_roundtrip_is_immutable_and_rejects_uncertain_sibling():
    checkpoint, batch = checkpoint_fixture()
    exposed = ToolCheckpoint(checkpoint=checkpoint, batch=batch)
    restored = ToolCheckpoint.model_validate_json(exposed.model_dump_json())
    assert restored == exposed
    detached = restored.batch.envelope.completion()
    detached.choices[0].message.tool_calls[0].function.arguments = "{}"
    assert restored.checkpoint.pending_tools[0].arguments == '{ "path": "é" }'
    assert (
        restored.batch.envelope.completion().choices[0].message.tool_calls[0].function.arguments
        == '{ "path": "é" }'
    )
    altered = checkpoint.model_dump(mode="json")
    altered["activations"][0]["status"] = "running"
    altered["activations"][0]["attempt_id"] = "uncertain"
    with pytest.raises(ValidationError, match="quiescent"):
        ToolCheckpoint.model_validate_json(
            json.dumps({"checkpoint": altered, "batch": batch.model_dump(mode="json")})
        )


def test_batch_identity_expiry_and_utc_are_contract_boundaries():
    _, batch = checkpoint_fixture()
    for field, value in (
        ("expires_at", batch.prepared_at),
        ("prepared_at", datetime(2026, 10, 3)),
        ("external_ids", ("different",)),
        ("sequence", 2),
    ):
        data = batch.model_dump()
        data[field] = value
        with pytest.raises(ValidationError):
            ToolBatch.model_validate(data)


def test_pending_tool_raw_and_normalized_hashes_cannot_drift():
    checkpoint, _ = checkpoint_fixture()
    data = checkpoint.pending_tools[0].model_dump()
    data["arguments"] = '{"path":"é"}'
    with pytest.raises(ValidationError, match="Raw tool arguments hash"):
        PendingTool.model_validate(data)
    data["arguments_hash"] = raw_text_hash(data["arguments"])
    assert (
        PendingTool.model_validate(data).canonical_arguments_hash
        == checkpoint.pending_tools[0].canonical_arguments_hash
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_json_rejected_at_boundary_in_seeds_and_tool_schemas(value):
    data = graph_dict()
    data["edges"].append(
        {
            "id": "aa",
            "source": "a",
            "target": "a",
            "target_port": "old",
            "kind": "feedback",
            "loop_id": "refine",
            "initial_value": {"nested": [value]},
        }
    )
    with pytest.raises(ValidationError, match="finite"):
        Graph.model_validate_json(json.dumps(data))
    request = request_dict()
    request["tools"][0]["function"]["parameters"]["default"] = value
    with pytest.raises(ValidationError, match="finite"):
        ChatCompletionRequest.model_validate_json(json.dumps(request))
