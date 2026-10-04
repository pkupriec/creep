# Cognitive Graph MVP completion report — 2026-10-04

## Outcome

The local implementation and complete corrected-source Windows/WSL2 production
smokes are delivered. Whole-MVP acceptance is **BLOCKED**, with no completion
or final independent PASS claim. All R01–R11, A01–A16 and G0–G6 identifiers and
the accepted product profile remain unchanged.

- **G2-runtime BLOCKED3/3:** terminal independent FAIL F5; valid Draft3
  schema-valued extends/type local references are omitted by controller-schema
  embedding, causing upstream_error. Prior F1–F4 are closed. The accepted
  schema is not reclassified as unsupported; no automatic fix/fourth review.
- **G1-contracts PASS4/4:** the user-authorized additional review attempt
  produced the authoritative PASS with zero findings. The original cycle3
  quota failure remains historical evidence; no fifth attempt is allowed.
- **G3-proxy BLOCKED3/3:** cycle1 and cycle2 findings are corrected and
  regression-tested; the reserved terminal cycle3 reviewer immediately hit the
  account usage limit and produced no verdict. Current image evidence does not
  substitute for that independent gate.
- **G0-research and G4-ui PASS2/3.** G5/G6 independent reviews remain OPEN0/3;
  the delivery owner’s logical backup/restore audit is evidence, not a review.

The installed team plugin/workflow/custom roles were verified before work, with
16 maintained files matching installed0.1.0-creep.3 and reviewed baseline
90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6. No reinstall/update/configuration change.
Setup's Solhigh lead/coding/DevOps and Astrahigh review/SA matrix is preserved.
Session approval/exposed-connector mismatch was recorded; no external connector
or automatic tool approval was enabled for this workflow.

## Delivered behavior and important files

- `backend/app/runtime/engine.py`, `admission.py`, `clock.py`: asynchronous
  lexical all-input fan-in, fan-out, optional-null named inputs, seeded explicit
  loops with strict conditional termination, separate timing/node/tool budgets
  and shared graph/direct admission/inference limits. The F5 exception above
  remains a required known defect.
- `backend/app/storage/repository.py`, `events.py`: serialized SQLite WAL/FK/
  FULL transactions, CAS/claims/checkpoints/tool mappings, persisted events,
  immutable run snapshots, exact continuation replay, waiting-ID recovery
  and interruption of uncertain active calls without rerun.
- `backend/app/providers/ollama.py`, `sse.py`; `tools/bridge.py`; `api/chat.py`,
  `runs.py`, `models.py`, `security.py`, `main.py`: physical/virtual models,
  strict JSON/SSE/tool/error semantics, byte-correct bounded UTF-8 streaming,
  sanitized invalid upstream data, opaque owner IDs, latest-segment routing,
  fixed TTL/partial results/replay, auth namespace and request limits. Tools
  execute only in external Hermes; Ollama stays external.
- `backend/app/graphs/repository.py`, `validator.py`, `api/graphs.py`, `examples/`:
  safe atomic graph files, expected revisions, immutable publications, topology/
  port/loop/controller/seed validation and whole-request UTF-8 rejection.
- `frontend/src/App.tsx`, `editor/`, `runs/`, `api/client.ts`: React Flow CRUD/
  ports/prompts/generation/tools/feedback editing, import/export/publish/conflict
  handling, named test runs, durable trace/history/status/manual tools/cancel,
  API reload and authenticated fetch SSE with in-memory token/cursor handling.
- `backend/app/contracts/`, `frontend/src/contracts/`, manifests/locks,
  `scripts/dev.py`, `export_contracts.py`, `Makefile`: one shared contract source,
  generated drift checks and isolated exact-pinned toolchains.
- `compose.yaml`, Dockerfiles, `frontend/nginx.conf`, pinned CI workflow, smoke
  helpers and `docs/`: two production services, localhost8000/8080, retained
  cg_data volume, one backend worker, non-root/read-only/capdrop containers,
  unbuffered proxy; exact original-Hermes live smoke and runbook.

Product files remain in the local working tree. Durable specification/research/
live-evidence artifacts are versioned in Git. No push, cloud deployment, global
installation, installed Hermes/Ollama change or user-data deletion occurred.

## Exact setup and launch

Observed toolchain: Python3.11.15, uv0.11.28, Node24.14.0, npm11.9.0; Docker
Desktop Linux daemon/WSL2 integration. External Ollama0.33.3 and an already
installed text/function-tool capable model are prerequisites. The tested model
is gemma4:12b, digest4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c.

PowerShell, repository root:

```powershell
Set-Location D:/Sources/creep
$env:NODE_OPTIONS = '--use-system-ca'
python scripts/dev.py setup
$env:OLLAMA_BASE_URL = 'http://host.docker.internal:11434/v1'
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml config --quiet
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml up --build -d --wait
curl.exe --fail http://127.0.0.1:8080/health/ready
```

UI: http://127.0.0.1:8080; API: http://127.0.0.1:8000. Import an example, select
your installed physical base model, validate/save/publish. Hermes custom
provider uses chat_completions, base_url http://127.0.0.1:8080/v1 and
model cg/synthesis; direct mode uses ollama/gemma4:12b. Optional CG_API_TOKEN
is supplied through the process environment and UI memory, never URLs/files.

For native development, use two terminals after setup:

```powershell
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:CG_DATA_DIR = Join-Path $PWD '.local-data'
python scripts/dev.py backend
# Second terminal, same repository:
python scripts/dev.py frontend
```

Native UI: http://127.0.0.1:5173. Compose needs its reachable container URL
shown above, not the native loopback value. See docs/runbook.md for explicit
Windows/WSL and fresh-project smoke commands, backup and retained-volume teardown.

## Exact verification evidence

All rows below inspected terminal exit0; owner/reviewer attribution is explicit.

| Command | Outcome / source |
| --- | --- |
| `uv --system-certs run --project backend --locked pytest backend/tests -q` | 593 passed39.70s after one unrelated timing-sensitive admission assertion was rerun alone and passed |
| `uv --system-certs run --project backend --locked pytest backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py backend/tests/contracts -q` | 283 passed15.03s after the G3 F3 correction |
| `uv --system-certs run --project backend --locked pytest backend/tests/providers/test_ollama.py backend/tests/api/test_chat.py -q` | 61 passed3.68s; strict high/low surrogate rejection and valid supplementary-ID regression coverage |
| `python scripts/dev.py test-contract` | 231 backend/provider/tool plus nine frontend/generated drift checks, exit0 |
| `python scripts/dev.py test-graphs` | 98 passed3.63s, independent G4 cycle2 |
| `npm --prefix frontend test` | 21 passed, independent G4 |
| `npm --prefix frontend run typecheck` and `npm --prefix frontend run build` | Strict TS and production509.13kB bundle, independent G4 |
| `npm --prefix frontend run test:e2e` | Six real-backend Chromium scenarios15.3s, independent G4; actual HTTP/file/SQLite/process restarts with mock Ollama |
| `python scripts/dev.py lint` | Current Ruff49formats/generated drift/both TypeScript projects, coordinator |
| Configured Ruff check/format-check on `scripts/smoke_compose.py` | 0 after narrow root native-metadata guard correction |
| Actual extracted-helper guard through WSL native interpreter | 0, exact pinned native client versions/equal Docker daemon IDs; wsl-client-guard.json |

G3 regression-first selector failed32/passed20 before correction, then passed52;
subsequent coverage brought65 new cases. Meaningful API expiry barriers prove
accepted waiting requests504 at their original deadline and new requests after
persisted terminal failure409, without TTL extension/new inference/state mutation.

Complete actual Windows smoke, terminal0:

```powershell
python scripts/smoke_compose.py --context desktop-linux --project cg-smoke-win-final-20261004-5f34c9e2 --model gemma4:12b --reasoning-effort none --hermes-python D:/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent
```

Complete actual WSL smoke, terminal0:

```powershell
python scripts/dev.py smoke-compose --project cg-smoke-wsl-final-20261004-369c51ea --model gemma4:12b --reasoning-effort none --hermes-python /mnt/d/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root /mnt/c/Users/pkupr/AppData/Local/hermes/hermes-agent --hermes-docker-context desktop-linux
```

Use new project IDs when reproducing: original volumes/fixtures are retained.
WSL invokes the original Windows-native client explicitly outside Compose; it
is not a claim that Linux Hermes was installed/tested. Both smokes assert real
Ollama/container route/current source equality, API/static UI/readiness, seven
public JSON/SSE/multiturn/native-tool-request/manual-result exchanges, Nginx
streaming/protection/timeouts, completed-history restart and same-volume
recreation. Native Hermes JSON cg/synthesis and SSE each make3 original SDK
calls,2 guarded native reads,2 exact replays, ending3 node executions/5 upstream
attempts/2 tool rounds. Actual waiting-ID backend restart occurs before effects;
original run/IDs/owners/checkpoints/counters persist. Real compression28→6
preserves pending IDs and raw results. All19 exercised native source/guard
files match pinned Hermes SHAcaed552de1c8a8f9983bc555512412a1ac0e0a9e after
normalization; dirty installed checkout is untouched.

Versioned live-windows-compose.json/live-windows-hermes.json and
live-wsl-compose.json/live-wsl-hermes.json contain exact image/source/run IDs
and measurements. Current Windows diamond/sequential1.563s/1.719s; WSL1.534s/
1.510s. Each3 calls, one sample per shape; no speedup promise. Successful
smokes scoped down(no-v)0, no own container/network residue, volumes retained.

## Remaining blockers, deviations and residual risk

- Required G2 format preservation is BLOCKED3/3 as above; its automatic
  fix/review loop stops. G1 is PASS4/4 through the explicit user exception.
- G3 terminal re-review is BLOCKED3/3 because its reviewer could not complete
  under the account usage limit; G5/G6 initial independent reviews remain
  OPEN0/3. Runtime/API/live successes do not substitute for those verdicts.
- Operator backup/restore drill and actual remote GitHub CI remain unexecuted;
  documented procedures/local equivalents are not labeled live PASS.
- Earlier unreproduced Windows native test exception remains unassigned despite
  later green suites. Bundle/React Flow warnings remain optional notices.
- Native GNU Make is unavailable; exact pinned Python wrapper targets executed
  instead. No global Make installation.
- No requirements/profile were relaxed or product scope expanded. Already
  pinned jsonschema4.26.0 moved from dev to production to enforce required
  native final-format constraints; all30 external lock versions/URLs/hashes
  stayed identical.
- Nginx writable temp paths, explicit smoke instruction, original SDK observer
  and WSL metadata guard were corrected from reproducible failures. Historical
  failures remain preserved; no retry-until-green/effect replay/model fallback.
- After confirmed agent quota termination, root performed existing local WSL
  validation and one narrow helper guard/status-documentation recovery; no
  broad implementation takeover or model reconfiguration.

Current requirements/spec/design/tasks/decisions/acceptance/review artifacts
are the source of truth. review.md preserves reviewer-authored verdicts only;
no G3cycle3 verdict was fabricated after its agent failed. G1cycle4 is the
explicit user-authorized exception and is exhausted at PASS4/4. User
disposition is required for the exhausted G2/G3 gates.

## Final evidence audit

Coordinator final UTF8/whitespace/local-link/JSON/source audit terminal0:
10 documentation/ledger files,34 actual local links, current Windows and WSL
backend source hashes, four original Hermes cases and all11 requirements/
16 scenarios/seven non-resetting group counters verified. git diff --check0.
final-residue-audit.json records fresh read-only Docker/Windows/WSL queries:
no containers/networks for either successful smoke or failed initial WSL
project, no localhost8000/8080/5173 listeners or owned final smoke process.
Volumes remain retained; unrelated resources are preserved. Agent inventory
confirmed only root active, with all requested workers completed/errored.

## Historical usage recovery record

The user reported refreshed account usage and explicitly authorized one
additional G1 review attempt only. Historical attempts1–3 remain consumed;
G1 cycle4 subsequently returned PASS4/4, with no automatic fifth attempt.
G2 F5 remains BLOCKED3/3 and runtime unchanged. The resumed G3 terminal
review subsequently hit the account limit and returned no verdict; G3 is
BLOCKED3/3. The delivery owner’s logical backup/restore drill is retained as
owner evidence, while G5/G6 independent reviews remain OPEN0/3. Reservation
and exact ownership are in tasks.md/decisions.md at cfa1214 and the later
terminal entries.
