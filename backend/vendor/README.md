# Local referencing correction

`referencing-0.37.0+cg.1-py3-none-any.whl` fixes G2 F6 in the existing
referencing 0.37.0 dependency. Draft 3 permits `extends` to be one schema or
an array. The older-draft subresource crawler incorrectly iterates mapping
keys when the value is one schema. The patch yields that mapping once;
array-valued `extends` and all other keywords retain upstream traversal.
The helper is shared with Draft 4, whose allOf/anyOf/oneOf behavior is tested.
Application schemas, accepted dialects and runtime source are unchanged.

Source is the exact previously locked [upstream universal wheel](https://files.pythonhosted.org/packages/2c/58/ca301544e1fa93ed4f80d724bf5b194f6e4b945841c5bfd555878eea9fcb/referencing-0.37.0-py3-none-any.whl),
SHA256 `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231`.
This is wheel-derived runtime source, not a complete upstream checkout.
Upstream MIT COPYING (Copyright 2022 Julian Berman), test files, type markers,
WHEEL metadata and dependencies are retained byte-for-byte. All 19 members
are retained; only jsonschema.py, METADATA's local version, and regenerated
RECORD contents differ. The dist-info directory is renamed for the local
version, including the unchanged COPYING and WHEEL members.

Local wheel SHA256:
`a84fbf0a7365b1a0592392a2859914de38f37258f1bca97d78fce582a102804c`.
Patched `referencing/jsonschema.py` SHA256:
`d71d7e00650fa3411b1957b1517d95a515461d7d428753eaf7a2719c10482c86`.
[Provenance](referencing-provenance.json) records the complete readable patch,
member delta and per-member hashes/sizes. Archive ordering is sorted;
timestamps are 1980-01-01, permissions 100644, compression ZIP_STORED.

From the repository root, with a separately obtained exact upstream wheel:

```text
uv --system-certs run --project backend --locked python scripts/rebuild_referencing.py --input <upstream-wheel-path> --output backend/vendor/referencing-0.37.0+cg.1-py3-none-any.whl --check
```

Remove `--check` to rebuild the wheel and sibling provenance. The stdlib-only
script verifies the input SHA256 before opening/patching it, requires exact
patch context, and fails on nonmatching wheel/provenance in check mode without
writing. It performs no downloads and needs no new build dependencies.
Reproduction is byte-identical using pinned Python 3.11.15. Setup installs the
exact wheel through pyproject.toml's relative uv source and uv.lock hash:

```text
uv --system-certs sync --project backend --locked --offline --python 3.11.15
uv --system-certs run --project backend --locked pytest backend/tests/contracts/test_referencing_patch.py -q
```

Native installation, wheel/provenance parity and original/emitted mixed-dialect
runtime tests are verified by the bootstrap owner and independent G2 attempt6
PASS. Attempt5's quota termination remains historical. Source-matched live
Hermes/Ollama reconciliation and G5/G6 reviews subsequently PASSed. Removing the
direct pin/source and restoring the old referencing lock entry reopens F6.
Maintainers must re-evaluate this patch against any explicitly approved future
upstream dependency revision rather than silently upgrading or dropping it.
