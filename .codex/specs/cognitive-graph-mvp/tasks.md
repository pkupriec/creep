# Cognitive Graph MVP tasks

Authority: root specification v1.1, section 12; requirement IDs R01–R11 and scenarios A01–A16 remain unchanged.
Main thread owns artifacts, research consolidation, decisions, and orchestration. No main implementation begins before G0 passes.

## Stable groups and non-resetting review budgets

| Group | Outcome | Dependency | State | Synthesizer spawns consumed |
| --- | --- | --- | --- | --- |
| G0-research | Proven Hermes continuation and editor choice | None | Review pending | 1/3 |
| G1-contracts | Frozen schema/API/scheduler/continuation contracts | G0 | Waiting | 0/3 |
| G2-runtime | DAG, loops, durable state/recovery | G1 | Waiting | 0/3 |
| G3-proxy | Ollama, Hermes tool bridge, JSON/SSE | G1; integrate G2 | Waiting | 0/3 |
| G4-ui | Editor, files API, history/traces | G1; integrate G2/G3 | Waiting | 0/3 |
| G5-delivery | Compose, CI, runbooks | G1; smoke G2–G4 | Waiting | 0/3 |
| G6-integration | A01–A16, real Hermes/Windows/WSL2 | G2–G5 | Waiting | 0/3 |

G-TEAM-SETUP is a separate, previously exhausted 3/3 PASS group. No setup reviewer is respawned.
Each product group has its own maximum three synthesizer spawns. Record consumption before spawn. Cycle 3 non-PASS is terminal.

## Wave 0 — research

All three named workers must return before consolidation. No recursive delegation. Peer work is concurrent; never revert peer changes.

- [x] [coding] `coding_rd1`, G0/RD1: prove pinned installed Hermes continuation. Writable files only: `experiments/hermes_bridge.py`, `experiments/test_hermes_bridge.py`, `experiments/hermes-requirements.txt`, `experiments/hermes-traces.json`, `docs/research/hermes-protocol.md`. No edits to Hermes installation/configuration, product code, other artifacts, or dependency manifests. Consume actual installed Hermes protocol at immutable SHA; produce prototype two-node tool continuation, two owners/ID collisions, replay/restart proof and sanitized real traces. A07–A10 research obligations; inspect compression/ID handling/timeouts/iteration limits/streaming. Run: repository-local isolated Python `-m pytest experiments/test_hermes_bridge.py`; document exact interpreter/commands in report. A fake client alone cannot close RD1. Coordinate live Ollama endpoint with `devops_env`; never read secrets or execute tools outside a dedicated test directory. Return exact files, pins, commands/exits, evidence and blockers.
- [x] [coding] `coding_rd2`, G0/RD2: compare existing editors. Writable files only: `experiments/editor/package.json`, `experiments/editor/package-lock.json`, `experiments/editor/tsconfig.json`, `experiments/editor/index.html`, `experiments/editor/src/main.tsx`, `experiments/editor/src/style.css`, `experiments/editor/src/graph.ts`, `experiments/editor/src/graph.test.ts`, `experiments/editor/playwright.config.ts`, `experiments/editor/e2e/editor.spec.ts`, `docs/research/graph-editor.md`, `docs/research/graph-editor.png`. Own these experiment manifests/lockfile only. No product or shared-contract edits. Consume unchanged R04/R05/R08 and RD2; produce diamond, named ports, feedback, membership/seed, prompt edits, JSON round-trip proof, license/version comparison and selection recommendation. Run: `npm --prefix experiments/editor ci`, typecheck/unit/build and pinned Playwright E2E exact scripts; record exits/screenshot. Existing disabled Playwright MCP must remain disabled; use project test dependency only. Return pins, files, commands, recommendation, blockers.
- [x] [devops] `devops_env`, G0 environment evidence: writable only `docs/research/environment.md`. Inspect available Python/Node/Docker/Compose/WSL2/Hermes and external Ollama reachability/version/model inventory using bounded read-only queries, including WSL2 host addressing. No Compose/product/bootstrap/config changes, no model downloads, no credential access, no deployment, no global installs. Consume R10/A15 environment constraints; produce exact safe endpoints and version/runtime evidence to RD1 and coordinator. Run: `docker version`, `docker compose version`, `wsl --list --verbose`, bounded GET Ollama version/tags/models on loopback/reachable documented addresses; record independent command exits. Return missing facts and exact live-validation procedure if unavailable.

## Later waves

## Architecture advisory during G0 — no frozen contracts yet

- [x] [sa] `sa_g0`, architecture advisory for future G1; writable only `.codex/specs/cognitive-graph-mvp/sa-review.md`. Read unchanged approved specification and G0 evidence; analyze loop SCC/activation initialization, durable identity/replay/restart, one external batch, cancellation/timeout accounting and external network boundaries. No production files, no edits to requirements/design/spec/tasks/decisions/review. Produce specific provisional contracts and risks, not implementation or a formal verdict. Run: evidence-linked analysis of A03–A10/A14/A16 plus current official SQLite/asyncio/Ollama documentation as needed; no runtime PASS. Peer coding research continues. Lead must wait for `coding_rd1`, `coding_rd2`, and `sa_g0` before G1 consolidation. G0 remains gated on RD1/RD2.

Section 12 of the authoritative source defines G1–G6. Exact writable files, shared bootstrap/manifest ownership and frozen contracts will be expanded here after G0 succeeds, before any implementation handoff.
