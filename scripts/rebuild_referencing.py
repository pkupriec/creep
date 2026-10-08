"""Reproduce the scoped referencing wheel from its hash-verified upstream wheel."""

import argparse
import base64
import csv
import difflib
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

UPSTREAM_VERSION = "0.37.0"
LOCAL_VERSION = "0.37.0+cg.1"
UPSTREAM_SHA256 = "381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231"
UPSTREAM_URL = (
    "https://files.pythonhosted.org/packages/2c/58/"
    "ca301544e1fa93ed4f80d724bf5b194f6e4b945841c5bfd555878eea9fcb/"
    "referencing-0.37.0-py3-none-any.whl"
)
WHEEL_NAME = f"referencing-{LOCAL_VERSION}-py3-none-any.whl"
OLD_INFO = f"referencing-{UPSTREAM_VERSION}.dist-info"
NEW_INFO = f"referencing-{LOCAL_VERSION}.dist-info"
SOURCE = "referencing/jsonschema.py"
TIMESTAMP = (1980, 1, 1, 0, 0, 0)
OLD = """        for each in in_subarray:
            if each in contents:
                yield from contents[each]
"""
NEW = """        for each in in_subarray:
            if each in contents:
                value = contents[each]
                if each == "extends" and isinstance(value, Mapping):
                    yield value
                else:
                    yield from value
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_source(original: bytes) -> bytes:
    text = original.decode("utf-8")
    start = text.index("def _subresources_of_with_crazy_aP_items_dependencies(")
    end = text.index("\ndef _maybe_in_subresource(", start)
    section = text[start:end]
    if section.count(OLD) != 1:
        raise ValueError("unexpected upstream crawler patch context")
    return (text[:start] + section.replace(OLD, NEW) + text[end:]).encode("utf-8")


def rebuild(upstream: bytes) -> tuple[bytes, dict]:
    if sha256(upstream) != UPSTREAM_SHA256:
        raise ValueError("upstream SHA256 mismatch; no output written")
    with zipfile.ZipFile(io.BytesIO(upstream)) as archive:
        original = {name: archive.read(name) for name in archive.namelist()}
    members = {}
    delta = []
    for old_name, data in original.items():
        name = old_name.replace(OLD_INFO + "/", NEW_INFO + "/", 1)
        before = data
        if old_name == SOURCE:
            data = patch_source(data)
        elif old_name == OLD_INFO + "/METADATA":
            old_version = f"\nVersion: {UPSTREAM_VERSION}\n".encode()
            if data.count(old_version) != 1:
                raise ValueError("unexpected upstream version metadata")
            data = data.replace(old_version, f"\nVersion: {LOCAL_VERSION}\n".encode())
        elif old_name == OLD_INFO + "/RECORD":
            continue
        members[name] = data
        if name != old_name or data != before:
            delta.append({"upstream": old_name, "local": name, "content_changed": data != before})

    record_name = NEW_INFO + "/RECORD"
    rows = []
    for name, data in sorted(members.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.append((name, "sha256=" + digest, str(len(data))))
    rows.append((record_name, "", ""))
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    members[record_name] = record.getvalue().encode()
    delta.append({"upstream": OLD_INFO + "/RECORD", "local": record_name, "content_changed": True})

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, TIMESTAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    wheel = output.getvalue()
    patch = "".join(
        difflib.unified_diff(
            original[SOURCE].decode().splitlines(True),
            members[SOURCE].decode().splitlines(True),
            fromfile=SOURCE + " (upstream)",
            tofile=SOURCE + " (local)",
        )
    )
    provenance = {
        "upstream_version": UPSTREAM_VERSION,
        "local_version": LOCAL_VERSION,
        "upstream_url": UPSTREAM_URL,
        "upstream_sha256": UPSTREAM_SHA256,
        "wheel_filename": WHEEL_NAME,
        "wheel_sha256": sha256(wheel),
        "source": "wheel-derived runtime source; not a full upstream checkout",
        "reason": "F6: Draft3 mapping-valued extends must yield one schema during crawling",
        "patch": patch,
        "member_delta": sorted(delta, key=lambda item: item["upstream"]),
        "members": {
            name: {"sha256": sha256(data), "size": len(data)}
            for name, data in sorted(members.items())
        },
        "upstream_source_sha256": sha256(original[SOURCE]),
        "patched_source_sha256": sha256(members[SOURCE]),
        "zip": {"compression": "ZIP_STORED", "timestamp": list(TIMESTAMP), "mode": "100644"},
        "license": "MIT; upstream COPYING retained byte-for-byte",
    }
    return wheel, provenance


def provenance_bytes(provenance: dict) -> bytes:
    return (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Exact upstream wheel path")
    parser.add_argument("--output", type=Path, required=True, help="Local wheel path")
    parser.add_argument("--provenance", type=Path, help="Defaults to output directory provenance")
    parser.add_argument("--check", action="store_true", help="Compare without writing any output")
    args = parser.parse_args()
    provenance_path = args.provenance or args.output.parent / "referencing-provenance.json"
    try:
        wheel, provenance = rebuild(args.input.read_bytes())
        metadata = provenance_bytes(provenance)
        if args.output.name != WHEEL_NAME:
            raise ValueError(f"output filename must be {WHEEL_NAME}")
        if args.check:
            if args.output.read_bytes() != wheel:
                raise ValueError("local wheel differs from deterministic reproduction")
            if provenance_path.read_bytes() != metadata:
                raise ValueError("provenance differs from deterministic reproduction")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(wheel)
            provenance_path.write_bytes(metadata)
        print(f"{'Verified' if args.check else 'Built'} {WHEEL_NAME} SHA256 {sha256(wheel)}")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
