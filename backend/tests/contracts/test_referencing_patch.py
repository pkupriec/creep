"""Installed dependency behavior and shipped wheel/provenance integrity."""

import base64
import csv
import hashlib
import importlib.metadata
import io
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest
import referencing.jsonschema
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT3, DRAFT4

ROOT = Path(__file__).resolve().parents[3]
VENDOR = ROOT / "backend/vendor"
VERSION = "0.37.0+cg.1"
WHEEL = VENDOR / f"referencing-{VERSION}-py3-none-any.whl"


@pytest.mark.parametrize("as_array", [False, True])
def test_draft3_extends_crawls_one_or_many_schemas(as_array):
    child = {"id": "urn:cg:extends-child", "type": "string"}
    schema = {"id": "urn:cg:extends-root", "extends": [child] if as_array else child}
    resource = Resource.from_contents(schema, default_specification=DRAFT3)
    assert [item.contents for item in resource.subresources()] == [child]
    registry = Registry().with_resource("urn:cg:extends-root", resource).crawl()
    assert registry["urn:cg:extends-child"].contents == child


@pytest.mark.parametrize("keyword", ["allOf", "anyOf", "oneOf"])
def test_draft4_combinators_keep_array_traversal(keyword):
    children = [{"id": "urn:cg:first", "type": "string"}, {"id": "urn:cg:second"}]
    resource = Resource.from_contents({keyword: children}, default_specification=DRAFT4)
    assert [item.contents for item in resource.subresources()] == children
    registry = Registry().with_resource("urn:cg:root", resource).crawl()
    assert registry["urn:cg:first"].contents == children[0]
    assert registry["urn:cg:second"].contents == children[1]


@pytest.mark.parametrize("as_array", [False, True])
def test_default_mixed_dialect_validator_preserves_extends(as_array):
    extends = {"$ref": "#/definitions/Text"}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:cg:isolated-answer",
        "$ref": "#/definitions/Answer",
        "definitions": {
            "Text": {"type": "string"},
            "Answer": {
                "$schema": "http://json-schema.org/draft-03/schema#",
                "extends": [extends] if as_array else extends,
            },
        },
    }
    validator = validator_for(schema)
    validator.check_schema(schema)
    instance = validator(schema, registry=Registry())
    assert instance.is_valid("ok")
    assert not instance.is_valid(3)


def test_installed_distribution_matches_shipped_wheel_and_provenance():
    provenance = json.loads((VENDOR / "referencing-provenance.json").read_text())
    wheel = WHEEL.read_bytes()
    assert hashlib.sha256(wheel).hexdigest() == provenance["wheel_sha256"]
    assert provenance["upstream_sha256"] == (
        "381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231"
    )
    assert importlib.metadata.version("referencing") == VERSION
    source = Path(referencing.jsonschema.__file__).resolve()
    assert source.is_relative_to(Path(sys.prefix).resolve())
    assert not any(".f6-probe" in part for part in sys.path)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == provenance["patched_source_sha256"]
    with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
        assert archive.namelist() == sorted(archive.namelist())
        assert set(archive.namelist()) == set(provenance["members"])
        assert source.read_bytes() == archive.read("referencing/jsonschema.py")
        for info in archive.infolist():
            content = archive.read(info)
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3
            assert info.external_attr == 0o100644 << 16
            assert provenance["members"][info.filename] == {
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        record_name = f"referencing-{VERSION}.dist-info/RECORD"
        records = list(csv.reader(io.StringIO(archive.read(record_name).decode())))
        assert {row[0] for row in records} == set(archive.namelist())
        assert len(records) == len(archive.namelist())
        for name, digest, size in records:
            if name == record_name:
                assert digest == size == ""
                continue
            content = archive.read(name)
            expected = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
            assert digest == "sha256=" + expected.decode()
            assert size == str(len(content))
        license_text = archive.read(f"referencing-{VERSION}.dist-info/licenses/COPYING")
        assert b"Copyright (c) 2022 Julian Berman" in license_text
        assert b"Permission is hereby granted, free of charge" in license_text


def test_manifest_and_lock_pin_the_shipped_wheel():
    project = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
    lock = tomllib.loads((ROOT / "backend/uv.lock").read_text())
    provenance = json.loads((VENDOR / "referencing-provenance.json").read_text())
    relative = "vendor/" + WHEEL.name
    assert f"referencing=={VERSION}" in project["project"]["dependencies"]
    assert project["tool"]["uv"]["sources"]["referencing"] == {"path": relative}
    package = next(package for package in lock["package"] if package["name"] == "referencing")
    assert package["version"] == VERSION
    assert package["source"] == {"path": relative}
    assert package["wheels"] == [
        {"filename": WHEEL.name, "hash": "sha256:" + provenance["wheel_sha256"]}
    ]


def test_rebuild_rejects_wrong_hash_without_writing(tmp_path):
    upstream = tmp_path / "upstream.whl"
    upstream.write_bytes(b"untrusted input")
    output = tmp_path / WHEEL.name
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/rebuild_referencing.py"),
            "--input",
            str(upstream),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "upstream SHA256 mismatch" in result.stderr
    assert not output.exists()
    assert not (tmp_path / "referencing-provenance.json").exists()
