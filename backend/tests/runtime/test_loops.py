import asyncio
import copy
import json

import pytest
from jsonschema import Draft201909Validator, Draft202012Validator
from jsonschema.validators import validator_for
from referencing import Registry
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

from app.contracts.api import ChatCompletionRequest
from app.contracts.config import Settings
from app.contracts.errors import CGError
from app.runtime.engine import AsyncGraphRuntime


def loop_graph():
    return graph(
        nodes=[input_node("i"), llm("draft"), llm("critique"), output_node()],
        edges=[
            edge("i", "draft", "question"),
            edge("draft", "critique", "draft"),
            edge("critique", "o", "answer"),
            {
                "id": "feedback",
                "source": "critique",
                "target": "draft",
                "target_port": "previous",
                "kind": "feedback",
                "loop_id": "L",
                "initial_value": None,
            },
        ],
        loops=[
            {
                "id": "L",
                "node_ids": ["draft", "critique"],
                "controller_node_id": "critique",
                "continue_value": "continue",
                "exit_value": "stop",
            }
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["ok", 3])
@pytest.mark.parametrize(
    "target",
    [
        "answer",
        "extends",
        "escaped",
        "annotation",
        "inherited",
        "legacy_id",
        "root_id",
        "absolute",
        "recursive",
        "legacy_absolute",
        "relative_id",
        "nested_pointer",
        "percent_pointer",
        "resolver_context",
    ],
)
async def test_mixed_draft3_single_extends_preserves_emitted_schema_and_recovery(
    tmp_path, payload, target
):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "#/definitions/Answer",
        "definitions": {
            "Text": {"type": "string"},
            "Answer": {
                "$schema": "http://json-schema.org/draft-03/schema#",
                "extends": {"$ref": "#/definitions/Text"},
            },
        },
    }
    if target == "extends":
        schema["$ref"] += "/extends"
    elif target == "escaped":
        schema["definitions"]["Text/~"] = schema["definitions"].pop("Text")
        schema["definitions"]["Answer"]["extends"]["$ref"] = "#/definitions/Text~1~0"
    elif target == "annotation":
        schema["examples"] = [copy.deepcopy(schema["definitions"]["Answer"])]
        schema["$ref"] = "#/examples/0"
    elif target in {"inherited", "nested_pointer"}:
        schema["definitions"]["Answer"]["extends"] = [{"extends": {"$ref": "#/definitions/Text"}}]
        if target == "nested_pointer":
            schema["$ref"] += "/extends/0/extends"
    elif target == "legacy_id":
        # The containing modern resource does not recognize Draft 3's id.
        schema["definitions"]["Answer"]["id"] = "https://example.invalid/answer"
    elif target in {"root_id", "absolute"}:
        schema["$id"] = "https://example.invalid/root"
        if target == "absolute":
            schema["definitions"]["Answer"]["extends"]["$ref"] = (
                "https://example.invalid/root#/definitions/Text"
            )
    elif target == "recursive":
        schema["$schema"] = "https://json-schema.org/draft/2019-09/schema"
        schema["$recursiveAnchor"] = True
        schema["type"] = "object"
        schema["properties"] = {
            "value": {"$ref": schema.pop("$ref")},
            "children": {"type": "array", "items": {"$recursiveRef": "#"}},
        }
        schema["required"] = ["value"]
    elif target == "legacy_absolute":
        schema["$schema"] = "http://json-schema.org/draft-03/schema#"
        schema["id"] = "https://example.invalid/root"
        schema["extends"] = {"$ref": schema.pop("$ref")}
    elif target == "relative_id":
        schema["$id"] = "payload.json"
    elif target == "percent_pointer":
        schema["definitions"]["Answer%2F"] = schema["definitions"].pop("Answer")
        schema["$ref"] = "#/definitions/Answer%252F/extends"
    elif target == "resolver_context":
        schema["$ref"] = "#/definitions/A/definitions/B/definitions/C"
        schema["definitions"] = {
            "A": {
                "$schema": "http://json-schema.org/draft-03/schema#",
                "definitions": {
                    "B": {
                        "id": "nested",
                        "extends": {"type": "string"},
                        "definitions": {"C": {"$ref": "#/definitions/A/definitions/B/extends"}},
                    }
                },
            }
        }
    good, bad = "ok", 3
    if target == "recursive":
        good = {"value": "ok", "children": [{"value": "ok"}]}
        bad = {"value": "ok", "children": [{"value": 3}]}
    payload = good if payload == "ok" else bad
    original = copy.deepcopy(schema)
    validator = validator_for(schema)
    validator.check_schema(schema)
    validator(schema, registry=Registry()).validate(good)
    assert not validator(schema, registry=Registry()).is_valid(bad)
    client = {
        "model": "cg/g",
        "messages": [{"role": "user", "content": "test"}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": schema},
        },
    }
    ChatCompletionRequest.model_validate(client)
    observed = []

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        wrapped_validator = validator_for(emitted)
        wrapped_validator.check_schema(emitted)
        wrapped = wrapped_validator(emitted, registry=Registry())
        wrapped.validate({"payload": good, "control": {"decision": "stop"}})
        assert not wrapped.is_valid({"payload": bad, "control": {"decision": "stop"}})
        assert not wrapped.is_valid({"payload": good, "control": {"decision": "invalid"}})
        if target == "annotation":
            assert emitted["properties"]["payload"]["examples"] == original["examples"]
        observed.append(emitted)
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    final = None
    try:
        run = await runtime.submit(submission(loop_graph(), client=client))
        if payload == good:
            final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
            assert json.loads(final.completion().choices[0].message.content) == good
        else:
            with pytest.raises(CGError) as failure:
                await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
            assert failure.value.code.value == "upstream_error"
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == ("completed" if final else "failed")
        assert checkpoint.responses == ((final,) if final else ())
        assert checkpoint.run.output_json == (
            json.dumps(good, sort_keys=True, separators=(",", ":")) if final else None
        )
        assert not checkpoint.pending_tools
        assert json.loads(checkpoint.run.policy.client_request_json) == client
        assert schema == original and len(observed) == 1 and len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        if final:
            assert await runtime.await_response(run.run_id, "anonymous") == final
        else:
            with pytest.raises(CGError) as failure:
                await runtime.await_response(run.run_id, "anonymous")
            assert failure.value.code.value == "upstream_error"
        assert len(provider.requests) == 2 and schema == original
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keyword,nested_resource",
    [(keyword, False) for keyword in ("extends", "extends_list", "type", "disallow")]
    + [(keyword, True) for keyword in ("extends_list", "type", "disallow")],
)
@pytest.mark.parametrize("root_id", [None, "#root"])
async def test_draft3_controller_schema_alternatives_preserve_validation_and_replay(
    tmp_path, keyword, root_id, nested_resource
):
    reference = {"$ref": "#/definitions/Text"}
    constraint = {
        "extends": {"extends": reference},
        "extends_list": {"extends": [reference, {}]},
        "type": {"type": [reference, "boolean"]},
        "disallow": {"disallow": [reference, "boolean"]},
    }[keyword]
    definition = {"type": "integer" if keyword == "disallow" else "string"}
    literal = {"id": "#", "$ref": "#/literal", "extends": {"$ref": "#"}}
    constraint["default"] = copy.deepcopy(literal)
    if nested_resource:
        constraint.update(
            {"id": "https://example.invalid/answer", "definitions": {"Text": definition}}
        )
    schema = {
        "$schema": "http://json-schema.org/draft-03/schema#",
        "$ref": "#/definitions/Answer",
        "definitions": {"Text": definition, "Answer": constraint},
    }
    if root_id:
        schema["id"] = root_id
    original = copy.deepcopy(schema)
    validator = validator_for(schema)
    validator.check_schema(schema)
    validator(schema, registry=Registry()).validate("ok")
    assert not validator(schema, registry=Registry()).is_valid(3)
    client = {
        "model": "cg/g",
        "messages": [{"role": "user", "content": "test"}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": schema, "strict": True},
        },
    }
    ChatCompletionRequest.model_validate(client)
    observed = []

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        emitted_validator = validator_for(emitted)
        emitted_validator.check_schema(emitted)
        wrapped = emitted_validator(emitted, registry=Registry())
        wrapped.validate({"payload": "ok", "control": {"decision": "stop"}})
        assert not wrapped.is_valid({"payload": 3, "control": {"decision": "stop"}})
        assert wrapped.is_valid({"payload": True, "control": {"decision": "stop"}}) == (
            keyword == "type"
        )
        assert not wrapped.is_valid({"payload": "ok", "control": {"decision": "invalid"}})
        assert not wrapped.is_valid({"payload": "ok"})
        embedded = emitted["properties"]["payload"]["definitions"]["Answer"]
        assert embedded["default"] == literal
        if nested_resource:
            assert embedded == constraint
        observed.append(emitted)
        return response('{"payload":"ok","control":{"decision":"stop"}}')

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(submission(loop_graph(), client=client))
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "completed" and checkpoint.responses == (final,)
        assert final.completion().choices[0].message.content == '"ok"'
        assert json.loads(checkpoint.run.policy.client_request_json) == client
        assert schema == original and len(observed) == 1 and len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert await runtime.await_response(run.run_id, "anonymous") == final
        assert len(provider.requests) == 2 and schema == original
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.parametrize("draft", ["04", "06", "07", "2019-09", "2020-12"])
def test_draft3_only_keywords_remain_literal_in_other_dialects(draft):
    legacy = draft in {"04", "06", "07"}
    dialect = (
        f"http://json-schema.org/draft-{draft}/schema#"
        if legacy
        else f"https://json-schema.org/draft/{draft}/schema"
    )
    literal = {"id": "#", "$id": "#", "$ref": "#/literal"}
    schema = {
        "$schema": dialect,
        "id" if draft == "04" else "$id": "#root" if legacy else "payload.json",
        "type": "string",
        "extends": [literal, {"extends": literal}],
        "disallow": [literal, "string"],
    }
    original = copy.deepcopy(schema)
    validator_for(schema).check_schema(schema)
    AsyncGraphRuntime._embed_payload_references(schema)
    assert schema["extends"] == original["extends"]
    assert schema["disallow"] == original["disallow"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "identifier", [None, "", "#", "payload.json", "https://example.invalid/payload"]
)
@pytest.mark.parametrize("nested", [False, True])
async def test_controller_emitted_schema_preserves_resource_ids(tmp_path, identifier, nested):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {"Text": {"type": "string"}},
        "type": "object",
        "properties": {"value": {"$ref": "#/$defs/Text"}},
        "required": ["value"],
    }
    if nested:
        child = {
            "type": "object",
            "properties": {"value": {"$ref": "#/$defs/Text"}},
            "required": ["value"],
        }
        if identifier is not None:
            child["$id"] = identifier
        if identifier not in (None, "", "#"):
            child["$defs"] = {"Text": {"type": "string"}}
        schema["properties"] = {"nested": child}
        schema["required"] = ["nested"]
        payload, bad = {"nested": {"value": "ok"}}, {"nested": {"value": 123}}
    else:
        if identifier is not None:
            schema["$id"] = identifier
        payload, bad = {"value": "ok"}, {"value": 123}
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    assert not Draft202012Validator(schema).is_valid(bad)
    client = {
        "model": "cg/g",
        "messages": [{"role": "user", "content": "test"}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "strict": True, "schema": schema},
        },
    }
    assert (
        ChatCompletionRequest.model_validate(client).response_format.json_schema.schema_ == schema
    )
    original = copy.deepcopy(client)

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        Draft202012Validator(emitted).validate(
            {"payload": payload, "control": {"decision": "stop"}}
        )
        assert not Draft202012Validator(emitted).is_valid(
            {"payload": bad, "control": {"decision": "stop"}}
        )
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(submission(loop_graph(), client=client))
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "completed" and checkpoint.responses[-1] == final
        assert json.loads(final.completion().choices[0].message.content) == payload
        assert json.loads(checkpoint.run.policy.client_request_json) == original == client
        assert len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert (await runtime.await_response(run.run_id, "anonymous")) == final
        assert len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "draft,identifier",
    [
        (draft, identifier)
        for draft in ("03", "04", "06", "07", "2019-09", "2020-12")
        for identifier in (None, "", "#", "payload.json", "https://example.invalid/payload")
    ]
    + [("03", "#root"), ("04", "#root"), ("06", "#root"), ("07", "#root")],
)
@pytest.mark.parametrize("root_reference", [False, True])
async def test_controller_emitted_schema_preserves_declared_dialects(
    tmp_path, draft, identifier, root_reference
):
    legacy = draft in {"03", "04", "06", "07"}
    dialect = (
        f"http://json-schema.org/draft-{draft}/schema#"
        if legacy
        else f"https://json-schema.org/draft/{draft}/schema"
    )
    definitions = "definitions" if legacy else "$defs"
    keyword = "id" if draft in {"03", "04"} else "$id"
    answer = {
        "type": "object",
        "properties": {"value": {"$ref": f"#/{definitions}/Text"}},
        "required": ["value"],
    }
    if draft == "03":
        del answer["required"]
        answer["properties"]["value"]["required"] = True
    payload, bad = {"value": "ok"}, {"value": 123}
    if identifier == "#root" and not root_reference:
        answer["properties"]["self"] = {"$ref": "#root"}
        payload, bad = (
            {"value": "ok", "self": {"value": "ok"}},
            {"value": "ok", "self": {"value": 123}},
        )
    schema = {
        "$schema": dialect,
        definitions: {"Text": {"type": "string"}, "Answer": copy.deepcopy(answer)},
        **answer,
    }
    if identifier is not None:
        schema[keyword] = identifier
    if root_reference:
        schema["$ref"] = f"#/{definitions}/Answer"
    original = copy.deepcopy(schema)
    validator = validator_for(schema)
    validator.check_schema(schema)
    validator(schema, registry=Registry()).validate(payload)
    assert not validator(schema, registry=Registry()).is_valid(bad)
    client = {
        "model": "cg/g",
        "messages": [{"role": "user", "content": "test"}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": schema, "strict": True},
        },
    }
    ChatCompletionRequest.model_validate(client)

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        assert emitted["$schema"] == dialect
        actual_validator = validator_for(emitted)
        actual_validator.check_schema(emitted)
        actual_validator(emitted, registry=Registry()).validate(
            {"payload": payload, "control": {"decision": "stop"}}
        )
        assert not actual_validator(emitted, registry=Registry()).is_valid(
            {"payload": bad, "control": {"decision": "stop"}}
        )
        assert not actual_validator(emitted, registry=Registry()).is_valid(
            {"payload": payload, "control": {"decision": "other"}}
        )
        if identifier not in (None, "", "#"):
            assert emitted["properties"]["payload"][keyword] == identifier
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(submission(loop_graph(), client=client))
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "completed" and checkpoint.responses[-1] == final
        assert json.loads(final.completion().choices[0].message.content) == payload
        assert client["response_format"]["json_schema"]["schema"] == original
        assert (
            json.loads(checkpoint.run.policy.client_request_json)["response_format"]["json_schema"][
                "schema"
            ]
            == original
        )
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert (await runtime.await_response(run.run_id, "anonymous")) == final
        assert len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("draft", ["04", "07"])
@pytest.mark.parametrize("recursive", [False, True])
async def test_legacy_active_extension_reference_preserves_dual_use_literal(
    tmp_path, draft, recursive
):
    literal = (
        {
            "type": "object",
            "properties": {
                "value": {"$ref": "#/definitions/Text"},
                "children": {"type": "array", "items": {"$ref": "#/x-schema"}},
            },
            "required": ["value"],
        }
        if recursive
        else {"$ref": "#/definitions/Text"}
    )
    payload, bad = (
        (
            {"value": "ok", "children": [{"value": "child"}]},
            {"value": "ok", "children": [{"value": 3}]},
        )
        if recursive
        else ("ok", 123)
    )
    schema = {
        "$schema": f"http://json-schema.org/draft-{draft}/schema#",
        "$ref": "#/x-schema",
        "definitions": {"Text": {"type": "string"}},
        "x-schema": literal,
        "const": literal,
    }
    original = copy.deepcopy(schema)
    original_validator = validator_for(schema)
    original_validator.check_schema(schema)
    original_validator(schema, registry=Registry()).validate(payload)
    assert not original_validator(schema, registry=Registry()).is_valid(bad)

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        payload_schema = emitted["properties"]["payload"]
        assert payload_schema["x-schema"] == payload_schema["const"] == literal
        validator = validator_for(emitted)(emitted, registry=Registry())
        validator.validate({"payload": payload, "control": {"decision": "stop"}})
        assert not validator.is_valid({"payload": bad, "control": {"decision": "stop"}})
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    provider = Provider(handler)
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        run = await runtime.submit(
            submission(
                loop_graph(),
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "answer", "schema": schema},
                    },
                },
            )
        )
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert json.loads(final.completion().choices[0].message.content) == payload
        assert schema == original
    finally:
        await runtime.shutdown()
        await repository.close()
    runtime, repository = await create_runtime(tmp_path, provider)
    try:
        await runtime.recover()
        assert (await runtime.await_response(run.run_id, "anonymous")) == final
        assert len(provider.requests) == 2
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_seed_two_continues_then_exit_preserves_inputs(tmp_path):
    iteration = 0

    async def handler(request):
        nonlocal iteration
        ports = {
            item["port"]: item["value"]
            for item in json.loads(request.messages[-1].content)["inputs"]
        }
        if node_request(request) == "draft":
            assert ports == {
                "question": "question",
                "previous": None if iteration == 0 else f"critique-{iteration - 1}",
            }
            return response(f"draft-{iteration}")
        assert ports == {"draft": f"draft-{iteration}"}
        assert request.response_format.type == "json_schema"
        decision = "continue" if iteration < 2 else "stop"
        result = response(
            json.dumps({"payload": f"critique-{iteration}", "control": {"decision": decision}})
        )
        iteration += 1
        return result

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(submission(loop_graph()))
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == "critique-2"
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.node_executions == 6
        assert checkpoint.loops[0].iteration == 2 and checkpoint.loops[0].status == "completed"
        assert len([item for item in checkpoint.activations if item.key.node_id == "draft"]) == 3
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [True, False])
async def test_invalid_control_or_endless_continue_fails(tmp_path, invalid):
    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        return response(
            "prose" if invalid else '{"payload":"again","control":{"decision":"continue"}}'
        )

    settings = Settings(max_node_executions=4)
    runtime, repository = await create_runtime(tmp_path, Provider(handler), settings)
    try:
        run = await runtime.submit(submission(loop_graph(), settings))
        with pytest.raises(CGError):
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        saved = await repository.get_run(run.run_id, "anonymous")
        assert saved.status == "failed"
        assert json.loads(saved.error_json)["code"] == (
            "graph_validation_failed" if invalid else "budget_exceeded"
        )
        assert saved.output_json is None
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_disjoint_loops_immutable_input_members_and_noncontroller_feedback(tmp_path):
    nodes = [input_node("external", "extra"), llm("join"), output_node()]
    edges = [edge("join", "o", "answer")]
    loops = []
    counts = {"L": 0, "R": 0}
    for name in ("L", "R"):
        nodes.extend([input_node("i" + name), llm("d" + name), llm("c" + name)])
        edges.extend(
            [
                edge("i" + name, "d" + name, "question"),
                edge("external", "d" + name, "constant"),
                edge("d" + name, "c" + name, "draft"),
                edge("c" + name, "join", name),
                {
                    "id": "feedback" + name,
                    "source": "d" + name,
                    "target": "d" + name,
                    "target_port": "previous",
                    "kind": "feedback",
                    "loop_id": name,
                    "initial_value": "seed" + name,
                },
            ]
        )
        loops.append(
            {
                "id": name,
                "node_ids": ["i" + name, "d" + name, "c" + name],
                "controller_node_id": "c" + name,
                "continue_value": "again",
                "exit_value": "done",
            }
        )
    value = graph(
        nodes=nodes,
        edges=edges,
        loops=loops,
        inputs=[{"id": "chat", "required": True}, {"id": "extra", "required": False}],
    )

    async def handler(request):
        node = node_request(request)
        ports = {
            item["port"]: item["value"]
            for item in json.loads(request.messages[-1].content)["inputs"]
        }
        if node == "join":
            assert counts == {"L": 2, "R": 3}
            assert ports == {"L": "exitL", "R": "exitR"}
            return response("joined")
        name = node[-1]
        iteration = counts[name]
        if node.startswith("d"):
            assert ports == {
                "question": "question",
                "constant": None,
                "previous": "seed" + name if iteration == 0 else f"draft{name}{iteration - 1}",
            }
            return response(f"draft{name}{iteration}")
        assert ports == {"draft": f"draft{name}{iteration}"}
        counts[name] += 1
        stop = counts[name] == (2 if name == "L" else 3)
        return response(
            json.dumps(
                {
                    "payload": "exit" + name if stop else "ignored",
                    "control": {"decision": "done" if stop else "again"},
                }
            )
        )

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(submission(value, inputs={"chat": "question"}))
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == "joined"
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert [(loop.loop_id, loop.iteration) for loop in checkpoint.loops] == [("L", 1), ("R", 2)]
        assert all(
            item.payload_json == '"question"'
            for item in checkpoint.activations
            if item.key.node_id in {"iL", "iR"}
        )
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_final_controller_keeps_control_schema_and_client_payload_format(tmp_path):
    async def handler(request):
        if node_request(request) == "draft":
            assert request.temperature is None
            return response("draft")
        assert request.temperature == 0.8
        schema = request.response_format.json_schema.schema_
        assert schema["$defs"]["Control"]["properties"]["decision"]["enum"] == ["continue", "stop"]
        assert schema["properties"]["payload"]["properties"]["answer"]["$ref"] == "#/$defs/Text"
        assert schema["properties"]["payload"]["$id"].startswith(
            "https://cognitive-graph.invalid/schema/"
        )
        return response('{"payload":{"answer":"final"},"control":{"decision":"stop"}}')

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(
                loop_graph(),
                client={
                    "model": "cg/g",
                    "temperature": 0.8,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "answer",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "$defs": {"Text": {"type": "string"}},
                                "properties": {"answer": {"$ref": "#/$defs/Text"}},
                                "required": ["answer"],
                            },
                        },
                    },
                },
            )
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert json.loads(result.completion().choices[0].message.content) == {"answer": "final"}
        assert "control" not in result.completion().choices[0].message.content
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        "hello",
        'quoted "value"\nnext',
        "123",
        "null",
        None,
        7,
        True,
        {"answer": "value"},
        {"$ref": "#/literal", "nested": [{"$ref": "#"}]},
        ["first", 2],
    ],
)
async def test_controller_json_payload_serialization_preserves_exact_value(tmp_path, payload):
    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_["properties"]["payload"]
        assert {key: value for key, value in emitted.items() if key != "$id"} == {"const": payload}
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(
                loop_graph(),
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "exact",
                            "strict": True,
                            "schema": {"const": payload},
                        },
                    },
                },
            )
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        content = result.completion().choices[0].message.content
        assert json.loads(content) == payload and type(json.loads(content)) is type(payload)
        Draft202012Validator({"const": payload}).validate(json.loads(content))
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.responses[-1] == result
        assert checkpoint.run.output_json == json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        assert (await runtime.await_response(run.run_id, "anonymous")) == result
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.parametrize("keyword", ["const", "enum", "default", "examples", "x-metadata"])
def test_schema_rebasing_preserves_literal_reference_data(keyword):
    literal = {
        "$ref": "#/literal",
        "$dynamicRef": "#literal",
        "$recursiveRef": "#",
        "nested": [{"$ref": "#", "$id": "data-id"}, {"properties": {"$ref": "literal-property"}}],
    }
    schema = {
        "type": "object",
        "$defs": {"Actual": {"type": "string"}},
        "properties": {"value": {"$ref": "#/$defs/Actual"}},
        keyword: [literal] if keyword in {"enum", "examples"} else literal,
    }
    original = copy.deepcopy(schema)
    AsyncGraphRuntime._embed_payload_references(schema)
    assert schema[keyword] == original[keyword]
    assert schema["properties"]["value"]["$ref"] == "#/$defs/Actual"
    assert schema["$id"].startswith("https://cognitive-graph.invalid/schema/")
    Draft202012Validator({"properties": {"payload": schema}}).validate({"payload": literal})


def test_schema_rebasing_changes_schema_maps_lists_only_and_preserves_resources():
    schema = {
        "$defs": {
            "Text": {"$anchor": "text", "type": "string"},
            "Child": {
                "$id": "https://example.invalid/child",
                "type": "object",
                "$defs": {"Number": {"type": "integer"}},
                "properties": {"number": {"$ref": "#/$defs/Number"}},
                "required": ["number"],
            },
        },
        "type": "object",
        "properties": {
            "text": {"$ref": "#text"},
            "child": {"$ref": "#/$defs/Child"},
            "items": {
                "type": "array",
                "prefixItems": [{"$ref": "#/$defs/Text"}],
                "items": {"allOf": [{"$ref": "#/$defs/Text"}], "examples": [{"$ref": "#/literal"}]},
            },
        },
        "required": ["text", "child", "items"],
    }
    original = copy.deepcopy(schema)
    AsyncGraphRuntime._embed_payload_references(schema)
    assert schema["$defs"]["Child"] == original["$defs"]["Child"]
    assert schema["properties"]["text"]["$ref"] == "#text"
    assert schema["properties"]["items"]["prefixItems"][0]["$ref"] == "#/$defs/Text"
    assert schema["properties"]["items"]["items"]["examples"] == [{"$ref": "#/literal"}]
    wrapped = {"type": "object", "properties": {"payload": schema}, "required": ["payload"]}
    instance = {"payload": {"text": "value", "child": {"number": 5}, "items": ["a", "b"]}}
    Draft202012Validator(wrapped).validate(instance)


@pytest.mark.parametrize("resource_id", [None, "https://example.invalid/tree"])
def test_schema_embedding_preserves_recursive_resource_semantics(resource_id):
    schema = {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
        "$recursiveAnchor": True,
        "type": "object",
        "properties": {"children": {"type": "array", "items": {"$recursiveRef": "#"}}},
        "additionalProperties": False,
    }
    if resource_id:
        schema["$id"] = resource_id
    original = copy.deepcopy(schema)
    AsyncGraphRuntime._embed_payload_references(schema)
    wrapped = {"properties": {"payload": schema}}
    assert schema["properties"]["children"]["items"]["$recursiveRef"] == "#"
    good = {"children": [{"children": []}]}
    bad = {"children": [{"unexpected": True}]}
    assert Draft201909Validator(original).is_valid(good)
    assert not Draft201909Validator(original).is_valid(bad)
    assert Draft201909Validator(wrapped).is_valid({"payload": good})
    assert not Draft201909Validator(wrapped).is_valid({"payload": bad})


@pytest.mark.asyncio
@pytest.mark.parametrize("requested", [None, {"type": "text"}])
async def test_controller_text_format_keeps_unquoted_string_payload(tmp_path, requested):
    payload = 'quoted "value"\n123'

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(loop_graph(), client={"model": "cg/g", "response_format": requested})
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert result.completion().choices[0].message.content == payload
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
async def test_controller_json_object_format_serializes_only_payload(tmp_path):
    payload = {"text": 'quoted "value"', "control": {"literal": True}}

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        assert request.response_format.json_schema.schema_["properties"]["payload"] == {
            "type": "object"
        }
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(
                loop_graph(), client={"model": "cg/g", "response_format": {"type": "json_object"}}
            )
        )
        result = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert json.loads(result.completion().choices[0].message.content) == payload
        assert (await repository.load_checkpoint(run.run_id, "anonymous")).responses[-1] == result
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "schema,payload",
    [
        ({"const": {"expected": 1}}, {"expected": 2}),
        ({"type": "object", "required": ["value"]}, {}),
        (
            {
                "$defs": {"Text": {"type": "string"}},
                "properties": {"value": {"$ref": "#/$defs/Text"}},
            },
            {"value": 3},
        ),
        (None, "scalar"),
    ],
)
async def test_controller_rejects_malformed_final_payload_before_envelope(
    tmp_path, schema, payload
):
    requested = (
        {"type": "json_object"}
        if schema is None
        else {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}
    )

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(loop_graph(), client={"model": "cg/g", "response_format": requested})
        )
        with pytest.raises(CGError) as failure:
            await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert failure.value.code.value == "upstream_error"
        checkpoint = await repository.load_checkpoint(run.run_id, "anonymous")
        assert checkpoint.run.status == "failed" and not checkpoint.responses
        assert checkpoint.run.output_json is None
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("reference_kind", ["anchor", "dynamic", "recursive", "escaped"])
async def test_controller_emitted_schema_keeps_recursive_anchor_and_escaped_references(
    tmp_path, reference_kind
):
    if reference_kind in {"dynamic", "recursive"}:
        recursive = reference_kind == "recursive"
        draft = "2019-09" if recursive else "2020-12"
        schema = {
            "$schema": f"https://json-schema.org/draft/{draft}/schema",
            "$recursiveAnchor" if recursive else "$dynamicAnchor": True if recursive else "tree",
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "children": {
                    "type": "array",
                    "items": {
                        "$recursiveRef" if recursive else "$dynamicRef": "#"
                        if recursive
                        else "#tree"
                    },
                },
            },
            "required": ["value"],
        }
        payload, bad = (
            {"value": "ok", "children": [{"value": "ok"}]},
            {"value": "ok", "children": [{"value": 3}]},
        )
    else:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "$defs": {"Text/tilde~": {"type": "string", "$anchor": "text"}},
            "properties": {
                "value": {
                    "$ref": "#text" if reference_kind == "anchor" else "#/$defs/Text~1tilde~0"
                }
            },
            "required": ["value"],
        }
        payload, bad = {"value": "ok"}, {"value": 3}
    original = copy.deepcopy(schema)
    validator = validator_for(schema)
    validator.check_schema(schema)
    validator(schema, registry=Registry()).validate(payload)
    assert not validator(schema, registry=Registry()).is_valid(bad)

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        wrapped = validator_for(emitted)(emitted, registry=Registry())
        wrapped.validate({"payload": payload, "control": {"decision": "stop"}})
        assert not wrapped.is_valid({"payload": bad, "control": {"decision": "stop"}})
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(
                loop_graph(),
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "answer", "schema": schema},
                    },
                },
            )
        )
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert json.loads(final.completion().choices[0].message.content) == payload
        assert schema == original
    finally:
        await runtime.shutdown()
        await repository.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parent,child", [("04", "2020-12"), ("2020-12", "04"), ("2020-12", "2019-09")]
)
async def test_controller_embedding_preserves_declared_nested_dialect_boundaries(
    tmp_path, parent, child
):
    def dialect(draft):
        return (
            f"http://json-schema.org/draft-{draft}/schema#"
            if draft == "04"
            else f"https://json-schema.org/draft/{draft}/schema"
        )

    same_id_keyword = parent != "04" and child != "04"
    parent_defs = "definitions" if parent == "04" else "$defs"
    child_defs = "definitions" if child == "04" else "$defs"
    child_schema = {
        "$schema": dialect(child),
        "id" if child == "04" else "$id": "https://example.invalid/child",
        child_defs: {"Text": {"type": "string" if same_id_keyword else "integer"}},
        "type": "object",
        "properties": {
            "value": {"$ref": f"#/{child_defs if same_id_keyword else parent_defs}/Text"}
        },
        "required": ["value"],
    }
    schema = {
        "$schema": dialect(parent),
        parent_defs: {"Text": {"type": "integer" if same_id_keyword else "string"}},
        "type": "object",
        "properties": {"child": child_schema},
        "required": ["child"],
    }
    original = copy.deepcopy(schema)
    payload, bad = {"child": {"value": "ok"}}, {"child": {"value": 3}}
    validator = validator_for(schema)(schema, registry=Registry())
    validator.validate(payload)
    assert not validator.is_valid(bad)

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        wrapped = validator_for(emitted)(emitted, registry=Registry())
        wrapped.validate({"payload": payload, "control": {"decision": "stop"}})
        assert not wrapped.is_valid({"payload": bad, "control": {"decision": "stop"}})
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    runtime, repository = await create_runtime(tmp_path, Provider(handler))
    try:
        run = await runtime.submit(
            submission(
                loop_graph(),
                client={
                    "model": "cg/g",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "answer", "schema": schema},
                    },
                },
            )
        )
        final = await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
        assert json.loads(final.completion().choices[0].message.content) == payload
        assert schema == original
    finally:
        await runtime.shutdown()
        await repository.close()
