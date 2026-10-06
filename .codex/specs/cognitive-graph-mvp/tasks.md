# Cognitive Graph MVP tasks

> Coordination shortcut: read [`current-state.md`](current-state.md) first.
> This file retains the complete historical task ledger; do not reread it for
> routine status checks.

Authority: root specification v1.1, section 12; requirement IDs R01–R11 and scenarios A01–A16 remain unchanged.
Main thread owns artifacts, research consolidation, decisions, and orchestration. No main implementation begins before G0 passes.

## Stable groups and non-resetting review budgets

G5 cycle1 FAIL harvested (review.md2388): Medium F1 direct-only early return
swallows cleanup-only failures; full successful live runs remain valid. Low D1
stale delivery status. Fix wave1 owners, all other files read-only:
coding_g5_fix: scripts/smoke_compose.py and new
backend/tests/delivery/test_compose_smoke.py, serial transfer from released
bootstrap/delivery owners; minimal error propagation and no-effect success,
down failure, residue failure, combined primary/cleanup regression coverage.
devops_g5_docs: docs/runbook.md, docs/hermes-compatibility.md,
docs/dependencies.md, docs/verification.md only; reconcile exact D1 locations,
retain history and live evidence, current-state pointer. Both consume F1/D1
and frozen semantics, no inference/tools/resource effects/manifest edits.
Run locked targeted pytest/Ruff + wrapper lint/test gates as relevant; docs
UTF8/local-link audit. Root waits BOTH terminal results before cycle2 review;
no review reservation yet, budget remains1/3. Peer writers are file-disjoint.

2026-10-06 current wave: G2 PASS6/6 and devops_live_compact terminal success
harvested. Both current full Windows/WSL2 helpers exited0; source/wheel equality,
real Hermes continuation/restart/replay/compression, and scoped teardown proven.
Evidence: live-current-summary.json and its four referenced JSONs. Timing is
one sample, with an unusable individual WSL wall-clock duration; no speed claim.

G5-delivery cycle1 reservation (consumed1/3 before spawn): review_g5_compact,
generic Astra/medium consuming installed review-agent role, sole synthesizer.
Writes review.md append only; exact read-only delivery slice: compose.yaml,
.env.example, .dockerignore, backend/Dockerfile, frontend/Dockerfile,
frontend/nginx.conf, .github/workflows/ci.yml, Makefile, scripts/dev.py,
scripts/smoke_compose.py, scripts/smoke_compose.sh, scripts/smoke_hermes.py,
README.md, docs/runbook.md, docs/verification.md, docs/hermes-compatibility.md,
docs/dependencies.md, current live/UI/F6 evidence and referenced prior proofs.
Acceptance: R10/A01/A07/A10/A15/A16 delivery subsets; frozen configuration,
external tools/Ollama, exact pins, safe lifecycle/backup docs and CI adequacy.
Run relevant pinned focused checks; evaluate actual source-matched live proof,
do not repeat inference/tool effects solely for review. No other writer edits
the slice; root waits terminal independent verdict before consolidation/G6.
All prior reservation/wave prose below is historical.

G2 attempt6 result harvested: independent PASS in review.md2198+, F1–F6 closed.
Root reconciled Low D1 status prose in README.md, docs/api.md,
docs/dependencies.md and backend/vendor/README.md (exact documentation-only
ownership); reviewed code/dependency20 non-MD hashes remain unchanged.
Current UI tests/build are recorded once in current-ui-evidence.json.
Live worker remains active; this is individual G2 harvesting, not wave closure.

Active delivery validation: `devops_live_compact` owns only new
live-current-windows-compose.json, live-current-windows-hermes.json,
live-current-wsl-compose.json, live-current-wsl-hermes.json,
live-current-summary.json under this directory, docs/verification.md and
docs/runbook.md, plus ignored .codex/.cache/current-live/ logs/fixtures.
Read-only preflight now; execute unique-project Windows then WSL full smoke
after G2 PASS signal. R10/A01/A02/A07/A09/A10/A11/A15/A16 and current source /
patched-dependency identity must be proven. Existing scripts are read-only;
no model/global installs, inference/tool caching/retries, existing resources
or data deletion. Exact commands from runbook208–244, child-local explicit
endpoint/model/client/context. Return parsed phase evidence/exit/image/source
hashes and residue, preserve historical JSON, label any unrun gate OPEN.
Root waits both agents before consolidation; source/docs in G2 review stay
unchanged during review.

Active reservation 2026-10-06: `review_g2_compact` is sole synthesizer for
G2-runtime attempt6, authorized by user's "Ok. Now with shorter context plz
proceed" after the missing verdict/retry requirement was explained. Writes:
review.md append only. Read-only exact scope: the24 file keys in
g2-f6-evidence.json/stable_implementation_source_sha256. Check F1–F6 and G2
module acceptance A03–A06/A08–A10/A13–A14/A16; evaluate current locked evidence,
run focused regressions and any necessary pinned checks. Consume6/6 before
spawn, preserve all prior cycles; no seventh attempt/fix automatically.
Expected output: independent findings, commands/exits, PASS/FAIL and remaining
separate live/G5/G6 gates. Root waits terminal result; no concurrent review
writer. Other owners may perform disjoint live preflight without product edits.

| Group | Outcome | Dependency | State | Synthesizer spawns consumed |
| --- | --- | --- | --- | --- |
| G0-research | Proven Hermes continuation and editor choice | None | PASS | 2/3 |
| G1-contracts | Frozen schema/API/scheduler/continuation contracts | G0 | PASS: user-authorized quota-recovery attempt 4 | 4/4 (one explicit user exception) |
| G2-runtime | DAG, loops, durable state/recovery | G1 | PASS: attempt6 closes F1–F6 | 6/6 (three explicit user review exceptions) |
| G3-proxy | Ollama, Hermes tool bridge, JSON/SSE | G1; integrate G2 | PASS: user-authorized medium-reasoning attempt 5 | 5/5 (two explicit user exceptions) |
| G4-ui | Editor, files API, history/traces | G1; integrate G2/G3 | PASS: cycle 2 closes F1/F2 | 2/3 |
| G5-delivery | Compose, CI, runbooks | G1; smoke G2–G4 | Cycle1 FAIL F1; scoped fix wave1, full live PASS retained | 1/3 |
| G6-integration | A01–A16, real Hermes/Windows/WSL2 | G2–G5 | Current deterministic/UI/live proof delivered; independent review OPEN | 0/3 |

G-TEAM-SETUP is a separate, previously exhausted 3/3 PASS group. No setup reviewer is respawned.
Each product group has its own maximum three synthesizer spawns. Record consumption before spawn. Cycle 3 non-PASS is terminal.

## Wave 0 — research

All three named workers must return before consolidation. No recursive delegation. Peer work is concurrent; never revert peer changes.

- [x] [coding] `coding_rd1`, G0/RD1: prove pinned installed Hermes continuation. Writable files only: `experiments/hermes_bridge.py`, `experiments/test_hermes_bridge.py`, `experiments/hermes-requirements.txt`, `experiments/hermes-traces.json`, `docs/research/hermes-protocol.md`. No edits to Hermes installation/configuration, product code, other artifacts, or dependency manifests. Consume actual installed Hermes protocol at immutable SHA; produce prototype two-node tool continuation, two owners/ID collisions, replay/restart proof and sanitized real traces. A07–A10 research obligations; inspect compression/ID handling/timeouts/iteration limits/streaming. Run: repository-local isolated Python `-m pytest experiments/test_hermes_bridge.py`; document exact interpreter/commands in report. A fake client alone cannot close RD1. Coordinate live Ollama endpoint with `devops_env`; never read secrets or execute tools outside a dedicated test directory. Return exact files, pins, commands/exits, evidence and blockers.
- [x] [coding] `coding_rd2`, G0/RD2: compare existing editors. Writable files only: `experiments/editor/package.json`, `experiments/editor/package-lock.json`, `experiments/editor/tsconfig.json`, `experiments/editor/index.html`, `experiments/editor/src/main.tsx`, `experiments/editor/src/style.css`, `experiments/editor/src/graph.ts`, `experiments/editor/src/graph.test.ts`, `experiments/editor/playwright.config.ts`, `experiments/editor/e2e/editor.spec.ts`, `docs/research/graph-editor.md`, `docs/research/graph-editor.png`. Own these experiment manifests/lockfile only. No product or shared-contract edits. Consume unchanged R04/R05/R08 and RD2; produce diamond, named ports, feedback, membership/seed, prompt edits, JSON round-trip proof, license/version comparison and selection recommendation. Run: `npm --prefix experiments/editor ci`, typecheck/unit/build and pinned Playwright E2E exact scripts; record exits/screenshot. Existing disabled Playwright MCP must remain disabled; use project test dependency only. Return pins, files, commands, recommendation, blockers.
- [x] [devops] `devops_env`, G0 environment evidence: writable only `docs/research/environment.md`. Inspect available Python/Node/Docker/Compose/WSL2/Hermes and external Ollama reachability/version/model inventory using bounded read-only queries, including WSL2 host addressing. No Compose/product/bootstrap/config changes, no model downloads, no credential access, no deployment, no global installs. Consume R10/A15 environment constraints; produce exact safe endpoints and version/runtime evidence to RD1 and coordinator. Run: `docker version`, `docker compose version`, `wsl --list --verbose`, bounded GET Ollama version/tags/models on loopback/reachable documented addresses; record independent command exits. Return missing facts and exact live-validation procedure if unavailable.

## Later waves

## G0 fix wave 1 — cycle 1 findings

- [x] [coding] `coding_g0_fix1` owns ONLY `experiments/hermes_bridge.py`, `experiments/test_hermes_bridge.py`, `experiments/hermes-traces.json`, `docs/research/hermes-protocol.md`. Address G0 cycle 1 Medium findings: immutable wire request/response trace snapshots; replay mismatch and changed execution/delivery counters must fail nonzero. Add regression tests for both defects, re-run pinned actual-Hermes suite/Ruff and documented live two-owner SSE/reconstruction/compression/serial experiment with unique dedicated directory, regenerate truthful aggregate traces/current source hashes. Preserve historical failed evidence and all source pins. No product/config/editor/dependency/spec/review edits, no change in semantics or scope. Required proof: trace remains byte/content-equivalent to wire after history mutation; injected false replay/counter changes cause failure; corrected live continuation remains successful. Lead waits terminal result, verifies current evidence, then reserves cycle 2 for G0 only.

## Architecture advisory during G0 — no frozen contracts yet

- [x] [sa] `sa_g0`, architecture advisory for future G1; writable only `.codex/specs/cognitive-graph-mvp/sa-review.md`. Read unchanged approved specification and G0 evidence; analyze loop SCC/activation initialization, durable identity/replay/restart, one external batch, cancellation/timeout accounting and external network boundaries. No production files, no edits to requirements/design/spec/tasks/decisions/review. Produce specific provisional contracts and risks, not implementation or a formal verdict. Run: evidence-linked analysis of A03–A10/A14/A16 plus current official SQLite/asyncio/Ollama documentation as needed; no runtime PASS. Peer coding research continues. Lead must wait for `coding_rd1`, `coding_rd2`, and `sa_g0` before G1 consolidation. G0 remains gated on RD1/RD2.

## Planned G1 wave — gated on G0 PASS

- [x] [coding] `coding_bootstrap`, G1-contracts single shared-contract/bootstrap/dependency owner. Writable exact files: `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/contracts/__init__.py`, `backend/app/contracts/graph.py`, `backend/app/contracts/api.py`, `backend/app/contracts/config.py`, `backend/app/contracts/errors.py`, `backend/app/contracts/interfaces.py`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`, `backend/tests/contracts/test_contracts.py`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/contracts/generated.ts`, `frontend/src/contracts/schema.json`, `frontend/src/contracts/contracts.test.ts`, `scripts/export_contracts.py`, `scripts/dev.py`, `Makefile`, `docs/api.md`, `docs/dependencies.md`. No edits to research, other product modules, configuration/authentication, durable spec/review artifacts, or peer files. Consume root sections 3–8/10 and accepted G0/SA decisions; produce exact Pydantic graph/API/config/error DTOs, activation/checkpoint/provider/storage/runtime/tool interfaces, generated JSON Schema/TypeScript consistency checks, isolated pinned Python/npm toolchains, executable development targets and API contract documentation. Preserve R01–R11/A01–A16. Structural/runtime implementation remains in later groups. Run: documented local locked setup, `make lint`, `make test-contract`, schema regeneration/consistency checks and frontend contract/type checks; Windows equivalent through `python scripts/dev.py` must execute the same commands. Targets without implemented prerequisites fail nonzero; no always-green smoke placeholders. Return files, pins/source evidence, frozen interface signatures, exact checks/exits and unresolved choices. Lead waits for terminal result and independent G1 review before dependent writers.

This planned ownership is not a G1 freeze or implementation start. No worker is launched until G0 PASS. The bootstrap owner retains sole ownership of manifests/locks/shared contracts/development targets through later waves; overlapping main.py/API composition ownership is transferred explicitly and serially when needed.

## Delivery preflight during G1 — research only

- [x] [devops] `devops_preflight`, writable only `docs/research/delivery-preflight.md`. Consume approved R10/A15 environment/ports/external-Ollama boundary and coordinate target Python/Node versions with the sole G1 bootstrap owner. Query exact base-image/tool digests and Windows/WSL2 prerequisites; use a uniquely named disposable diagnostic container from an immutable already-cached image if useful to establish Docker-network Ollama reachability. Override entrypoint to a bounded HTTP GET diagnostic only, no inference server/GPU/volumes/Docker socket, no external-resource/config mutation or image/model download. Own and remove only its temporary diagnostic container; record exact resource identity and residue check. No Compose/Dockerfile/manifests/bootstrap/config/source edits. Run: bounded metadata/version/HTTP probes and read-only residue query; all exits recorded. This prepares G5 without starting delivery implementation before frozen G1. Return exact digests/routes/commands, unresolved facts and open actual-backend/Compose gates; send needed pin facts to coding_bootstrap. Lead harvests this independent result before delivery handoff.

Section 12 of the authoritative source defines G1–G6. Exact writable files, shared bootstrap/manifest ownership and frozen contracts will be expanded here after G0 succeeds, before any implementation handoff.

## G1 contract architecture advisory

- [x] [sa] `sa_g1`, G1-contracts advisory; writable only `.codex/specs/cognitive-graph-mvp/sa-review.md`, append a distinct G1 section preserving G0 advice. Read available G1 contract drafts and approved specification/decisions, coordinate questions with `coding_bootstrap` without editing its files. Review the concrete interfaces for loop barriers, immutable snapshots, partial continuation/replay, durable recovery, claim transactions, shared admission and inference bounds. This is advisory, not a synthesizer verdict or review-budget consumption. Return actionable interface gaps tied to A03–A10/A14/A16 and exact source references. No runtime PASS claims, production/review/config edits, recursive delegation, external writes or secret access. Bootstrap is a concurrent peer and sole contract owner; never revert its edits. Lead waits for both this advisory and bootstrap before independent G1 review.

## Module wave — launched after G1 PASS

### G1 fix wave 1 — cycle 1 findings

- [x] [coding] `coding_bootstrap` retains sole contract ownership. Exact writable files for this correction: `backend/app/contracts/api.py`, `backend/tests/contracts/test_contracts.py`, `frontend/src/contracts/schema.json`, `frontend/src/contracts/generated.ts`, `frontend/src/contracts/contracts.test.ts`, `docs/api.md`. No other edits. Close G1 cycle 1 High F1 by preserving optional tool-result name and proving all three authoritative pinned Hermes client requests pass Python and generated-schema validation without changing raw arguments/results/history. Close Medium F2 by specifying and testing the strict upstream response normalization boundary against all five authoritative raw Ollama wire responses, preserving semantic fields and documenting only known transport metadata treatment. Unsupported client semantics remain strict errors; malformed/unsupported upstream semantics must not be silently dropped. Pure DTO-boundary construction/parsing is allowed; no provider/network/runtime implementation yet. Use read-only authoritative_final_experiment in existing traces; preserve research evidence, request metadata and dependency pins. Run test-first reproductions, regeneration, `python scripts/dev.py lint`, `test-contract`, `test`, and schema drift check; report exact exits/counts/hashes and unchanged lock hashes. Lead waits terminal result, reconciles current evidence, then reserves G1 cycle 2; G0 counter remains unchanged and downstream writers still wait.

The following scopes are prepared for handoff. They consume the final G1 contracts, not current drafts. Every worker reads the source specification and AGENTS.md. Peer writers are concurrent and must not revert or overwrite one another. No recursive delegation. Root waits for every launched worker's terminal result before consolidating the wave. Contract/manifest/lock/development-target changes route exclusively to `coding_bootstrap` and are applied serially.

- [x] [coding] `coding_runtime`, G2-runtime module wave; independent review and integration gates open. Exact writable files: `backend/app/runtime/__init__.py`, `backend/app/runtime/engine.py`, `backend/app/runtime/admission.py`, `backend/app/runtime/clock.py`, `backend/app/storage/__init__.py`, `backend/app/storage/repository.py`, `backend/app/storage/events.py`, `backend/tests/runtime/test_scheduler.py`, `backend/tests/runtime/test_loops.py`, `backend/tests/runtime/test_recovery.py`, `backend/tests/runtime/test_admission.py`, `backend/tests/storage/test_sqlite.py`. No other files. Implement frozen GraphRuntime/AdmissionController/EventBus/RunRepository interfaces, DAG readiness and lexical all-input fan-in, independent seeded scopes and strict control termination, short WAL transactions with durable uniqueness/CAS/claims/events, quiescent tool checkpoints, budgets and independent timing, cancellation/recovery/retention. Consume CompiledGraph, OllamaAdapter and ToolBridge; do not implement graph validation, HTTP routes, upstream transport or tool execution. Fake adapters are test-only. Required evidence A03–A06/A08–A10/A13–A14/A16: deterministic concurrency, seeds and iterations, malformed control/budget failure, partial/replay race and late result rejection, uncertain recovery without rerun, snapshot invariance, global admission bounds. Run locked backend pytest on these exact test paths and Ruff on owned files; return commands/exits, source signatures and remaining integration gates. Neither in-memory maps alone nor tests mirroring implementation prove durability.

- [x] [coding] `coding_graphs`, G4-ui graph backend portion. Exact writable files: `backend/app/graphs/__init__.py`, `backend/app/graphs/repository.py`, `backend/app/graphs/validator.py`, `backend/app/api/__init__.py`, `backend/app/api/graphs.py`, `backend/tests/graphs/test_repository.py`, `backend/tests/graphs/test_validator.py`, `backend/tests/graphs/test_api.py`, `examples/synthesis.json`, `examples/feedback.json`, `examples/multiple-inputs.json`. No other files. Implement GraphRepository/Validator and injectable graph management router on frozen contracts. Validate forward DAG, port ownership, reachability, disjoint explicit loop scopes/controller barriers, feedback seed and boundary edges; compile immutable plans. Atomic fsync/replace graph files, safe IDs, expected revision, immutable retained publications, draft isolation, named input preparation. Consume auth dependencies through injection until API integration supplies them; no separate auth policy. Required A04–A06/A12–A13/A16 proof includes invalid cross-scope cycles, concurrent saves, publication retention, path traversal/symlink safety and unchanged data on errors. Run locked pytest on exact graph tests and Ruff on owned files; return exact interface construction and commands/exits. Lead will assign proxy work only after this scope finishes.

- [x] [devops] `devops_delivery`, G5-delivery independent files; integrated build/live gates remain open. Exact writable files: `compose.yaml`, `.env.example`, `.dockerignore`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `.github/workflows/ci.yml`, `docs/runbook.md`, `docs/hermes-compatibility.md`, `docs/verification.md`, `README.md`, `scripts/smoke_hermes.py`, `scripts/smoke_compose.sh`, `scripts/smoke_compose.py`. No other files. Consume frozen config/API/dev commands and preflight immutable image pins. Build two services only, external Ollama/tools, no GPU/socket/cloud/MCP/automatic approvals, one backend worker, named cg_data volume, localhost ports, same-origin static UI and unbuffered SSE/timeouts above active budget. Real smoke commands must fail nonzero when prerequisites or checks fail; preserve safe dedicated fixtures and user data. Document native Windows/WSL2 setup, endpoint alternatives demonstrated by probes, backup/retention/restart and explicit destructive down -v warning. Required R10/A01/A07/A10/A15/A16: actual config/build/health/route/volume/SQLite/SSE/restart smoke when permitted; static checks alone leave live gates open. Do not bypass the rejected preflight diagnostic. A distinct actual implemented Compose validation is a separate gate; report any enforcement rejection exactly. Never read/print secrets, mutate existing Ollama, download models or install globally. Ask root for concrete gates requiring non-reversible/external changes. Report exact commands/exits and open gates.

## Planned proxy, UI and integration ownership — sequential handoffs

### Narrow shared metadata correction during module implementation

Serial correction also owns `scripts/dev.py` and `Makefile` for the executed Windows smoke-wrapper defect: wslpath must receive ROOT.as_posix(), propagate conversion/helper failures without a raw traceback, and forward explicit smoke arguments and required environment safely. Use the existing owner, preserve secret values from output, no global WSLENV/config edit. Verify actual Windows→WSL helper validation and argument/nonzero propagation, not only mocked subprocess lists. This is the same G1 additive correction and counter, not a new task group.

- [x] [coding] `coding_bootstrap`, G1-contracts compatible additive correction; independent review remains open. Exact writable files: `backend/app/contracts/interfaces.py`, `backend/tests/contracts/test_contracts.py`, `docs/api.md`; regenerated `frontend/src/contracts/schema.json` and `frontend/src/contracts/generated.ts` only if authoritative generation changes them. No other edits. Add optional ActivationRecord.finish_reason typed with existing FinishReason, default None for non-provider/pending activations; preserve actual final length across serialized checkpoint and recovery. Do not overload unrelated fields or change public profile/config/topology/constructor methods. Document graph router injection and current module-only implementation status without claiming G4 complete. Run test-first checkpoint round-trip and invalid-reason rejection, locked contract/lint/drift checks, graph regression. Runtime owner is concurrent on disjoint files and will add executable length/recovery proof; do not edit peer modules. Final G1 review cycle 3 is retained for coherent post-consumer contract reconciliation, not spawned during this small edit; current extension gate remains open until independent review. Do not reset G1's 2/3 counter.

- [x] [coding] `coding_proxy`, G3-proxy module handoff; JSON boundary/API/review remain open. Exact writable files: `backend/app/providers/__init__.py`, `backend/app/providers/ollama.py`, `backend/app/providers/sse.py`, `backend/app/tools/__init__.py`, `backend/app/tools/bridge.py`, `backend/tests/providers/test_ollama.py`, `backend/tests/providers/test_sse.py`, `backend/tests/tools/test_bridge.py`. Consume frozen contracts and runtime storage; own OllamaAdapter and ToolBridge only. Transport uses a shared inference limiter for graph and direct calls, no effectful retry/disk cache; streaming permit lasts through closure. Preserve physical-model profile, strict SSE/errors, opaque owner IDs, latest-segment continuation, canonical echo/replay checks, conservative tool exposure and fixed TTL. Backend never executes tools. Run mock HTTP/SSE and durable-store contract tests, Ruff; required A02/A07–A11/A14/A16; return exact evidence and interface seams.

- [x] [coding] `coding_ui`, G4-ui frontend independent handoff; API-backed E2E/review remain open. Exact writable files: `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts`, `frontend/src/editor/Editor.tsx`, `frontend/src/editor/GraphNode.tsx`, `frontend/src/editor/graph.ts`, `frontend/src/editor/graph.test.ts`, `frontend/src/runs/History.tsx`, `frontend/src/runs/RunDetail.tsx`, `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/styles.css`, `frontend/playwright.config.ts`, `frontend/e2e/mvp.spec.ts`. No manifests/lockfiles/contracts/Vite changes. Consume generated DTOs and management API; existing selected React Flow provides canvas only. Implement CRUD/import/export/publish/revision conflicts, named ports/prompts/generation/tools/loop membership/seed, named-input test run, history/details/readiness/manual tool results/cancel, authenticated fetch SSE with durable resume and API reload. No tokens in URLs/graphs/logs. Run pinned TypeScript/unit/build and real-browser backend E2E; A12/A13 and trace/UI portions of A04/A05/A08/A14/A16. Return exact evidence; missing endpoints are integration gates, not mock-only PASS.

- [x] [coding] `coding_api`, G3-proxy/G6-integration after runtime/proxy contracts are implemented. Exact writable files: `backend/app/api/chat.py`, `backend/app/api/runs.py`, `backend/app/api/models.py`, `backend/app/api/security.py`, `backend/app/main.py`, `backend/tests/api/test_chat.py`, `backend/tests/api/test_runs.py`, `backend/tests/api/test_security.py`, `backend/tests/integration/test_acceptance.py`. `main.py` transfers serially from bootstrap only when this handoff is activated. All other shared contracts/manifests/locks/dev commands remain bootstrap-owned. Compose components, lifecycle/recovery, every management/public route, auth/namespace/size limits, JSON/SSE graph/direct behavior, cancellation/disconnect and event replay. Preserve runtime independence and immutable published snapshots. Integration tests exercise real HTTP handlers/mock Ollama and SQLite, not only DTO construction; cover A01–A16 deterministic portions. Run full locked backend checks plus contract suite, frontend/browser checks after UI availability; return exact evidence and live gates.

## G2 fix wave 1 — cycle 1 findings (queued for a coding slot)

- [x] [coding] Existing coding_runtime owns only backend/app/runtime/engine.py and backend/tests/runtime/test_scheduler.py, test_loops.py, test_recovery.py for review_g2_c1 F1-F3. Reject failed/cancelled/interrupted before saved envelope delivery while retaining successful completion and detach-after-exposure; preserve controller payload JSON encoding for external JSON formats without double-encoding ordinary final text; rebase only actual schema reference keywords, preserving literal data under const/enum/default/examples. Regression-first proof, locked affected/full tests and scoped Ruff; no contracts/manifests/storage/peer/review edits. One fix wave then reserve G2 cycle2, not a reset.

## Additional G1 upstream normalization correction (queued serially)

- [x] [coding] Existing coding_bootstrap owns only backend/app/contracts/api.py, backend/tests/contracts/test_contracts.py, docs/api.md and frontend/vite.config.ts for captured default-thinking upstream evidence and actual Vitest collection seam. Private upstream assistant DTO accepts optional reasoning str/null and discards validated hidden reasoning only. Public AssistantMessage remains strict; malformed metadata and unknown semantics rejected, visible text/calls/raw arguments preserved and input unmutated. No public reasoning control/default, no hidden reasoning capture in artifacts. Exact generation drift/contract/Ruff checks; locks/generated outputs unchanged unless actual generator proves drift. Same G1 group2/3; final cycle3 held until coherent consumer reconciliation.

## G5 actual-image persistence check during proxy/UI implementation

- [x] [devops] Existing devops_delivery owns the same14 delivery files only; actual-image persistence delivered, stdin-free helper correction queued. Rebuild the actual pinned backend image, then exercise production SQLiteRunRepository and runtime fake-provider behavior against native Linux/SQLite3.40.1 through a uniquely scoped Compose backend test command. No external network probe/Ollama inference, tool execution, user volume/config mutation or destructive teardown; retain own named data volume and record resources. Current G2 findings remain unresolved; probe only unaffected persistence/runtime behavior and cannot claim overall G2/G5 PASS. Inspect Windows/WSL path/symlink/fsync behavior in actual Linux if feasible. Exact executable commands/exit/source hashes and no-extra-service/device/socket assertions; integrated startup/Hermes/Compose smoke still OPEN. No new file ownership or recursive agents.

The same queued G1 correction must separate pinned Vitest unit discovery from Playwright e2e/mvp.spec.ts, preserving normal src tests and all E2E execution through the real test-e2e target. Current npm test mistakenly invokes Playwright beforeAll via Vitest and fails while17 unit cases pass. No browser check is skipped or relabeled green.

- [x] [devops] Same devops_delivery owns only scripts/smoke_compose.py and docs/verification.md for noninteractive contract reconciliation: replace Compose override stdin input with a task-owned temporary parameter file passed through -f; never wait on stdin/TTY. Retain actual executed d1/d2/d3 evidence unchanged, test real validate/argv behavior and fresh persistence in new unique project if permitted. No user data deletion/network/inference/runtime/server/shared file changes.

## G2 fix wave 2 — final available fix before terminal cycle 3

- [x] [sa] sa_g2_schema, advisory only, sole writable .codex/specs/cognitive-graph-mvp/sa-review.md (append). Analyze final controller schema embedding, empty/fragment/relative/absolute IDs, legacy/modern dialect/resource/reference/annotation semantics and final-format paths. Reproduce with pinned local validators/actual request construction, no remote schema fetch or inference. Produce a minimal supported design without changing accepted profile/dependencies or emitting PASS. Exact source requirements and cycle2 F4 remain authoritative; same G2counter2/3, advisory is not a synthesizer.
- [x] [coding] Existing coding_runtime owns only backend/app/runtime/engine.py and backend/tests/runtime/test_scheduler.py, test_loops.py, test_recovery.py. Regression-first cycle2 F4 empty-ID reproduction plus accepted schema boundary matrix; coordinate with SA advisory before finalizing minimal correction, no caller contract narrowing or production dependency. Verify all final response-format paths including legal no-LLM pass-through and preserve ordinary already-formatted LLM text. No other edits. Run pinned affected/full/drift/Ruff. Lead waits both terminal results before reserving final G2cycle3; no fourth cycle or reset.

## G1/G2 final-format disposition and browser integration

- [x] [coding] Existing coding_runtime retains exact four-file fixwave2 ownership. Final native zero-LLM/controller payloads must honor response_format: JSON serialization plus object/schema validation, explicit invalid_parameter400 for incompatible zero-LLM input and upstream_error502 for invalid controller payload. Validate standard local declared dialects/refs with pinned jsonschema, never fetch remote resources; preserve original immutable caller policy and ordinary serialized LLM content. No dependency/profile edits by runtime.
- [x] [coding] Existing coding_bootstrap resumed sole owner backend/pyproject.toml, backend/uv.lock, docs/dependencies.md and docs/api.md. Promote already exact-pinned jsonschema4.26.0 to production for required final native-payload constraint validation, retain immutable transitives/pins, reconcile actual API composition/status and format errors. No main.py ownership (transferred API), other files or scope expansion. Run locked sync/contract/drift/full checks and report lock changes. Same G1counter2/3, final review held until coherent consumers.
- [x] [coding] Existing coding_ui resumed identical thirteen-file frontend ownership for actual-backend four-scenario Playwright E2E. Consume terminal API routes, no backend/contracts/manifests/docs changes; mock Ollama only, no browser route stubs as acceptance. Exact pinned unit/typecheck/build/E2E commands and listener cleanup proof; report integration defects to owning agent. No concurrent Compose8000 listener. Lead waits requested owners before consolidation.

## G5/G6 integrated delivery and target evidence

- [-] [devops] Existing devops_delivery resumes same fourteen-file delivery ownership. Prepare real production smokes for public direct JSON/SSE/tools+results/multiturn; literal cg/synthesis Hermes selection in dedicated new project; actual waiting-tools backend process/container restart with preserved IDs and no repeated effects; actual Hermes compression pending-continuation; same-model target diamond versus sequential wall/queue/node/call metrics. Safe dedicated fixtures only, no fake provider advertised live, no token/hidden reasoning capture or user Ollama/model/config changes. Wait root release of UI8000/5173 and bootstrap pinned-manifest handoff before actual build/start; no concurrent listener ownership. Rebuild both immutable-pinned images, Windows and WSL2 actual Compose smoke, validate actual container upstream route, Nginx SSE and retained volume, native Hermes outsideCompose. Record exact errors and unavailablegates rather than substitute. Retain own volumes and never down-v/prune; scoped owncontainers down permitted by prior smokecontract. All shared/product/backend/frontend files excluded; integration defects route owner. G5/G6counters remain0/3 until ready independentreview.

## G4 independent review cycle 1 reservation

- [x] [review] review_g4_c1 sole independent synthesizer, G4-ui cycle1/3 reserved before spawn. Writable only review.md append; read-only exact24files: graph backend eleven files from coding_graphs and frontend thirteen files from coding_ui. Review currentdisk including newuntracked productfiles, entire source/AGENTS/artifacts/pinned contracts and current API seam. RequiredG4proof: schema/files/atomicrevision/publication/path validation, actualUIports/prompts/generation/tools/loop/seed/import/export/publication/history/readiness/manualresults/cancel, APIreload/tokenmemory/authSSEcursor, immutable snapshot and processpersistence. Run exact locked test-graphs/frontunit/typecheck/build/realbackendfourE2E; no mock browserrequeststubs, actual mockOllama clearly separate from Hermes. Reviewer owns native8000/5173 only during dedicated E2E, scopedownprocesscleanup, DevOpsbuild/start awaits release. Runtimefourfilecorrection concurrent but G4 files frozen; do noteditpeers/delegate/reconfigure/useusersecrets or claim realHermes/containerproof. Return prescribed PASS/FAIL/findings/evidence/openintegrationgates, missingrequiredG4evidenceFAIL. Lead waits terminal, no other review.mdwriter.

## G4 cycle1 correction preparation (not activated before verdict)

- [x] [coding] Existing coding_ui resumed exact frontend/src/editor/Editor.tsx, frontend/src/App.tsx and frontend/e2e/mvp.spec.ts ONLY for same-ID APIreload generation inspector stale overwrite, after authoritative cycle1FAIL. Preserve currentserverloadedgeneration/null/committedlocalsettings coherently and uncommittededitbehavior; regression-first actualbrowser reload0.7→Apply→Save mustretain0.7. No backend/manifests/generated/peer/review/artifactedits. Pinned frontendunit/typecheck/build/full4+newE2E and scopedlistenercleanup.
- [x] [coding] Existing coding_graphs resumed exact backend/app/api/graphs.py and backend/tests/graphs/test_api.py ONLY for graphrequest escapedunpairedUnicode400 validation, after authoritative cycle1FAIL. Reproduce POST/PUT plusvalidate boundary andunchangedexistingdata, positivevalidUnicode; rejectstrictcanonicalUTF8 beforehash/storage, standard sanitized400 no500. No repository/schema/runtime/manifest/peer/review/artifactedits. Lockedaffected52+newgraphcases/fullchecks/Ruff.

Scopes file-disjoint but boundedslotsapply: G2 terminalcycle3 reviewer may run concurrently, sole review.mdowner only after G4cycle1terminal. Activate one codingfixowner alongside DevOps/reviewer, then other afterterminal; G4cycle2reserved onlyafterbothrequestedfixresults/currentchecks. SameG4counter1/3; no reset. DevOps integratedstartawaits correctedUI/backend readiness and explicitportrelease.

## G2 final independent review cycle 3 reservation

- [x] [review] review_g2_c3 sole independent synthesizer, stableG2-runtime cycle3/3 reserved BEFOREspawn. Exactoriginal12runtime/storage source/testfiles read-only, current4file finalfix plus productionvalidator4.26 consumer. Writable review.md appendONLY after terminalG4reviewer. Reprove priorF1-F4 and advisoryformat/native/dialect/resource/legacy/annotation targets, originalschema good/bad and immutablepolicy, before-saving successvalidation/400native502provider/rawbytes/length, no remote fetch. Fullmodule/G1contract/stableAPI regression evidence currentroot475+21/lint0. RequiredG2modulechecks+crossseams no fakeequivalentliveproof. Correctedimage/Hermes/container/WindowsWSL/performance remainG5/G6gates and no completionclaim. Counter3terminalnonPASS=>BLOCKED stopautomaticfix/review; neverfourth/reset/split. Native modulefixtures do notneed8000/5173; codingUIfix may ownthoseports, DevOpspreparationonly.

### G2 terminal blocker (authoritative cycle3 review)

G2-runtime BLOCKED3/3: valid Draft3 schema-valued extends/type localreferences are notrebased, causing actualscheduler failed/upstream_error despiteoriginalgood/bad constraints/publicDTOvalidity. ReviewF5sourceengine657/671, immutablecaller/no successenvelope retained. StopautomaticG2fix/review; no fourth/replacement/reset/renaming. Userdisposition required tochange thisgate; no change to acceptedprofile orbudget. ContinueonlyindependentG4fixes/G3/G5verification; cannotcompleteMVPwhileG2blocked.

G2reviewerterminal frees slot: activate graph2filefix concurrentlywithUI3filefix, exactfile-disjoint; nowtwoCoding+oneDevOps=root+3children ceiling. Both G4requestedfixownersmustreturnbeforeconsolidation/cycle2. No G2fixauthorized bythiscapacitychange.

## G3 expired-wait verification seam

- [x] [coding] Existing coding_api owns ONLY backend/app/api/chat.py and backend/tests/api/test_runs.py to diagnose full-suite expiredwait409vs504 failingassertion after G4fix. Preserve distinct expired-in-flight timeout504 and lateresult-after-terminal409, fixedUTCdeadline, no timeoutextension/reexecution/successfabrication. Establish deterministicbefore/after-terminal barrier evidence; do not merely acceptbothcodes/removeassertions. ProductionAPIchangeonlyifactualsourcecontractdefectproven; bridge/runtime/storage edits excluded and G2exhaustedgroupfrozen. Tests actualHTTP/SQLite/mockupstream exactfocusedAPI/integration/fullbackend whenstable, Ruffowned2files. Userrequirementerrorcontractauthoritative; record discrepancybetweenpreviousroot475pass andcurrent520/1fail+isolatedfailure ratherthanclaimnewG4parser causedit. Returnterminalverifieradequacy/interface/evidence. G3counter0/3, thisimplementationtestseam notnewreviewcycle/group.

## G1 final documentation reconciliation before review

- [x] [coding] Existing coding_bootstrap owns ONLY docs/api.md and docs/dependencies.md. Record preciseknownG2terminalF5controller/Draft3referencebug and3/3BLOCKED, frozenacceptedprofile/noautomaticfourth; do notdescribevalidschemaasunsupported tohidebug. Reconcile finalG4wholeUTF8validation/inspector reload+6browser andpinned22productionpackage/imagebuild subsets, APItesttimeout504vsafterterminal409 onlyafterfreshownerterminal/currentproof. G1contractextensionsremainreview2/3 untilfinalsynthesizer; no Productcomplete/liveclaim. Exactdocumentationreferences/sourceaudit/whitespacecheck, no production/tests/manifests/lock/review/artifactedits orlisteners. PeerAPI2filetestseamactive+DevOpsdelivery14filesbuild/liveholds disjoint, leadwaitsterminal.

## G4 independent review cycle2 reservation

- [x] [review] review_g4_c2 sole synthesizer, G4-ui cycle2/3 reservedBEFOREspawn. Sameexact24fileoriginalG4scope, fivefixfiles (UI3/graph2), read-onlyactualdisk. Writable review.mdappendONLY, previousG2writerterminal. Bothrequestedfixownersterminal, baselineF1F2regressionsfirstfailed andcurrent98graphs/55API/21frontend/TS/build/6browser15.3spassed; latestbackend522 androotlint0. Reprove sameIDreopen/conflictreload/import inspector generation/edge/scope semantics withunapplieddrafts preservedwithin currentloadedgraph, invalidwholedecodedUTF8400/validSupplementary/no-write/no-tokenlogs. Requiredappropriatecommands+fresh6actualbackendE2E no browserrequeststubs; reviewer8000/5173 untilterminalcleanup, DevOpsbuildONLYdone/noSTARTuntilrootrelease. G2remainsBLOCKED3/3separateknownschemaF5,noG2repair/profilechange/groupreset. No analystmissing/peerwrites/delegation/externaltool/liveclaim. Leadwaitsterminalbeforerelease/consolidation; nonPASScycle2 permitsonescopedfixthenfinal3, nofourth.


## G4 cycle 2 terminal consolidation and delivery release

G4-ui independent cycle2 PASS; F1/F2 empirically closed, current findings zero. Reviewer independently ran graph98/frontend21/TS/build/six actual-backend Chromium scenarios15.3s and repository lint, all exit0. Current24-file aggregate SHA90a624649afbb5da3c8ca6e08301eff55b1619f8716b2fe589bdfd81648b46ae. All own fixture process trees stopped,8000/5173 verified clear; report in review.md. G4counter stays2/3. Root released already-authorized G5/G6 actualWindows smoke and freshWSL smoke after this positive terminal cleanup; preserve unavailable live gates and finish independent native fallback. No G2 fix/review is authorized; G2BLOCKED3/3F5 still prevents completion.


## G3 independent review cycle 1 reservation

- [x] [review] review_g3_c1 sole review-agent synthesizer, G3-proxy cycle1/3 reserved before spawn; no analysts. Sole writable review.md append, G4 previouswriter terminal. Read-only exact17files: backend/app/providers/__init__.py, ollama.py, sse.py; backend/app/tools/__init__.py, bridge.py; backend/tests/providers/test_ollama.py, test_sse.py; backend/tests/tools/test_bridge.py; backend/app/api/chat.py, runs.py, models.py, security.py; backend/app/main.py; backend/tests/api/test_chat.py, test_runs.py, test_security.py; backend/tests/integration/test_acceptance.py. Review original G3 modules and composed API seam, frozen contracts/source/profile, mocked and real public transport/continuation evidence. Fresh focused contract/provider/tool/API/integration checks, applicable CI lint; inspect strictmetadata/framing/auth/namespace/immutablepolicy/admission/opaqueIDs/partialwhole-ownerround/forcedchoice/replay/TTL/recovery/disconnect. No listeners, container actions, real inference/tools or writes beyond review; DevOps owns current actual live8000/8080 andsmoke14files. Wait root terminal-live evidence before synthesizing required real-public gates; missing required evidence meansFAIL with precisegate, never fabricatedseverity. G2BLOCKED3/3F5 separate and frozen; no G2 fixes/reset/profile narrowing underG3. Rootwaits terminalreport; onlycurrentreview.mdwriter.


## G1 final current-state documentation handoff

- [x] [coding] Existing coding_bootstrap sole owner docs/api.md and docs/dependencies.md ONLY. Replace stale API timing/G4 pending claims with terminal522backend/49API+integration/21frontend/98graphs/sixrealbackendbrowser/G4independentPASS2/3. Preserve G2BLOCKED3/3validDraft3F5/noautomaticfourth/frozenprofile and G1lastreviewpending2/3. Current actualWindows correctedhealthy/defaultcontainerroute probe andsevenreal directJSONSSE/native-toolrequest+manualresult phases passed, but fullHermes/restart/performance/WSL session stillactive; reference deliveryverification for changing live details, never advertisefullPASS. Retain historical475/firstnativeexception/verifier failures with clear attribution, current22prodjsonschema4.26/unchangedlocks. No otherfiles/tests/manifest/lock/contracts/review/artifacts/listeners/liveeffects. Directsource/UTF8/link/whitespaceaudit exactcommands/exits; rootwaitsterminal before G1finalcycle3 reservation. PeerDevOps14files+G3reviewsole review.mdwriter active, disjoint; no agentdelegation.


FinalG1docs dispatch returned agentthreadlimitreached, no newwork/result claimed. Freshinventory root/DevOps/G3review running, bootstrap absent/terminal; defer sameowner resume until terminal capacityrelease ratherthan spawnreplacement/reconfigure. No reviewbudgetconsumed.


## G3 cycle 1 scoped correction wave

- [x] [coding] Existing coding_proxy sole owner ONLY backend/app/providers/ollama.py, backend/app/providers/sse.py, backend/tests/providers/test_ollama.py and backend/tests/providers/test_sse.py. Re-read currentfiles; regression-first authoritative G3cycle1MediumF1/F2: SSE wire framing CR/LF/CRLF only, incrementalstrictUTF8 preserving literalU0085/U2028/U2029 andfragmentedmultibyte/supplementary characters; rejectmalformedbytes incontent/rawtoolarguments preheader502 orpostheadererrorevent/nofakefinishDONE, boundedline/eventbuffers andfullpermitcleanup. Nonstream complete normalized upstream JSON mustbeUTF8encodable beforeproviderreturns; escapedunpairedscalars incontent/name/IDs/rawarguments rejectsanitizedupstream502 neverstorage500, validpairs/rawargumentbytes preserved. No publicprofile/sharedcontract/dependencies/bridge/API/runtime/store/locks/docs/spec/reviewedit orliveeffects. Run affectedmocktests, exactG3focused212+new, contract/drift/Ruff/fullbackendappropriatechecks withterminalexits; preserve fail-firstevidence. DevOps14filesobserver correction offline andnextfullimagesheldpendingstableproviderhandoff. G2BLOCKED3/3F5 isfrozen/no repairunderG3. Rootwaits terminal/freshcoherentimageproof beforecycle2 reservation, G3counter1/3unchanged.


G3fixownerTERMINAL:65newcases; affected109/focused277/fullbackend58757.11s/Ruff4files/drift/ninefrontendcontracts all0. Rootcurrenthashesverifiedollama660797ab43282dba990d8ef69e8214009606d87d0d9861c28997a07182152dff/sse99b8128918baca052f969f897e9049ced87128766cc66a3afd5ec7a8c69ece75/tests54a9979b.../69272cff..., chatb68226/engineb8ff/uv431c/npm229187 unchanged. ReleaseDevOpscorrected-sourceimagebuild/live Windows+freshWSL withauthenticobserver; no inheritedoldproviderproof/independentPASSyet. FinalG1docs sameownerresumeafterpositivecodingterminalcapacityrelease updateslatest587/277/109 asappropriate, nopeer/sourceedits.


## G1 final independent review cycle 3 reservation

- [!] [review] review_g1_c3 sole synthesizer G1-contracts FINALcycle3/3 reserved BEFOREspawn, noanalysts. Solewrite review.mdappend (G3priorwriterterminal), exact25originalcontract/bootstrap/manifests/locks/generated/docs filesread-only, excludingmain.pyseriallytransferredAPI. CurrentoptionalActivationRecord.finish_reason/privateknownreasoningnormalization/Vitestdiscovery/WinWSLwrapper/jsonschema4.26production/docscurrentstates reviewedwithcoherentterminalG3/API/G4consumers. ReprovebaselineF1toolresultname/F2strictupstreammetadata; generatedschema consistency, exactpins/locks/config/error/profile/scheduler+store+bridgeinterfaces/Makewrapper meaningfultargetchecks. No productionedits/liveeffects/listeners/containerstarts/globaltoolinstall/peerwrites. DevOps14filesactualWindowsWSLsourcecoherentlive maycontinue disjoint; realservicesgate belongsG5/G6 and mustnotbeclaimedbyG1static checks. G2BLOCKED3/3F5separatefrozen, noacceptedprofilenarrowing/budgetreset. Counter3terminalnonPASS=>G1BLOCKED/nofourth; leadwaits authoritative terminalreport beforeconsolidation.


## Account-usage terminal failures and local verification recovery

Clientpositiveevidence: review_g1_c3 anddevops_delivery agentstatusERRORED accountusagelimit, no normalterminalreview/deliveryhandoff. G1finalcycle3unablecompleteisBLOCKED3/3; freshtest-contract228Python/ninefrontend/drift0 partialonly, NOauthoritativecycle3verdict/PASS. DoNOTrespawn/retry/fourth/reset/reclassifyG1. G2BLOCKED3/3F5 unchanged. G3re-reviewandG5/G6initialindependentreviews unexecuted dueaccountlimits, counters1/3/0/3/0/3 stayunchanged. No modelmatrixchange/purchase/globalapproval/externalwrites. Allrequestedworkersnowterminalcompletedorerrored, noquietinflighttakeover.

Rootonlyexecutesalreadyimplementedlocalvalidation/no productedits: freshconfiguredlint0 all49formatchecks/drift/TS; ownWindows/Linuxsmokeprocessqueriesempty, no ownactiveCompose/listeners; existingunrelatedcontainerspreserved. PreparedfullWSLhelperrunning uniquelyownedcg-smoke-wsl-root-20261004-81cd29e6 viaexistingnativeWindowsHermesinterop, currentsourceprobe/newownedvolume, sameoriginalassertions, noeffectretries. Thisis localverification recovery afterconfirmedworkerfailure, no independentreviewsubstitution. Exactlog .venv/root-wsl-smoke-20261004-81cd29e6.log; nativeWindows evidence versioned live-windows-hermes.json.


## Narrow G5 helper recovery after confirmed quota termination

Root temporarilyowns ONLY scripts/smoke_compose.py nativeinteropversionguard, solewriterafterpositiveDevOpsterminalERRORED/noactiveworker. ActualWSLfullattempt81cd29e6exit1 after currentcontainer/public/Nginx/history/targetpassed, nativeguardPackageNotFound beforeHermes; rootreadonlyactualnativeWSLdiagnostic0 provesmetadatahermes-agent/OpenAI/httpx absentbeforeexistingnativesitepath and exact0.18.2/2.24.0/0.28.1 aftersameHermesvenvLibsitepathalreadyusedbypinnedload_hermes. Correctguardappendexplicitnativehermesrootexistingpackagepath beforemetadata; preserve strictversions/same-daemon/sourcechecks, no install/globalenv/pin/profile/client/executor/configchange. Exactcurrent3-line-equivalenthelpercorrectiononly, no broadimplementationtakeover/nopeers/G1/G2edits. Actualextractedguard +configuredRuff +onefreshfullWSL rerunrequired; oldfailure/evidence/volumeretained, noeffectsreplayed. G5counter0/3 stillindependentreviewOPENdueusage.


## Final administrative documentation consolidation

After confirmed quota-errored delivery owner/reviewer and terminal WSL
validation, root was the sole status/evidence writer for the listed docs.
This historical handoff preserved failed checks/source/pins/contracts and
recorded G1's then-unable cycle3, G2 F5 BLOCKED3/3, G3 correction with review
OPEN1/3, G5/G6 OPEN0/3, and known unexecuted backup/restore/remote-CI gates.
The later user-authorized G1 cycle4 PASS and terminal G3 cycle3 quota outcome
are recorded below; no automatic reset or profile change occurred.


## Final local verification consolidation — 2026-10-04

Root completed the already-authorized WSL validation after confirmed DevOps
termination. The first 81cd29e6 attempt exited1 before native Hermes at the
metadata guard; its earlier real service/transport/history/target proof remains
attributed to that attempt. The narrow guard correction was exercised with
the original Windows interpreter through WSL, exact pinned versions and the
same Docker daemon, then configured Ruff check/format-check passed0.

Fresh cg-smoke-wsl-final-20261004-369c51ea full smoke terminal exit0: current
provider/source equality, both production services, external Ollama, seven
public exchanges, Nginx, completed-history restart, retained-volume recreation,
original Hermes JSON/SSE continuation/replay, actual waiting-tools restart
before effects, compression and target measurements all executed. Windows
full cg-smoke-win-final-20261004-5f34c9e2 exit0 is preserved separately. Scoped
down(no-v)0 removed each smoke's containers/network and retained its volume.

Root administrative consolidation owns ONLY README.md, docs/runbook.md,
docs/hermes-compatibility.md, docs/verification.md, docs/api.md and
docs/dependencies.md status/evidence text, after confirmed owner termination.
No shared contract, manifests/lockfiles, runtime, API or accepted-profile edit.
This is no independent verdict or G1 fix/fourth-cycle attempt.

Current versioned evidence: live-windows-compose.json, live-windows-hermes.json,
live-wsl-compose.json, live-wsl-hermes.json, wsl-client-guard.json and
completion.md. G1 is PASS4/4; G2 is BLOCKED3/3; G3 is BLOCKED3/3 with no
terminal verdict; G5/G6 reviews remain OPEN0/3. G0/G4 preserve independent PASS2/3. All requested workers are terminal
completed/errored; no required worker is active. Native Linux Hermes was not
installed: WSL Compose invokes the original Windows client explicitly.

Final read-only residue proof is final-residue-audit.json; all exact own
container/network/listener/process queries exited0 and were empty. Root
artifact audit0 checked10 UTF8/whitespace files,34 local links, live source
equality/four native cases and unchanged R01–R11/A01–A16/G0–G6 counters.


## Usage recovery wave — explicit user G1 exception

User reports account usage refreshed and authorizes proceeding with quota-
blocked work. In the explicit clarification, user selected: "Authorize one
additional G1 review attempt" with G2/all other budgets unchanged. Historical
G1 cycle3 remains unable to complete; its counter is not reset. Reserve G1
cycle4/user-exception attempt BEFORE resumed synthesizer invocation, cap4
for this group only. Non-PASS/cannot-complete cycle4 is terminal; no automatic
fix/fifth attempt. G2 remains BLOCKED3/3, engine frozen at b8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6.

- [-] [review] Existing custom review-agent instance review_g1_c3 resumes as
  G1-contracts cycle4, one explicit quota-recovery attempt, no analysts. Sole
  writable file review.md append. Exact25 read-only G1 files are original26
  bootstrap files minus main.py serially transferred to API; enumerated in
  resumed handoff. Current compatible addons/strict pinned interfaces and
  baselineF1/F2 revalidated through actual pinned test-contract/lint/dev
  target checks and coherent consumers. Source/profile/pins frozen; no live
  effects/listeners/production edits. G2 F5 remains a separate blocker. Root
  waits terminal before any G3/G5/G6 reviewer writes review.md.
- [-] [devops] Existing custom devops-agent devops_delivery resumes narrowly
  for G5-delivery final evidence reconciliation and own-fixture backup/restore
  drill. Writable only README.md, docs/runbook.md, docs/hermes-compatibility.md
  and docs/verification.md; ignored newly-owned .venv delivery-recovery fixture/
  log/proof files only. Remaining original delivery/source files are read-only,
  especially smoke_compose.py root guard correction. No contract/manifest/
  locks/API/runtime/review/artifact/config/model edits. Use already-cached
  immutable production images and unique new owned projects/empty volumes,
  no user volume/data access or replacement; retain own originals/backups/
  restored copies and scoped down(no-v). Prove actual production stop/copy/
  isolated restore/permissions/integrity/readiness/graph/hash/history checks.
  Historical Windows/WSL live proof/source equality must be harvested, not
  needlessly rerun inference/tool effects. Exact commands/exits/source/image
  identities/residue returned; remote CI remains unexecuted/no push. Root
  waits both requested workers before wave consolidation.

G3 re-review remains next within unchanged1/3 budget; G5 initial independent
review0/3 follows coherent delivery evidence. G6 requires G2–G5 and remains
held on the known G2 terminal blocker, not renamed or consumed prematurely.


## G1 result harvested; independent G3 recovery review

G1 cycle4 customreviewer terminal PASS/zero findings; root read full section,
verified all25 recorded current source hashes, latest test-contract228+9/lint/
five targeted runtime/wrapper/pin/evidence probes all0. Historical cycle3
quota failure preserved; current cap4 exception exhausted with PASS, no reset.
Whole recovery wave remains pending DevOps and following requested G3 result;
this is individual result harvesting, not premature wave completion.

- [-] [review] Existing review-agent review_g1_c3 reused as the unique sole
  synthesizer for G3-proxy cycle2/3, reserved BEFORE resume; no analysts.
  Writable review.md appendONLY; exact17 G3 files read-only from original
  review_g3_c1 handoff. Independently verify corrected strict UTF8 SSE framing/
  normalized JSON encoding F1/F2 and complete current API/bridge semantics,
  required production native/direct gates through source-matched Windows/WSL
  proof. Fresh focused277/provider109/contract/drift/configuredRuff or necessary
  targeted adversarial cases; no listeners/inference/tools/containers/source
  edits. OriginalG3cycle1 FAIL remains history, current counter2/3. G1PASS4/4;
  G2F5BLOCKED3/3 separate/frozen. DevOps four docs/newignored backup fixtures
  active on disjoint writes; root waits all requested results before final
  wave consolidation. No other review.md writer.


## G3 cycle2 FAIL harvested; final available scoped correction

G3 reviewer terminal FAIL/oneMedium F3: escaped unpaired high/low model IDs
accepted by HttpOllamaAdapter.models lead to public /v1/models500 storage_error
instead of sanitized502 upstream_error. Valid supplementary pair200; eachone
mock inventory call/no inference/effects/leases. Prior completion/SSE F1/F2
CLOSED, required previous real live gates source-matched/executed. Root read
full review and verified17 current source hashes before any correction.

- [x] [coding] Root degraded fallback owns ONLY
  backend/app/providers/ollama.py, backend/tests/providers/test_ollama.py and
  backend/tests/api/test_chat.py for G3-C2-F3 after both replacement coding
  agents positively errored from the account usage limit. User's earlier
  explicit “You may proceed this part” authorizes this exact fallback. Regression
  first adapter+composed GET/v1/models high/low unpaired scalars and valid
  supplementary pairs pass with exact 502/upstream_error or 200 behavior,
  one inventory call and no effects/leaks. Minimal provider models() UTF8
  validation only; baseline g3-inventory-baseline.json proves all other
  provider/module AST unchanged. Affected61, focused283, full593, Ruff3,
  contract export and repository lint/test-contract all exit0. No listeners,
  live inference/tools, docs/review edits or product scope expansion. Current
  image Windows/WSL inventory validation passes in
  g3-current-image-evidence.json; terminal G3 review cycle3 was then ready and
  is superseded by the terminal quota outcome below.

Delivery source reconciliation for this inventory-only change completed with a
current backend image and isolated Windows/WSL callers. Direct composed app
inventory/health probes passed valid supplementary IDs as200 and high/low
unpaired IDs as502/upstream_error, with zero inference/tool effects and no
admission leaks. Image/source IDs are in g3-current-image-evidence.json. Earlier
full native proof remains source-attributed to old provider bytes and is not
relabeled current-source. Terminal G3 review cycle3 is ready; no required live
criterion was silently waived. DevOps backup logical audit0 remains evidence,
not an independent G5 verdict. G2 engine/profile remains frozen and
  BLOCKED3/3.

## G3 terminal independent review reservation — cycle 3/3

- [-] [review] Existing custom review-agent review_g1_c3 resumes as the sole
  G3-proxy synthesizer for terminal cycle3/3, reserved before invocation after
  the scoped F3 correction and current-image Windows/WSL inventory proof. Only
  `.codex/specs/cognitive-graph-mvp/review.md` may be appended. Read-only scope
  is the same exact17 G3 files plus current three-file source delta,
  g3-inventory-baseline.json, g3-fix-evidence.json and
  g3-current-image-evidence.json. Reprove F3 high/low invalid inventory IDs,
  valid supplementary ID, health/error mapping, cleanup and no substitution;
  recheck prior F1/F2 closure and focused/API/contract/Ruff/drift evidence.
  Windows/WSL current image evidence is attributed coordinator execution, not
  reviewer live inference. G2 F5 remains frozen BLOCKED3/3 and is outside this
  group. Cycle3 non-PASS or inability to complete is terminal: no fourth G3
  review, replacement, automatic fix, budget reset, or artificial split.
  Root records the reviewer outcome before scheduling any G5/G6 review-file
  writers.

## G3 terminal cycle 3/3 quota outcome

- [!] [review] Existing custom `review_g1_c3` was resumed for the reserved
  terminal G3-proxy cycle3/3. The agent immediately terminated with the
  positive account usage-limit error: “You’ve hit your usage limit. Upgrade to
  Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage
  to purchase more credits or try again at 10:46 PM.” No reviewer report,
  verdict, or `review.md` append was produced. This is a terminal inability to
  complete under the three-cycle rule; it is not PASS and no severity is
  fabricated. Current correction tests and Windows/WSL inventory evidence are
  retained as coordinator evidence only.
- G3 is **BLOCKED3/3**. Do not spawn a fourth/replacement review, reset the
  counter, rename/split the group, or widen the degraded coordinator fallback.
  The F3 correction remains source- and image-validated; the required
  independent synthesizer gate is open.

## User-authorized one-time recovery exceptions — 2026-10-04

The user explicitly requested one more attempt for both listed blockers. This
is a recorded exception to the normal terminal-cycle rule, not a reset: the
original G2 and G3 counters remain 3/3, all prior findings stay authoritative,
and each group receives at most one bounded recovery attempt. G2 implementation
and G3 review are file-disjoint and may run concurrently. Any further attempt
requires a new explicit user disposition.

- [!] [coding] `coding_g2_exception` was dispatched with the exact scope below
  and immediately terminated with the account usage-limit error. No G2 source
  or test file changed, and no F5 fix/review evidence was produced.
- [!] [coding] `coding_g2_exception` owns only
  `backend/app/runtime/engine.py` and the existing runtime tests needed to
  close F5. Preserve accepted Draft 3 support; add dialect-aware traversal and
  rebasing for schema-valued `extends` and `type` alternatives, literal data,
  resource boundaries, and original-good/original-bad runtime/SQLite proof.
  No profile narrowing, DTO/contract/lock/API/provider edits, or review-file
  writes. Run the exact locked runtime/focused/full tests and Ruff; return
  source hashes and exit codes. Root waits for this terminal result before any
  G2 exception review.
- [!] [review] `review_g3_exception` was dispatched with the exact scope below
  and immediately terminated with the account usage-limit error. No reviewer
  report or `review.md` append was produced.
- [!] [review] `review_g3_exception` is the sole writer of `review.md` for one
  user-authorized G3 recovery review. Read-only exact G3 provider/bridge/API
  scope plus current correction evidence; independently recheck F1/F2/F3,
  current focused/full/contract checks, and current Windows/WSL inventory
  evidence. No product edits, no G2 files, no fourth automatic retry, and no
  review verdict before the agent returns.

## User-authorized recovery outcome

The one G2 implementation attempt and one G3 review attempt authorized above
were both consumed by immediate positive account usage-limit failures. The
original counters remain G2 3/3 and G3 3/3; the exceptions do not create a
new automatic budget. No product files, contracts, profiles, locks, or review
verdicts were changed. Further work requires a later explicit disposition and
available agent quota.

## 2026-10-05 — User-authorized medium-reasoning retry

The user explicitly said “TRY AGAIN. Use 1 step lower reasoning.” Authorize
one new bounded G2 correction and subsequent independent review, and one G3
independent review. Preserve every prior attempt and consumed counter. G2 has
three historical synthesizer attempts; G3 has four (the original three plus
the quota-failed user exception). Reserve G3's fifth synthesizer attempt now
as the second explicit user exception; G2's fourth review will be reserved
only after its correction passes verification. No automatic follow-on retry.

Installed role profiles fix reasoning at high. Generic agents explicitly
using the installed role instructions will execute at medium, preserving
coding model gpt-6.1-sol and review model gpt-6-astra. Project/plugin profiles
are not reconfigured. These executions are not claimed as custom-role spawns.

- [-] [coding] `coding_g2_medium` owns exactly
  backend/app/runtime/engine.py, backend/tests/runtime/test_loops.py,
  backend/tests/runtime/test_scheduler.py, backend/tests/runtime/test_recovery.py.
  Close F5 accepted Draft3 schema-reference rebasing without changing accepted
  semantics, literals or resource boundaries. Contracts, locks, other product
  modules and all artifacts are read-only. Regression-first runtime/SQLite
  proof; locked runtime/full backend and scoped Ruff checks. No live effects.
- [-] [review] `review_g3_medium` owns only review.md append for G3 attempt5,
  under this explicit exception. The original seventeen G3 files and current
  correction/source/image/live evidence are read-only. Reprove F1/F2/F3 and
  assigned acceptance via pinned focused, contract and lint checks; no product
  edits, listeners or inference/tool effects. Root waits for both workers.

## 2026-10-05 — Recovery wave harvested; G2 attempt4 reserved

Both requested medium agents returned terminal results. G3 attempt5 independent
PASS with zero findings; reviewer freshly ran focused283, contract231+9/drift,
Ruff17, inventory/health ASGI and AST/live-source audits. Root read the full
review append. G3 review ownership is released; earlier attempts remain consumed.

G2 coding owner changed only engine.py and test_loops.py. Definitive F5
fail-first8failed/6passed exit1; corrected14passed exit0; runtime219 and full
backend612 passed; Ruff4 check/format exit0. Root verified new engine SHA
7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f and
test_loops SHA f574690ba105d27ae700ab1602a46b75433e6bc72ab20944cf3c9dc3db3f0f5f.
Earlier reproduction fixture mistakes are preserved in g2-recovery-evidence.json.
No independent G2 PASS or current-engine live image claim is made yet.

- [-] [review] Reserve `review_g2_medium` as sole G2-runtime synthesizer
  attempt4 (one explicit user exception) before spawn. Writable review.md
  append only; read-only original twelve runtime/storage files plus current
  two-file F5 delta and evidence. Reprove accepted Draft3 schema locations,
  original-good/original-bad emitted requests, scheduler/SQLite/replay/policy
  invariance, prior F1–F4 closure; locked runtime/full backend/contracts/lint
  as appropriate. No product edits or effects. G3 PASS5/5 is separate. Root
  waits the final verdict; no automatic attempt5 or new fix wave.

## 2026-10-05 — Terminal medium-reasoning outcomes

- [x] [coding] G2 F5 correction delivered in engine.py/test_loops.py, exactly
  the two declared edits; definitive fail-first and successful module/full
  checks preserved in g2-recovery-evidence.json. Independent G2 attempt4
  confirms original F5 closure, not whole-group acceptance.
- [x] [review] G3 attempt5 PASS/zero findings, authoritative review.md section;
  no sixth attempt or new automatic budget. Generic Astra/medium execution
  follows installed review instructions under the explicit user override.
- [!] [review] G2 attempt4 FAIL/one Medium F6. Original-good/original-bad
  validation and public DTO accept a Draft2020-12 root referencing a Draft3
  child with single-valued extends. Controller embedding adds a resource ID;
  pinned referencing crawling then raises AttributeError. Real scheduler /
  temporary SQLite commits failed/upstream_error with two fake provider calls,
  zero success envelopes and unchanged policy. Exact reproducer and hashes in
  review.md. Preserve accepted profile; no automatic fifth attempt/fix wave.
- [x] [documentation] Root owns status-only reconciliation in README.md,
  docs/api.md, docs/dependencies.md, docs/verification.md, docs/runbook.md and
  docs/hermes-compatibility.md, after all requested workers returned. No
  contracts/locks or remaining product changes. Older delivery evidence is
  historical; changed engine production reconciliation remains OPEN.

Root independently ran repository lint exit0, read both complete reviewer
reports, and checked source hashes. Current G2/G3 retry is concluded with the
concrete F6 acceptance blocker. G5/G6 reviews remain OPEN0/3; no whole-MVP PASS.

## 2026-10-05 — User authorizes step 1: F6 fix and independent review

The user explicitly requests validation step1 (fix G2 F6 and pass independent
review). Authorize one scoped correction and one subsequent G2 review attempt5
as a second explicit review exception. Prior four synthesizer attempts remain
consumed. Medium reasoning and the same Sol/Astra model assignments persist;
reuse the terminal medium instances. No step2 production smoke or step3 G5/G6
review is included in this request. No automatic further fix/review if non-PASS.

- [!] [coding] Existing `coding_g2_medium` was dispatched for this exact
  scope and immediately terminated with the account usage-limit error (retry
  available after Oct 6, 2026 12:13 AM). No engine/test/artifact file changed,
  so the F6 fix and its attempt5 review were never started.
- [!] [coding] Existing `coding_g2_medium` owns exactly
  backend/app/runtime/engine.py and backend/tests/runtime/test_loops.py.
  Reproduce exact accepted modern-root/Draft3-child single-extends F6 through
  original and emitted validation, scheduler/SQLite and reconstruction/replay;
  preserve literals, resource boundaries, references, dialects, immutable
  policy, invalid-output rejection and F1–F5 fixes. No dependency/contract/API
  or other product/artifact writes. Run regression-first, locked runtime/full
  tests and scoped Ruff; return commands/exits/hashes and remaining gates.
- [ ] [review] Existing `review_g2_medium` queued as sole independent G2
  attempt5 reviewer after stable correction. Writable review.md append only;
  original12 runtime/storage files and exact new2file delta are read-only.
  Reprove F6 plus F1–F5 closure and assigned G2 acceptance; root reserves the
  counter before dispatch and waits for every requested result.

## 2026-10-06 — Refreshed-quota continuation of authorized step 1

User requests one step forward with refreshed quota. Resume the approved F6
correction and its queued independent G2 attempt5. Fresh agent inventory has
only root; prior medium instances are unavailable, so scoped replacements
are needed. Current engine7a9ccb1e and loopsf574690b hashes match the last
reviewed state. No partial coding edit or fifth synthesizer spawn occurred
during the previous quota-failed correction. Review consumption remains4.

- [-] [coding] `coding_g2_f6_oct6` replaces only the unfinished two-file scope:
  backend/app/runtime/engine.py and backend/tests/runtime/test_loops.py.
  Generic Sol/medium consumes installed coding-role instructions, preserving
  the model matrix and explicit reasoning preference. Reproduce exact F6,
  preserve all schema/reference/literal/policy semantics, prove scheduler /
  SQLite/reconstruction/replay and invalid-output rejection. Run locked
  targeted, runtime/full and Ruff checks. All other files are read-only.
- [ ] [review] Queue one independent generic Astra/medium reviewer for G2
  attempt5 after correction succeeds. Only review.md append writable. Reserve
  counter before spawn; no automatic sixth attempt or scope expansion.

## F6 reference-preservation advisory during correction

- [-] [sa] `sa_g2_f6_oct6` owns only sa-review.md append, generic Astra/medium
  consuming installed sa-agent instructions. Read current engine/tests and
  pinned jsonschema/referencing implementation; advise a bounded fix for
  Draft3 single-extends crawling without altering recursive/dynamic anchors,
  literal data, escaped/local/absolute references or caller policy. No product,
  dependency, other artifact or review.md writes; no verdict/counter consumed.
  Coding owner remains sole engine/test_loops writer. Root waits both terminal
  handoffs before the queued independent G2 attempt5.

## F6 bounded dependency investigation — 2026-10-06

- [x] [coding] Initial two-file correction terminated without a safe fix.
  Engine restored to reviewed SHA2567a9ccb1e; 28 unweakened new regressions
  remain. Existing backend612 and runtime/storage231 pass only with those
  regressions explicitly excluded; no F6 acceptance or new review consumed.
- [-] [coding] Reuse `coding_g2_f6_oct6` for isolated copied-package experiment
  under `.f6-probe/` only. Narrow referencing0.37.0 Draft3 crawler object/array
  correction; no production, venv, dependency manifest/lock or global edits.
  Confirm import provenance, run all28 regressions unchanged plus existing
  runtime/storage using locked tooling. Engine/test ownership released.
- [-] [sa] Reuse `sa_g2_f6_oct6`, only sa-review.md append, for reproducible
  deployment recommendation if probe succeeds. No verdict/review consumed.
  Root waits both results. Any implementation needs a new exact single-owner
  dependency/bootstrap handoff; current experiment grants no such writes.

## F6 dependency correction ownership — 2026-10-06

Isolated copied referencing experiment:28 F6 cases and259 runtime/storage
cases pass, baseline engine unchanged. Proceed with the proven narrow patch
as a local exact wheel; no schema rewriting/profile narrowing.

- [-] [coding/bootstrap] `coding_bootstrap_f6_oct6`, sole writer of
  backend/pyproject.toml, backend/uv.lock,
  backend/vendor/referencing-0.37.0+cg.1-py3-none-any.whl,
  backend/vendor/referencing-provenance.json, backend/vendor/README.md,
  scripts/rebuild_referencing.py, backend/tests/contracts/test_referencing_patch.py,
  docs/dependencies.md. Reproduce from prior locked upstream wheel/hash,
  retain MIT license, deterministic metadata/RECORD, exact direct pin/path;
  preserve all other dependency pins. Native locked sync, import/source audit,
  reproduction and wrong-hash failure; Draft3 object/array and Draft4 crawler
  regression, new28 cases, full backend/contracts/lint. No engine, shared
  contracts, API, Docker, other docs/artifacts or frontend writes.
- [-] [devops] `devops_f6_oct6`, separate owner for backend/Dockerfile, .dockerignore,
  docs/api.md and README.md only; precise handoff follows bootstrap wave.
  Copy only exact corrected wheel before locked install, production import
  assertion; truthful known-issue/docs status. Native/Linux build/install proof
  required, not a source-matched Hermes/Ollama live claim.
- [x] [review] Authorized G2 attempt5 was reserved and spawned after stable
  implementation. It terminated at the account usage-limit error before a
  verdict or review.md append. The fifth attempt is consumed under the
  non-resetting G2 budget; no sixth automatic attempt/fix or budget reset.

## G2 attempt5 quota outcome — 2026-10-06

`review_g2_f6_oct6` ran as the sole independent synthesizer with Astra/medium
after the exact reservation above. It independently returned fresh runtime/
storage259 and contract241Python+9frontend evidence before the account usage
limit terminated the turn. It did not append review.md or issue PASS/FAIL.
The attempt is nevertheless consumed because the synthesizer was spawned.
This is missing required reviewer evidence, not a PASS and not an
implementation defect. G2 remains blocked pending user disposition or a new
explicitly authorized exception; automatic sixth review/fix is forbidden.

## G2 authorized attempt5 reservation — 2026-10-06

Both bootstrap/delivery owners returned terminal success and released files.
Production wheel version0.37.0+cg.1 is reproducible; native650/backend,
259/runtime-storage,241Python+9frontend/contracts, root lint and Docker image
offline F6 proof pass. Engine remains unchanged7a9ccb1e. Source provenance
and commands are in g2-f6-evidence.json; no real inference/tool execution.

- [-] [review] `review_g2_f6_oct6`, sole independent synthesizer, generic
  Astra/medium consuming installed review-role instructions. Reserve and
  consume G2 attempt5 here before spawn, retaining original1–3 plus exception4
  and all historical findings. Authorized by user step1/refresh continuation;
  no sixth automatic attempt or post-terminal automatic fix wave.
  Writable review.md append only; all runtime/storage12 files, regression
  delta, bootstrap8/delivery4 files and proof artifacts are read-only. Verify
  F1–F6 closure and assigned A03–A06/A08–A10/A13–A14/A16 with fresh locked
  tests, installed source/wheel/provenance/default-validator parity, no remote
  retrieval, literal/reference/dialect/resource/immutable policy preservation,
  archive and exact dependency delta, Docker proof adequacy. Independent
  targeted/full/runtime/contracts/lint and adversarial counterexamples; no
  missing required G2 evidence on PASS. G5/G6/source-matched live gates remain
  separate OPEN; no whole-MVP PASS from this group's verdict. Root waits
  reviewer terminal return before consolidation or closure.
