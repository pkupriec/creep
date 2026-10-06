"""Offline installed-image proof for the F6 dependency correction, not live inference."""

import copy
import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

import referencing.jsonschema as referencing_schema
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT3, DRAFT4

from app.contracts.graph import Loop, controller_schema
from app.runtime.engine import AsyncGraphRuntime

assert os.getuid() == 10001
assert sys.version_info[:3] == (3, 11, 15)
assert version("referencing") == "0.37.0+cg.1"
assert version("jsonschema") == "4.26.0"
source = Path(referencing_schema.__file__)
assert str(source).startswith("/app/.venv/lib/python3.11/site-packages/")
assert hashlib.sha256(source.read_bytes()).hexdigest() == (
    "d71d7e00650fa3411b1957b1517d95a515461d7d428753eaf7a2719c10482c86"
)
engine_hash = hashlib.sha256(Path("/app/app/runtime/engine.py").read_bytes()).hexdigest()
assert engine_hash == "7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f"
child = {"type": "string"}
for extends in (child, [child]):
    resource = Resource.from_contents({"extends": extends}, default_specification=DRAFT3)
    assert [item.contents for item in resource.subresources()] == [child]
for keyword in ("allOf", "anyOf", "oneOf"):
    resource = Resource.from_contents({keyword: [child]}, default_specification=DRAFT4)
    assert [item.contents for item in resource.subresources()] == [child]

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
original = copy.deepcopy(schema)
retrieval_attempts = []


def deny_remote(uri):
    retrieval_attempts.append(uri)
    raise NoSuchResource(ref=uri)


registry = Registry(retrieve=deny_remote)
validator = validator_for(schema)
validator.check_schema(schema)
assert validator(schema, registry=registry).is_valid("ok")
assert not validator(schema, registry=registry).is_valid(3)
payload = copy.deepcopy(schema)
AsyncGraphRuntime._embed_payload_references(payload)
emitted = controller_schema(
    Loop(
        id="L",
        node_ids=["draft", "critique"],
        controller_node_id="critique",
        continue_value="continue",
        exit_value="stop",
    )
)
emitted["properties"]["payload"] = payload
emitted["$schema"] = payload["$schema"]
validator = validator_for(emitted)
validator.check_schema(emitted)
envelope_validator = validator(emitted, registry=registry)
assert envelope_validator.is_valid({"payload": "ok", "control": {"decision": "stop"}})
assert not envelope_validator.is_valid({"payload": 3, "control": {"decision": "stop"}})
assert not envelope_validator.is_valid({"payload": "ok", "control": {"decision": "invalid"}})
assert schema == original
assert not retrieval_attempts
remote_uri = "https://cognitive-graph.invalid/forbidden-schema"
try:
    validator_for({})({"$ref": remote_uri}, registry=registry).validate("ok")
except Exception as error:
    denial_type = type(error).__name__
else:
    raise AssertionError("remote retrieval should fail")
assert retrieval_attempts == [remote_uri]
print(
    json.dumps(
        {
            "referencing": version("referencing"),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "engine_sha256": engine_hash,
            "original_and_emitted_good_bad": True,
            "invalid_control_rejected": True,
            "original_immutable": True,
            "draft3_and_draft4_crawling": True,
            "remote_retrieval_denied": denial_type,
        }
    )
)
