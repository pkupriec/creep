# Cognitive Graph MVP — Current State

Updated: 2026-10-06. This is the compact coordination entry point. The
authoritative requirements and acceptance definitions remain in
`requirements.md`, `spec.md`, and `acceptance.md`; historical detail remains in
`tasks.md`, `decisions.md`, `review.md`, and `sa-review.md`.

## Product status

The implementation is locally testable, but the MVP is not fully accepted.
Current-source Hermes/Ollama Windows/WSL2 validation passed; the remaining gates
are independent G5/G6 reviews. See live-current-summary.json for exact commands,
source/dependency identity, teardown and the limited timing sample.

| Group | State | Review budget | Current gate |
| --- | --- | ---: | --- |
| G0 research | PASS | 2/3 | Hermes continuation and React Flow selection recorded |
| G1 contracts | PASS | 4/4 | User-authorized quota recovery; exhausted |
| G2 runtime | PASS; F1–F6 closed | 6/6 | Independent attempt6; prior quota termination retained |
| G3 proxy | PASS | 5/5 | User-authorized medium retry; exhausted |
| G4 UI | PASS | 2/3 | Independent cycle 2 closed assigned findings |
| G5 delivery | REVIEWING | 1/3 | Current-source live evidence harvested; independent review reserved |
| G6 integration | OPEN | 0/3 | Cross-group acceptance and current-source live reconciliation remain |

## Stable F6 evidence

The accepted-schema profile and runtime engine are unchanged. The exact local
wheel `referencing==0.37.0+cg.1` fixes only object-valued Draft3 `extends`
crawling. Upstream wheel SHA256:
`381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231`.
Local wheel SHA256:
`a84fbf0a7365b1a0592392a2859914de38f37258f1bca97d78fce582a102804c`.
Patched source SHA256:
`d71d7e00650fa3411b1957b1517d95a515461d7d428753eaf7a2719c10482c86`.
Engine SHA256:
`7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f`.

Evidence file: `g2-f6-evidence.json`.

## Verified commands

All commands below exited 0 with the pinned project tooling:

```text
uv --system-certs run --project backend --locked pytest backend/tests -q
python scripts/dev.py test-runtime
python scripts/dev.py test-contract
python scripts/dev.py lint
docker --context desktop-linux compose -p cg-f6-image-proof-20261006 -f compose.yaml config --quiet
docker --context desktop-linux build --file backend/Dockerfile --tag cg-f6-backend-proof:20261006-local1 .
```

Results: backend 650 passed; runtime/storage 259 passed; contract 241 Python
plus 9 frontend; lint, format, drift, and both TypeScript projects passed. The
current coordinator checks also passed `npm --prefix frontend test` (21),
`python scripts/dev.py test-e2e` (six browser cases,15.7s) and
`python scripts/dev.py build` (typecheck/production build). Browser cases use
real native backend/SQLite with a mock upstream, separately from live smoke.
The
network-isolated image proof passed under UID 10001 with the corrected wheel,
valid/invalid F6 payloads, immutable input, Draft3/Draft4 crawling, and
deliberately denied remote retrieval. Image ID:
`sha256:ffc31653bf7e2ea11ed9cf22497bb67c739ae918c412232f76ebd91cd5c5e07d`.

## Coordination rules for the next step

Read this file plus the relevant requirement/spec sections and evidence JSON.
Read the full historical ledgers only when reviewing their assigned history.
G2 attempt6 PASS was harvested; no seventh G2 review or new fix wave is
authorized automatically. See review.md's final G2 section for exact evidence.
Do not rerun live inference or tool effects merely to reproduce historical
evidence. Source-matched live validation must record current source/image
hashes and remain distinct from static or mock tests.
