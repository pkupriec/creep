# Acceptance evidence ledger

Authority: unchanged A01–A16 in `spec.md` and root specification section 10.
This ledger maps required evidence; planned checks are not executed checks.
G0 research PASS proves only its pinned experiment, not these production gates.

| ID | Required production proof | Responsible groups | Current evidence / gate |
| --- | --- | --- | --- |
| A01 | Actual pinned Hermes selects published `cg/synthesis`, completes graph and receives final answer | G3, G6 | OPEN; pinned G0 research passed; production Hermes smoke still required |
| A02 | Physical-model chat/multiturn JSON/SSE and tool request/result through production proxy, mock and real upstream | G3, G6 | OPEN |
| A03 | Controlled fake provider proves both diamond experts start before either finishes; synthesis sees both in lexical port order | G2, G6 | OPEN |
| A04 | Named required/optional inputs, fan-out/fan-in; missing required input causes 400 and zero provider calls | G2, G4, G6 | OPEN; graph suite52 passed; runtime71 passed before current final fix; production HTTP/SQLite integration48 passed; current independent runtime/UI/integration gates pending |
| A05 | Seeded draft/critique loop continues twice then stops; per-iteration data isolated; no exit payload before stop | G2, G6 | OPEN |
| A06 | Endless continue ends with budget error; missing/invalid control and undeclared/cross-scope cycles rejected | G2, G4, G6 | OPEN; graph suite52 passed; runtime71 passed before current final fix; production HTTP/SQLite integration48 passed; current independent runtime/UI/integration gates pending |
| A07 | Actual pinned Hermes reads dedicated fixture; exact owning activation resumes and final payload reaches synthesis | G3, G6 | OPEN; pinned G0 research passed; production Hermes smoke still required |
| A08 | Colliding provider IDs across owners remain isolated; serialized unknown effects and parallel=false obeyed; partial/full result routing | G2, G3, G6 | OPEN |
| A09 | Independent identical turns get distinct runs; latest segment routing, unknown IDs, changed results, concurrent replay produce no extra calls | G2, G3, G6 | OPEN |
| A10 | Stop/restart production process after delivery; original tool IDs complete same run; uncertain active calls interrupted without rerun | G2, G3, G6 | OPEN real Hermes/container gate; actual native backend process restart with mock Ollama preserved pending original ID and completed same run in browser E2E; uncertain active interruption covered HTTP/SQLite tests. G0 object reconstruction remains separate |
| A11 | Parsed JSON/SSE tool deltas, finish_reason and DONE; final stream excludes internal/control text; post-start errors never fake stop | G3, G6 | OPEN |
| A12 | Real browser CRUD, ports, prompts, feedback seed/membership, import/export and publish; reopened state fetched from API; restart persistence | G4, G6 | OPEN independent review; actual-backend Playwright four scenarios passed (12.8s): editor/revision/import/export/API reload, completed history process restart, waiting original tool-ID process restart/manual result, active snapshot/cancel. Mock Ollama; real Hermes/container gates separate |
| A13 | Revision conflict leaves file unchanged; editing draft during run leaves canonical snapshot/hash unchanged; drafts absent from model list | G2, G4, G6 | OPEN; graph suite52 passed; runtime71 passed before current final fix; production HTTP/SQLite integration48 passed; current independent runtime/UI/integration gates pending |
| A14 | Deterministic timeout/upstream failure/cancel/late-result tests; fixed tool TTL, queue overflow 429, separate queue/active/wait time | G2, G3, G6 | OPEN |
| A15 | Built production Compose on Windows/WSL2: external Ollama reachability, API/UI/Hermes smoke and restart history persistence | G5, G6 | OPEN; actual pinned backend image and Linux SQLite3.40.1 persistence/fsync/symlink probe passed; Windows/WSL config helpers passed. Current complete image/startup/routing/waiting restart/Hermes full smoke pending |
| A16 | Strict HTTP/schema/path limits, auth namespace isolation, synthetic-token log checks, global inference/admission bounds across graph/direct jobs | G1, G2, G3, G4, G5, G6 | OPEN; strict contract suite163 Python/nine frontend, graph path/revision52, production HTTP/SQLite48 pass; synthetic auth/namespace/global graph-direct pool checks included. Current full-suite/review/Linux/live gates pending |

## Evidence rules

- Record exact commands, pinned interpreter/tool, exit code, parsed counts and relevant paths. Include the commit/source state exercised.
- Unit/contract tests use deterministic fake providers/clocks; integration tests use actual mock HTTP/SSE; UI checks run a real browser against the backend.
- Real Hermes/Ollama and Windows/WSL2 Compose checks remain separate live gates. Availability checks and static config validation do not satisfy them.
- Each independent group requires a review-agent synthesizer PASS within its own non-resetting three-cycle budget. A PASS does not erase an open required gate.
- If enforcement or missing environment prevents live checks, finish independent work and retain OPEN with exact runnable instructions. Never label unexecuted checks passed.
- No inference response disk cache, effectful retries or minimum-concurrency rule is introduced by this ledger.

## Latest executed component evidence (not final acceptance)

- API owner terminal command `uv --system-certs run --project backend --locked pytest backend/tests/api backend/tests/integration/test_acceptance.py -q`: exit0,48passed. Actual handlers/SQLite with mock upstream; diamond barrier, named inputs, seeded two-continue loop, budget failure, owner collisions, partial/fixedTTL/exact first-next replay, reconstruction/uncertain interruption, shared admission/inference, JSON/SSE/tool framing/error/disconnect/namespace checks. Source API hashes preserved in owner terminal and coordinator decisions. This is not real Ollama or process/container restart proof.
- Root fresh `python scripts/dev.py test-contract`: exit0,163Python/ninefrontend, generated contracts unchanged. Root fresh `python scripts/dev.py test-runtime`: exit0,71passed before final F4/format fixwave2. Prior full backend336passed/9failed and lint sixfindings occurred during concurrent runtime fail-first edits; current combined checks remain open. No passing assertion supersedes required independent review.
- Native adapter default-thinking SSE text/tools passed; bounded real JSON text plus native toolrequest/manualresult passed against Ollama0.33.3/gemma4:12b pinned digest, zero tools executed. These are transport subsets, not public production proxy/Hermes acceptance.

- Latest ROOT `python scripts/dev.py test` exit0:475allbackend in33.93s and21frontend; ROOT `python scripts/dev.py lint` exit0:Ruff49files/generateddrift/strictTS. Includes finalruntime212cases, API48, graph52 and contract/provider/tools163. Earlier concurrentfailfirst combinedfailures are closed; G2lastreview/G4reloadcorrection/otherindependentreviews/livegates remainOPEN.
