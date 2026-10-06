# Cognitive Graph MVP — Current State

Updated: 2026-10-07. MVP IMPLEMENTED AND VERIFIED. All mandatory R01–R11 and
A01–A16 gates closed by independent G6 review; original requirements unchanged.
Read this compact entry point before historical ledgers.

| Group | Independent result | Consumed review budget |
| --- | --- | ---: |
| G0 research | PASS | 2/3 |
| G1 contracts | PASS | 4/4, explicit user quota exception |
| G2 runtime | PASS; F1–F6 closed | 6/6, explicit user exceptions |
| G3 proxy | PASS | 5/5, explicit user exceptions |
| G4 UI | PASS | 2/3 |
| G5 delivery | PASS; F1/D1 closed | 2/3 |
| G6 integration | PASS; A01–A16 closed | 1/3 |

Verified evidence, all final checks exit0:

- [G5 correction](g5-fix-evidence.json): 661 backend tests,11 lifecycle
  regressions, full lint/52 formats/generated drift/both TypeScript projects.
- [G2 correction](g2-f6-evidence.json): 259 runtime/storage,241 Python+9
  frontend contracts,28 F6 regressions,10 wheel integrity checks.
- [UI evidence](current-ui-evidence.json): 21 unit tests,six real-backend
  browser scenarios, production build.
- [Current live summary](live-current-summary.json): both full Windows/WSL2
  Compose with external Ollama and original pinned Hermes JSON/SSE; authentic
  fixture reads, owner continuation/replay, waiting-ID restart, compression,
  history persistence and empty owned container/network residue. Volumes retained.
  All29 app files and installed corrected wheel match; later three-line helper
  error-handler correction is exactly reconciled in G5.
- [Independent reviews](review.md): final G5/G6 sections include fresh11
  lifecycle/52 API-integration tests and source/native-proof audits.
- [Acceptance map](acceptance.md), [completion/setup](completion.md).

No mandatory blockers or open live-validation gates. Optional residuals:
UI “Active duration” displays elapsed time including tool waits (G6-D1 Low);
existing bundle/React Flow notices; one sample per benchmark shape and one
unusable WSL UTC node duration; historical unassigned Windows native exception
not diagnosed by later green suites. Remote GitHub CI, arbitrary user-data
restore/cutover and native-Linux Hermes installation were not executed/claimed.
WSL used explicit Windows-native Hermes interop.

Exact local referencing0.37.0+cg.1 patch fixes Draft3 object-valued extends
without narrowing accepted schemas; pins/provenance/reproduction are preserved.
All historical FAIL/quota results and non-resetting counters remain in Git/
tasks/decisions/review. Product remains local; no push/cloud/global team change.
