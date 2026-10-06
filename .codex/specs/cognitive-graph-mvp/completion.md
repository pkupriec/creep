# Cognitive Graph MVP — completion

2026-10-07: **implemented and verified**. Independent G6 PASS1/3 closes all
R01–R11/A01–A16 mandatory requirements and verification gates. G5 PASS2/3 closes
delivery; G0–G4 final independent results and user-authorized quota exceptions
remain recorded in [current-state.md](current-state.md) and [review.md](review.md).
Earlier completion snapshots remain available in Git (for example db6bcfd).

Delivered behavior:

- All-input asynchronous fan-in/fan-out, stable named-port order, explicit
  seeded disjoint feedback loops, conditional stop, strict controls and budgets:
  backend/app/runtime/ and backend/app/graphs/.
- Durable SQLite checkpoints, owner-specific opaque tool IDs, partial/full
  results, exact continuation replay, waiting-ID recovery and interruption of
  uncertain active calls; immutable run snapshots: backend/app/storage/,
  backend/app/tools/bridge.py.
- Virtual cg/<graph_id> and physical ollama/<model> models, full client history,
  final-only JSON/SSE, strict errors/authentication/size/namespace/global limits:
  backend/app/providers/, backend/app/api/, backend/app/main.py.
- React Flow graph CRUD/ports/prompts/feedback/import/export/publication,
  API-restored history/traces/status/cancellation/manual tool results:
  frontend/src/App.tsx, frontend/src/editor/, frontend/src/runs/.
- Two-service local Compose, one backend worker, loopback8000/8080, retained
  cg_data, unbuffered Nginx, pinned toolchains/dependencies and executable
  development/CI/smoke commands: compose.yaml, Dockerfiles, scripts/, docs/.
  Hermes executes tools externally; Ollama is external to Compose.

## Exact setup and launch

From PowerShell at D:/Sources/creep. Prerequisites: Docker Desktop Linux daemon
with WSL2 integration, external reachable Ollama and an already installed
text/function-tool-capable model. Native tooling pins Python3.11.15,
uv0.11.28, Node24.14.0/npm11.9.0. No global/model installation is implied.

```powershell
Set-Location D:/Sources/creep
$env:NODE_OPTIONS = '--use-system-ca'
python scripts/dev.py setup
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml config --quiet
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml up --build -d --wait
curl.exe --fail http://127.0.0.1:8080/health/ready
```

Open http://127.0.0.1:8080. Choose an installed physical model; create/import,
validate and publish a graph. Hermes custom provider uses chat_completions,
base URL http://127.0.0.1:8080/v1, model cg/<published_graph_id>; direct mode
uses ollama/<installed_model_name>. Optional CG_API_TOKEN protects both surfaces;
use the process environment and UI memory, never a URL/export.

Native alternative, two terminals:

```powershell
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:CG_DATA_DIR = Join-Path $PWD '.local-data'
python scripts/dev.py backend
# Second terminal:
python scripts/dev.py frontend
```

Full Windows/WSL2 smoke, backup and volume-preserving shutdown instructions:
[runbook](../../../docs/runbook.md). Current exact executed smoke argv,
timestamps, image/source/model pins and exits: [live summary](live-current-summary.json).
Test services were stopped; retained volumes/fixtures were not deleted.

## Verification and independent review

| Exact executed command | Exit | Outcome |
| --- | ---: | --- |
| uv --system-certs run --project backend --locked pytest backend/tests -q | 0 | 661 passed,45.11s |
| python scripts/dev.py test-runtime | 0 | 259 runtime/storage cases |
| python scripts/dev.py test-contract | 0 | 241 Python+9 frontend contracts |
| python scripts/dev.py lint | 0 | Ruff/52 formats/generated drift/both TS projects |
| npm --prefix frontend test | 0 | 21 unit cases |
| python scripts/dev.py test-e2e | 0 | Six real-native HTTP/SQLite/browser cases; mock upstream; restart and persistence |
| python scripts/dev.py build | 0 | TypeScript and production Vite bundle |
| uv --system-certs run --project backend --locked pytest backend/tests/delivery/test_compose_smoke.py -q | 0 | 11 no-effect lifecycle regressions, independently repeated |
| uv --system-certs run --project backend --locked pytest backend/tests/integration/test_acceptance.py backend/tests/api -q | 0 | Independent G6:52 passed,7.01s |

Real current-source Windows and WSL2 full Compose/Ollama/Hermes helpers both
exited0. Per platform: seven direct exchanges, native Hermes JSON/SSE two
fixture reads/two verified continuations per case, real waiting-ID restart,
compression28→6, completed history and volume recreation. Both29 application
files,22 package inventories and corrected wheel members were independently
reconciled. G5's later three-line cleanup-only correction exactly reverses to
the executed helper hash; no live effects were repeated merely for this fix.
Scoped down without -v and independent residue probes passed; own volumes retained.

Independent final budgets: G0 2/3,G1 4/4,G2 6/6,G3 5/5,G4 2/3,G5 2/3,G6 1/3,
all PASS. G1/G2/G3 exceeded original ceilings only through explicit user quota
exceptions, preserving every consumed attempt. G5 cycle1's reproduced verifier
failure is fixed, with original3 failing regressions retained as evidence.
G6 has zero blocking findings and one optional Low duration-label finding.
Proof boundaries and scenario closure: [acceptance](acceptance.md).

## Blockers, deviations and residual limitations

No mandatory blocker or live-validation gate remains open.

The exact local referencing0.37.0+cg.1 wheel corrects upstream Draft3 object-valued
extends crawling; its one-function patch, upstream/local hashes, license and
deterministic reproduction are recorded in backend/vendor/ and
scripts/rebuild_referencing.py. Engine and accepted schema profile remain unchanged.
WSL uses the existing pinned Windows-native Hermes via explicit interop, rather
than a Linux Hermes installation. Native Make was unavailable; equivalent pinned
Python wrapper targets ran. No requirement or acceptance criterion was weakened.

Optional G6-D1: “Active duration” in RunDetail.tsx labels elapsed wall time,
including tool waits; runtime budgets themselves are correct. Existing React Flow
handle/Vite bundle warnings remain. Hardware measurements are one sample per
shape, with no speedup guarantee; one WSL UTC node duration is unusable after
clock adjustment, raw evidence retained. Earlier unexplained Windows native test
exception remains historical/unassigned and is not declared fixed by later passes.

Remote GitHub CI, arbitrary user-data restore/cutover and native-Linux Hermes
were not run/claimed; isolated backup/restore evidence was independently accepted
within its stated scope. Native/browser deterministic tests use mock upstream;
real external inference/tools are separately proven by the live manifests.

Durable specification/evidence artifacts are versioned in local Git; product
files remain in the local working tree. No push/cloud deployment, team reinstall,
global reconfiguration, unneeded external MCP, secret access or user-data deletion.
Installed Sol/Astra model assignments remain intact; generic role-consuming
instances used user-requested medium reasoning without changing persisted profiles.
