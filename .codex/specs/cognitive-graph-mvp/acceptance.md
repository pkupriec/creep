# Acceptance evidence ledger

Authority: unchanged A01–A16 in `spec.md` and root specification section 10.
This ledger maps required evidence; planned checks are not executed checks.
G0 research PASS proves only its pinned experiment, not these production gates.

| ID | Required production proof | Responsible groups | Current evidence / gate |
| --- | --- | --- | --- |
| A01 | Actual pinned Hermes selects published `cg/synthesis`, completes graph and receives final answer | G3, G6 | OPEN; G0 experiment only |
| A02 | Physical-model chat/multiturn JSON/SSE and tool request/result through production proxy, mock and real upstream | G3, G6 | OPEN |
| A03 | Controlled fake provider proves both diamond experts start before either finishes; synthesis sees both in lexical port order | G2, G6 | OPEN |
| A04 | Named required/optional inputs, fan-out/fan-in; missing required input causes 400 and zero provider calls | G2, G4, G6 | OPEN |
| A05 | Seeded draft/critique loop continues twice then stops; per-iteration data isolated; no exit payload before stop | G2, G6 | OPEN |
| A06 | Endless continue ends with budget error; missing/invalid control and undeclared/cross-scope cycles rejected | G2, G4, G6 | OPEN |
| A07 | Actual pinned Hermes reads dedicated fixture; exact owning activation resumes and final payload reaches synthesis | G3, G6 | OPEN; G0 experiment only |
| A08 | Colliding provider IDs across owners remain isolated; serialized unknown effects and parallel=false obeyed; partial/full result routing | G2, G3, G6 | OPEN |
| A09 | Independent identical turns get distinct runs; latest segment routing, unknown IDs, changed results, concurrent replay produce no extra calls | G2, G3, G6 | OPEN |
| A10 | Stop/restart production process after delivery; original tool IDs complete same run; uncertain active calls interrupted without rerun | G2, G3, G6 | OPEN; G0 object reconstruction is insufficient |
| A11 | Parsed JSON/SSE tool deltas, finish_reason and DONE; final stream excludes internal/control text; post-start errors never fake stop | G3, G6 | OPEN |
| A12 | Real browser CRUD, ports, prompts, feedback seed/membership, import/export and publish; reopened state fetched from API; restart persistence | G4, G6 | OPEN; RD2 prototype only |
| A13 | Revision conflict leaves file unchanged; editing draft during run leaves canonical snapshot/hash unchanged; drafts absent from model list | G2, G4, G6 | OPEN |
| A14 | Deterministic timeout/upstream failure/cancel/late-result tests; fixed tool TTL, queue overflow 429, separate queue/active/wait time | G2, G3, G6 | OPEN |
| A15 | Built production Compose on Windows/WSL2: external Ollama reachability, API/UI/Hermes smoke and restart history persistence | G5, G6 | OPEN; diagnostic rejected before execution, no actual backend/container proof |
| A16 | Strict HTTP/schema/path limits, auth namespace isolation, synthetic-token log checks, global inference/admission bounds across graph/direct jobs | G1, G2, G3, G4, G5, G6 | OPEN |

## Evidence rules

- Record exact commands, pinned interpreter/tool, exit code, parsed counts and relevant paths. Include the commit/source state exercised.
- Unit/contract tests use deterministic fake providers/clocks; integration tests use actual mock HTTP/SSE; UI checks run a real browser against the backend.
- Real Hermes/Ollama and Windows/WSL2 Compose checks remain separate live gates. Availability checks and static config validation do not satisfy them.
- Each independent group requires a review-agent synthesizer PASS within its own non-resetting three-cycle budget. A PASS does not erase an open required gate.
- If enforcement or missing environment prevents live checks, finish independent work and retain OPEN with exact runnable instructions. Never label unexecuted checks passed.
- No inference response disk cache, effectful retries or minimum-concurrency rule is introduced by this ledger.
