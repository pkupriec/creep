# Acceptance evidence ledger

Authority: unchanged A01–A16 in `spec.md` and root specification section 10.
This ledger maps required evidence; planned checks are not executed checks.
G0 research PASS proves only its pinned experiment, not these production gates.

| ID | Required production proof | Responsible groups | Current evidence / gate |
| --- | --- | --- | --- |
| A01 | Actual pinned Hermes selects published `cg/synthesis`, completes graph and receives final answer | G3, G6 | OPEN; pinned G0 research passed; production Hermes smoke still required |
| A02 | Physical-model chat/multiturn JSON/SSE and tool request/result through production proxy, mock and real upstream | G3, G6 | OPEN |
| A03 | Controlled fake provider proves both diamond experts start before either finishes; synthesis sees both in lexical port order | G2, G6 | OPEN required G2/G6 review gates; actual HTTP/SQLite mock-upstream diamond barrier test passes in current 49-case API/integration suite; both experts start before either finishes and lexical input order is asserted |
| A04 | Named required/optional inputs, fan-out/fan-in; missing required input causes 400 and zero provider calls | G2, G4, G6 | OPEN required G2/G6 gates; current graph98/runtime212/API+integration49 tests pass; named inputs and missing-input zero-inference behavior exercised; assigned G4 portion independently PASS2/3 |
| A05 | Seeded draft/critique loop continues twice then stops; per-iteration data isolated; no exit payload before stop | G2, G6 | OPEN required G2/G6 gates; JSON and SSE composed HTTP/SQLite seeded two-continue loop tests pass; six browser scenarios include seeded loop traces; final-format schema F5 remains a separate required G2 defect |
| A06 | Endless continue ends with budget error; missing/invalid control and undeclared/cross-scope cycles rejected | G2, G4, G6 | OPEN required G2/G6 gates; graph98/runtime212/API+integration49 exercise endless-loop budget failure and invalid controls/topology; assigned G4 portion independently PASS2/3 |
| A07 | Actual pinned Hermes reads dedicated fixture; exact owning activation resumes and final payload reaches synthesis | G3, G6 | OPEN; pinned G0 research passed; production Hermes smoke still required |
| A08 | Colliding provider IDs across owners remain isolated; serialized unknown effects and parallel=false obeyed; partial/full result routing | G2, G3, G6 | OPEN |
| A09 | Independent identical turns get distinct runs; latest segment routing, unknown IDs, changed results, concurrent replay produce no extra calls | G2, G3, G6 | OPEN |
| A10 | Stop/restart production process after delivery; original tool IDs complete same run; uncertain active calls interrupted without rerun | G2, G3, G6 | OPEN real Hermes/container gate; actual native backend process restart with mock Ollama preserved pending original ID and completed same run in browser E2E; uncertain active interruption covered HTTP/SQLite tests. G0 object reconstruction remains separate |
| A11 | Parsed JSON/SSE tool deltas, finish_reason and DONE; final stream excludes internal/control text; post-start errors never fake stop | G3, G6 | OPEN |
| A12 | Real browser CRUD, ports, prompts, feedback seed/membership, import/export and publish; reopened state fetched from API; restart persistence | G4, G6 | OPEN whole cross-group acceptance; assigned G4 portion independently PASS2/3, six real-backend Chromium scenarios passed15.3s including CRUD/ports/prompts/seeds/loops/import/export/publish/reload/history/manualtools/cancel/immutable snapshots/native process restarts; mock Ollama, actual container/Hermes gate separate |
| A13 | Revision conflict leaves file unchanged; editing draft during run leaves canonical snapshot/hash unchanged; drafts absent from model list | G2, G4, G6 | OPEN required G2/G6 gates; current graph98/runtime212/API+integration49 plus six actual-backend browser scenarios verify immutable publication/snapshot, conflict no-write and draft hiding; assigned G4 portion independently PASS2/3 |
| A14 | Deterministic timeout/upstream failure/cancel/late-result tests; fixed tool TTL, queue overflow 429, separate queue/active/wait time | G2, G3, G6 | OPEN required G2/G3/G6 gates; current deterministic provider/runtime/API tests prove fixed TTL, before-deadline waiting504 versus after-persisted-failure409, cancellation/late results/queue overflow and separate timing without extra inference or checkpoint mutation |
| A15 | Built production Compose on Windows/WSL2: external Ollama reachability, API/UI/Hermes smoke and restart history persistence | G5, G6 | OPEN full Windows/WSL2/Hermes gate; both actual digest-pinned images built; corrected Windows startup healthy and actual unchanged default container-to-Ollama route/storage probe exit0. Two prior Nginx read-only temp-path startup failures and subsequent direct smoke assertion failure retained; Hermes/restart/performance phases not yet reached |
| A16 | Strict HTTP/schema/path limits, auth namespace isolation, synthetic-token log checks, global inference/admission bounds across graph/direct jobs | G1, G2, G3, G4, G5, G6 | OPEN required cross-group gates; current strict contract163Python/ninefrontend, graph98, API+integration49 and backend522 pass; synthetic auth/namespace/global graph-direct concurrency/limits tests included; G4 independently PASS2/3; G2BLOCKED3/3 and real/live/reviews pending |

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

## Required runtime blocker

G2-runtime independentterminalreview3/3 FAIL/BLOCKED: reviewF5 validDraft3 localreference traversal omission. PriorF1–F4closed, current212/475+21/Ruff/contractchecks pass but requiredfinal-controllerformatpreservation remainsfailed. Noautomaticfourthcycle/fix/narrowedprofile; userdispositionrequired. WholeMVPacceptancecannotclosewhilethisrequiredgroupblocked. InitialunreproducedWindowsnativefulltestexception retained as separateverificationdiscrepancy.


## Latest integrated deterministic and G4 independent evidence

- API owner exact `uv --system-certs run --project backend --locked pytest backend/tests -q`: terminal exit0,522passed37.26s; focused `uv --system-certs run --project backend --locked pytest backend/tests/api backend/tests/integration/test_acceptance.py -q`: exit0,49passed6.99s. Deterministic expiry barriers prove acceptedwaitingrequest504 atoriginaldeadline versus freshrequestafterpersistedfailure409run_terminal, withoutTTLextension/inference/checkpointmutation. Test-only verifier correction; productionchat/engine unchanged. The earlier first-wrapper Windows native exception remains unassigned historical risk, not diagnosed by a later green suite.
- G4 independent cycle2 PASS: exact `python scripts/dev.py test-graphs` exit0,98passed3.63s; `npm --prefix frontend test` exit0,21passed; `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, `npm --prefix frontend run test:e2e` and `python scripts/dev.py lint` each exit0. Six actualbackendChromium scenarios15.3s include unchangedservergeneration afterreopen/Apply/Save, preserveduncommitteddrafts, authoritativeconflictreload/sameIDimport, wholeUTF8400beforemutations, validUnicode roundtrip, seededloop and ownbackendprocessrestarts. OriginalpendingID andcompletedhistory persisted. MockOllama only; no realHermes/container inference claim. This closes assigned G4 portions A04/A06/A12/A13/A16, not the whole cross-group scenarios.
- ROOT released actualWindows/WSL2 production smokes only after G4reviewer terminalpositive listenercleanup. Both pinned images already built exit0. Startup/routing/Hermes/compression/performance remain OPEN until fresh terminal evidence.
- All whole-product A01–A16 gates remain OPEN because required G2-runtime is BLOCKED3/3 on F5 acceptedDraft3 extends/type schema localreferences. Passing522/21/98/sixbrowser checks do not prove or repair this failing acceptance behavior.


## Current delivery progression (not terminal live acceptance)

Two actualWindows startup attempts exited1 beforeinference becausefrontendNginx triedcreating /var/cache/nginx/fastcgi_temp onreadonlyroot; secondboundedreproduction captured exactemerg/healthlogs. Deliveryowner corrected only nginx.conf defaultfastcgi/uwsgi/scgi temp dirs to existing writable/tmp and added failure-state capture retaining originalexit. Freshowned cg-smoke-win-fixed-20261004-674d0a1a builtbothimages; backend/frontend HEALTHY, actualcontainerprobe exit0 UID10001/fsync/SQLite3.40.1 WAL/quick_check/jsonschema4.26/currentengine/main plusunchangeddefault host.docker.internal route toOllama0.33.3/pinnedGemma4digest. Fullhelper subsequently exited1 on Expected a successful final JSON completion, exactphase notyetattributed; noHermes/restart/targetphase executed inthatattempt. Allattempts owncontainers/networks removed via down(no-v)exit0, volumesretained. Diagnostic/fixture investigation proceeds onlywithinowneddeliveryfiles, no API/runtime/profile/network/userOllama edits, no successfulpublic/Hermes/fullWSLclaimyet.


## Real public and Windows executed subsets before native observer correction

- Fresh pure directdiagnostic exit0 and subsequentfullWindows417276aa direct phasespassed againstactualcontainer/Nginx/externalOllama0.33.3/pinnedgemma4:12b, sevenordinary/multiturnJSONSSE/native-toolrequest+manualresult exchanges, strictfinish/DONE/unknown404, zero executedtools. InitialstrictfinalJSONassertionfailedwithoutphasecapture; boundedreproductionpasses do notdiagnose/erase that prior unassigned discrepancy.
- ActualWindowsfullhelper executedhealthyservices/read-onlyUID/protection/runtimeNginx/unbufferedSSE, completedhistory actualbackendrestart andsamevolumedown-up/publishedsnapshot, targetdiamond-versus-sequential metrics. Diamond1.515swall0.004944queue3calls/overlap versussequential1.531swall0.006202queue3calls, sameexternalmodel, no guaranteedacceleration.
- NativeHermesJSON actualcg/synthesis/twoguardedRead/compression28→6/pendingID-resultpreservation occurred, but originalSDKobservation onwrongpersistentclient captured0APIcalls/IDs. Wholehelperexit1; required originalrun/IDwaitingcontainerrestart/replay/SSEproof UNEXECUTED. G0prototypeoractualReadalone cannotcloseA01/A07/A10. Deliveryowner corrects observerwithinownedhelper/sourcepins, no fakeclient/transport/tool.
- These livecomponentproofs usedprovider6dd84.../sse073da... images. IndependentG3Unicodeboundary findings stillpendingcycle1terminal; anylaterproviderchange requiresnewcoherentimage/targetedproof. RequiredG2BLOCKED3/3F5 unchanged.
