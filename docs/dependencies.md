# Pinned application and development dependencies

G1 uses one backend uv project and one frontend npm project. No Hermes executor,
Ollama inference server, cloud resource, external MCP server or browser MCP is
installed/enabled by these dependencies. The already installed Codex team and
model assignments are preserved. Hermes/Ollama remain external prerequisites.

## Toolchains and setup

Verified native Windows versions: Python **3.11.15**, uv **0.11.28**, Node
**24.14.0**, npm **11.9.0**. `backend/.python-version` pins Python; Python's
project requirement is 3.11; frontend engines record exact Node/npm versions.
Use the project-local `backend/.venv`, `uv.lock` and `package-lock.json`.

From the repository root:

```powershell
$env:NODE_OPTIONS = '--use-system-ca'
python scripts/dev.py setup
python scripts/dev.py lint
python scripts/dev.py test-contract
python scripts/dev.py test
```

The system CA option verifies TLS through this host's installed CA; it does
not disable certificate checks. The wrapper uses `uv --system-certs sync
--project backend --locked --python 3.11.15` and `npm --prefix frontend ci`.
It propagates subprocess failures without ignoring them. `make <target>` runs
the identical `python scripts/dev.py <target>` command on systems with Make.
Set `PYTHON=python3` for Make if the interpreter executable is named python3.

Backend launch: `python scripts/dev.py backend` (one Uvicorn worker, loopback
8000). Frontend launch: `python scripts/dev.py frontend` (loopback 5173, proxy
/api, /v1 and /health to native backend). The composed FastAPI application and
UI entry point are implemented. Startup initializes SQLite and recovers runs
before readiness; shutdown joins runtime work and closes owned resources.
Actual native backend/SQLite browser scenarios and the production UI build
have executed, and G4 independent cycle 2 is PASS at 2/3. G3's medium-reasoning
attempt5 independently PASSed with zero findings. Current-source Windows and
WSL2 production Hermes/Ollama/Compose smokes passed with application and wheel
source equality. Independent G5 PASS2/3 and G6 PASS1/3 close mandatory acceptance;
native unit checks alone do not prove live behavior. See
[current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md) for status.
G2 attempt4 historically FAILed on F6: a valid modern-root/Draft3-child
single-extends schema failed after controller embedding. The F6 candidate
correction now uses exact local `referencing==0.37.0+cg.1`; 28 unmodified F6
runtime regressions pass in the production backend environment, with engine
source unchanged. Original F5 remains fixed and the accepted profile remains
unchanged. Independent G2 attempt6 PASS closes F1–F6; attempt5's quota failure
remains consumed. Current-source live Hermes/Ollama/Windows/WSL reconciliation
passed; G5 PASS2/3 and G6 PASS1/3 independently accepted the integrated proof.
Older images do not prove this dependency's runtime behavior. See
[the current acceptance status](api.md#f6-correction-and-independent-acceptance).
G1's cycle3 quota failure is retained historically; user-authorized attempt4
independently PASSed. Team models/pins remain unchanged. The latest explicit
retry used medium instead of high reasoning through generic instances consuming
installed role instructions; project role profiles remain unchanged.

All public environment names/defaults are in `contracts/config.py` and the
[specification](../.codex/specs/cognitive-graph-mvp/spec.md). Positive limits
are checked at startup; OLLAMA_BASE_URL requires HTTP(S) `/v1` without embedded
credentials/query/fragment. CG_API_TOKEN is optional, excluded from model
serialization and repr. WEB_CONCURRENCY other than 1 is rejected; explicit
launch workers are also fixed at one. Configuration is read at process startup
and changes require restart. No tokens are included in generated schemas.

| Environment variable | Default | Effect / format |
| --- | --- | --- |
| OLLAMA_BASE_URL | `http://host.docker.internal:11434/v1` | External HTTP(S) OpenAI-compatible upstream, no URL credentials |
| CG_DATA_DIR | `/data` | Persistent local graph/SQLite directory |
| CG_API_TOKEN | unset | Optional bearer token; excluded from serialized state/logs; token rotation changes caller namespace |
| CG_MAX_PARALLEL_LLM | 2 | Positive integer; one global graph/direct provider limit |
| CG_MAX_ACTIVE_RUNS | 4 | Positive integer; shared admitted graph/direct jobs, including waiting_tools |
| CG_MAX_QUEUED_RUNS | 20 | Positive integer; additional shared reserved queue positions |
| CG_LLM_TIMEOUT_SECONDS | 300 | Positive integer; each complete upstream exchange after acquiring permit |
| CG_RUN_ACTIVE_TIMEOUT_SECONDS | 1800 | Positive integer; run computing/draining/permit-wait wall time |
| CG_TOOL_WAIT_TIMEOUT_SECONDS | 1800 | Positive integer; separate fixed exposed-batch UTC TTL, including downtime |
| CG_MAX_NODE_EXECUTIONS | 100 | Positive integer; new LLM activations, not tool-result resumptions |
| CG_MAX_TOOL_ROUNDS | 20 | Positive integer; newly exposed external batches, not replay/partial results |
| CG_HISTORY_RETENTION_DAYS | 30 | Positive integer; terminal history only, never graphs/live mappings |

Explicit environment values override defaults, never client request values.
The external endpoint must be reachable from the actual backend environment;
native loopback success does not establish Docker/WSL2 reachability.

## Python pins

Actual available release metadata was queried from the official PyPI JSON
API `https://pypi.org/pypi/<package>/json` on 2026-10-03; installation and lock
resolution succeeded using uv0.11.28/Python3.11.15. Every direct dependency is
exactly pinned in pyproject.toml; uv.lock records exact transitive versions,
source URLs and artifact hashes. No unbounded install instruction is used.

| Dependency | Pin | Purpose |
| --- | --- | --- |
| fastapi | 0.142.2 | HTTP composition/API |
| pydantic | 2.13.5 | Strict DTOs, validation and JSON Schema |
| httpx | 0.28.1 | External Ollama HTTP and deterministic HTTP test transport |
| uvicorn | 0.54.0 | One-process ASGI server |
| pytest | 9.1.1 | Backend behavior/contracts/integration tests |
| pytest-asyncio | 1.4.0 | Async runtime/provider test fixtures |
| ruff | 0.16.10 | Python lint and formatting gates |
| jsonschema | 4.26.0 | Production final response-format validation and independent schema contract tests |
| referencing | 0.37.0+cg.1 | Exact local wheel correcting Draft3 single-schema extends crawling (G2 F6) |

`jsonschema==4.26.0` was promoted from the dev group to production to enforce
the final external response format, including legal input→output graphs with
no inference. Offline lock/sync preserved all transitive versions and artifact
records. Its locked dependencies are attrs 26.1.0,
jsonschema-specifications 2025.9.1, referencing 0.37.0+cg.1 and rpds-py 2026.6.3.
Validation uses installed local meta-schemas and a Registry that rejects
external retrieval; it never fetches schema resources or enables an extra
format checker. Unsupported dialects and unresolved references fail explicitly.

To reproduce this dependency reconciliation without updating pins:

```text
uv --system-certs lock --project backend --offline
uv --system-certs sync --project backend --locked --offline --python 3.11.15
```

The referencing wheel is supplied at
`backend/vendor/referencing-0.37.0+cg.1-py3-none-any.whl`. The direct exact pin
and relative `[tool.uv.sources]` path install it normally into backend/.venv;
no experiment PYTHONPATH or application monkeypatch is used. Its local SHA256
is `a84fbf0a7365b1a0592392a2859914de38f37258f1bca97d78fce582a102804c`.
The source is the previous locked upstream 0.37.0 universal wheel, SHA256
`381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231`.
Only the older-draft crawler's mapping-valued `extends`, necessary local
version metadata and RECORD change; all other upstream files, MIT COPYING
and unrelated locked package versions/artifacts are preserved. All 31 package
names remain; 29 unrelated package blocks are byte-identical, and the root
project metadata adds the direct referencing pin.

[Wheel provenance and reproduction](../backend/vendor/README.md) includes the
source URL, readable patch, all member hashes, deterministic archive settings
and rollback limitation. With that separately obtained upstream wheel,
verify byte-for-byte reproduction without writing:

```text
uv --system-certs run --project backend --locked python scripts/rebuild_referencing.py --input <upstream-wheel-path> --output backend/vendor/referencing-0.37.0+cg.1-py3-none-any.whl --check
uv --system-certs run --project backend --locked pytest backend/tests/contracts/test_referencing_patch.py -q
```

The stdlib-only script checks the upstream SHA256 before consuming the archive
and fails on nonmatching output/provenance. Native locked/offline sync,
deterministic rebuild and wrong-hash rejection executed successfully using
uv0.11.28/Python3.11.15. Contract tests cover Draft3 object/array extends,
Draft4 allOf/anyOf/oneOf, installed module/wheel/provenance/RECORD parity and
manifest/lock consistency. These owner checks do not assign an independent
review verdict or close the separate live validation gates.

The backend venv is resolved independently of research-only Hermes
dependencies. `app/contracts` imports no installed Hermes package or inference
server. Additional dependencies/manifests/locks remain the single bootstrap
owner's scope; peer owners request changes rather than changing these files.

## Frontend pins

React Flow and toolchain versions reuse the actual G0 pinned, tested package
metadata/provenance in [editor research](research/graph-editor.md). Production
omits the Rete comparison packages and auto-layout engines. Additional Ajv
8.18.0 availability/MIT license was checked with exact-version npm metadata.
All direct dependencies are exact versions; package-lock.json records exact
transitive tarball versions/integrity. npm clean install uses that lock.

| Dependency | Pin | Purpose |
| --- | --- | --- |
| @xyflow/react | 12.12.0 | MIT visual canvas; backend owns execution semantics |
| react / react-dom | 18.3.1 / 18.3.1 | Browser UI |
| @types/react / @types/react-dom | 18.3.31 / 18.3.7 | Strict React declarations |
| @types/node | 24.10.0 | Config/E2E declarations |
| typescript | 5.9.3 | Strict source and configuration type checks, skipLibCheck=false |
| vite | 8.3.2 | Local development and production static bundle |
| vitest | 5.0.3 | Contract and component tests |
| ajv | 8.18.0 | Python-generated draft2020-12 schema validation |
| @playwright/test | 1.61.1 | Production UI E2E test dependency; MCP remains disabled |

Playwright uses the existing cached Chromium/headless-shell revision 1228
(149.0.7827.55); G1 does not download browsers. On a clean host the pinned
package-local install is `npm --prefix frontend run browser:install`; that
download remains unexecuted here and is not a live validation claim.

## Executable gates and open later evidence

| Command (`python scripts/dev.py <target>`, or `make <target>`) | Claimed scope |
| --- | --- |
| setup | Locked isolated backend sync and clean frontend npm install |
| lint | Pinned Ruff lint/format, schema drift and strict frontend/config typecheck |
| test-contract | Generated schema drift, backend contracts plus provider/tools tests when present, frontend Ajv/type contract cases |
| test | All current backend tests and frontend unit/component tests |
| test-runtime / test-graphs | Required named backend suites; missing tests fail exit2 |
| test-e2e | Actual Playwright UI suite; missing config/main/specs fail exit2 |
| smoke-hermes | Dedicated production Hermes smoke script; missing script fails exit2 |
| smoke-compose | Actual production Compose smoke in WSL2/Linux; missing compose/script fails exit2 |
| build | Strict typecheck and Vite production build; missing UI entry fails exit2 |
| generate-contracts / check-contracts | Regenerate / byte-content consistency check of schema and TS |

Native verification includes contracts, API/runtime/provider tests, production
UI build and six real backend/SQLite browser scenarios with a mock upstream,
including process restart, durable tool IDs and authoritative same-ID reload.
Whole-request UTF-8 validation now rejects escaped unpaired surrogates with
400 before graph hashing/storage and preserves existing files on rejected PUT.
G4's independent cycle 2 is PASS at 2/3, closing both inspector-load and graph
Unicode findings. The API timing-test discrepancy was corrected only in tests:
a claim accepted before its fixed TTL waits to 504; a fresh submission after
persisted failure returns 409. Exact assertions, immutable checkpoint, deadlines
and effect counts are preserved; production chat is unchanged.

Latest terminal executable evidence (all exit 0, attributed to the respective
owners or independent G4 reviewer):

| Check | Result |
| --- | --- |
| Full backend, F6 bootstrap owner | 650 passed, 74.08s; includes all 28 F6 regressions and 10 patched-dependency contract checks |
| Runtime/storage, F6 bootstrap owner | 259 passed, 42.14s; actual scheduler/SQLite/recovery/replay coverage |
| Focused F6 / patched-dependency checks | 28 passed, 4.19s / 10 passed, 0.20s |
| Contract wrapper, F6 bootstrap owner | 241 Python plus 9 frontend contract tests passed; generated schema drift clean |
| Lint wrapper, F6 bootstrap owner | Ruff check, 51-file format, generated drift and both TypeScript projects passed |
| Affected provider suite | 109 passed, 5.38s; includes 65 added Unicode regressions |
| Focused G3 contract/provider/tool/API/integration checks | 277 passed, 20.07s |
| Focused API/integration timing seam | 49 passed, 6.99s |
| Frontend / graph suites | 21 / 98 passed |
| Actual-backend browser scenarios | Six passed, 15.3s; mock upstream, real HTTP/file/SQLite/process restart |

The original historical 475-case wrapper run with an unidentified failure and
Windows native exception remains unreproduced and unassigned. Later passing
runs do not diagnose that exception. No full-MVP verification is claimed.

Production builds retain Python 3.11.15, 22 locked production packages,
jsonschema 4.26.0 and Linux SQLite 3.40.1; the frontend uses strict TypeScript
and Vite with retained approximately 509 KB bundle/directive warnings. Build
proof is distinct from startup, external Ollama, Hermes or restart proof.
[Delivery verification](verification.md) is the current live authority and
records exact project/source/image hashes and executed phases. Earlier-provider
Windows images exercised healthy services, the default container-to-Ollama
route, seven real public direct JSON/SSE/multiturn/native-tool-request/manual-
result exchanges with zero executed tools, Nginx protections and history/volume
restart subsets. Target diamond/sequential measurements make no speed promise.
That whole Windows helper failed its original Hermes observation assertions;
its waiting-ID restart/replay and streamed Hermes phases were unexecuted.
The authentic SDK-factory observer's offline proof is not a complete live smoke.
Those historical subsets cannot establish current Unicode-corrected image
behavior. Subsequent full corrected-source Windows and WSL2 smokes passed,
including original Hermes JSON/SSE/waiting restart/replay/compression. WSL used
the existing native Windows client via explicit interoperability, without
installing Linux Hermes. G1 attempt4 and G3 attempt5 independently PASSed after
explicit user exceptions; delivery/integration reviews independently PASSed. G2 attempt4
historically FAILed on F6 despite original F5 closure; the local dependency
correction independently PASSed at attempt6. Current-source live reconciliation
passed on both platforms with installed wheel equality. Follow
[current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md) for G5/G6
accepted reviews and the live authority for exact source-scoped evidence; old smokes
do not prove the corrected dependency or waive review.
