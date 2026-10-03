# Cognitive Graph MVP decisions and blockers

## 2026-10-03 — initialization and team preservation

- User authorized implementation, team delegation, local tests/reversible setup, and Git versioning of these artifacts. No external writes, pushes, cloud deployment, secret access or data deletion authorized.
- Full root specification v1.1 and AGENTS.md read before product work. Approved sections extracted verbatim; no acceptance weakened.
- `python .codex/verify-team.py`: exit 0, static PASS. All 16 maintained plugin files match installed `0.1.0-creep.3` cache by SHA256; no reinstall/update performed. Upstream baseline remains `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`.
- Custom roles are explicitly exposed by this client's spawn schema. Configured matrix: main/fullstack/coding/devops `gpt-6.1-sol` high; review/SA `gpt-6-astra` high. Spawns select custom role without model overrides.
- Session mismatch: danger-full-access and never approval plus exposed external connectors differ from on-request/user and disabled connector project configuration. No config/trust/authentication changes; workflow uses local tools and honors user approval boundaries.
- Existing repository is unborn main; all setup/spec files initially untracked. Preserve all existing files; commit only newly created durable specification/research artifacts when ready, as explicitly requested.
- Installed Hermes source SHA discovered: `caed552de1c8a8f9983bc555512412a1ac0e0a9e`. G0 must verify source state and actual protocol. Docker Engine responds with 28.3.2; Ubuntu/docker-desktop are running WSL2. No live acceptance inferred.
- G0 research gates remain OPEN. G1–G6 wait on proven RD1/RD2. Unknown external Ollama details are investigated without reading credentials.

## 2026-10-03 — environment research harvested

- `devops_env` completed, only `docs/research/environment.md` written and inspected. Version/reachability commands and individual exit codes recorded there; prerequisite checks do not close product acceptance.
- External Ollama 0.33.3 reachable at Windows/Ubuntu `127.0.0.1:11434/v1`, installed tool-capable model inventory/digests recorded. Existing user-owned inference container remains external and untouched.
- Current host.docker.internal probes fail (Windows curl 28; WSL curl 7); future application-container reachability remains an open G5/G6 gate. No default endpoint change from these host probes.
- No missing endpoint facts block RD1. Local research dependencies remain isolated. Coordinator added derived-output ignore patterns while preserving durable spec versionability.
- `sa_g0` uses the freed third slot for provisional architecture analysis only. This does not bypass G0 or freeze G1 contracts. No lifecycle close API exists; completed workers have terminal status, not a claimed closed session.

## 2026-10-03 — architecture advisory harvested

- `sa_g0` completed; only `sa-review.md` written, inspected in full. Architecture advice is evidence-linked to approved scenarios, not an acceptance verdict. Its reported SQLite version probe and link check exited 0; no runtime criteria claimed.
- Carry into G1: quiescent checkpoint before external tool delivery; non-null activation uniqueness; batch-wide transactional replay/partial-result handling; per-loop iteration barriers and immutable external inputs; shared inference permit through full graph/direct exchange; file-authoritative publication and immutable run snapshots.
- Routine implementation choices still to freeze after G0: exposed-batch tool-round counting; partial chat wait versus management acknowledgment; waiting-run active-slot accounting; bounded direct admission; retained published/current-draft revision lookup. These do not require a product scope change.

## 2026-10-03 — G0 research consolidated; cycle 1 reserved

- All requested researchers and SA returned terminal results. Their exact file scopes match disk; no implementation scope was taken over. Source evidence resides in `docs/research/` and `experiments/`.
- RD1: actual Hermes 0.18.2 at SHA `caed552de1c8a8f9983bc555512412a1ac0e0a9e`; 18 exercised files match normalized pinned source. Actual Ollama 0.33.3/gemma4:12b native tool continuation, two owners, serialized delivery, SSE, bridge reconstruction and exact replay proved. Actual compressor reduced 28 messages to 6 and preserved latest pending ID/result. Full installed checkout remains dirty; clean-install and product process recovery remain later gates.
- RD1 worker: 16 tests, Ruff lint/format and pinned install passed, each exit 0. Coordinator independently reran `$env:CG_RD1_HERMES='1'; .venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q`: exit 0, 16 passed in 16.88s. Final live trace wall time 20.0207s; not a production concurrency benchmark.
- RD2: actual React Flow and Rete canvases, 6 unit/6 browser scenarios, strict typecheck and build, clean install all exit 0. Coordinator independently reran `npm --prefix experiments/editor run typecheck` and `npm --prefix experiments/editor test`: both exit 0, six tests. Screenshot inspected; lock SHA256 `058006972d96f330a17318b1cc21f16659819d7d7514f5eb1a8d9d970466d71f`; screenshot SHA256 `054d3750038bdbf159cffb2efcd6ce4dce5972dd71dc9d108971105d8d2a627e`.
- Select React Flow `@xyflow/react@12.12.0` (MIT) based on executable comparison and simpler controlled canonical JSON mapping. No Rete runtime or frontend execution engine enters the MVP. G1 will separately own production manifest/lock pins. This selection does not claim production UI acceptance.
- Research trace SHA256 `add3babddf3b1ea927eee687cb59d7bbe8e592853bf7734d8ba06e4db4c2545d`; actual request keys fit the specified client profile. Model-specific research thinking control is not a new accepted client parameter or universal default.
- G0 cycle 1 consumed before spawning `review_g0_c1` as sole independent synthesizer. G0 budget 1/3, all other product groups 0/3. Scope is G0 research proof/selection/evidence; A01–A16 production acceptance remains open and must not be substituted by prototype tests. G1 stays waiting until verdict.

## 2026-10-03 — G0 cycle 1 FAIL and scoped fix wave

- Independent `review_g0_c1` completed and appended authoritative FAIL. No High/Critical findings; two empirical Medium acceptance-gate defects: mutable upstream trace histories distort the transmitted request, and CLI replay mismatches are recorded without enforcing a nonzero failure. Fresh real continuation itself succeeded; reviewer reproduced trace divergence and false completed replay assertion.
- Independent evidence: 16 Hermes tests, Ruff, strict TypeScript, six unit tests, build, five behavioral browser tests and actual Hermes/Ollama combined run passed. The independent live run took 58.9422s, three client requests/two reads, compression 28→6. These successes do not waive the required evidence defects.
- One G0 fix wave assigned to `coding_g0_fix1` with four exact research files and regression/evidence regeneration duties. No implementation or requirements change. G0 remains 1/3 consumed; G1–G6 waiting at 0/3. Cycle 2 will be reserved only after corrected evidence is reconciled. Review history is preserved.

## 2026-10-03 — G0 corrected evidence reconciled; cycle 2 reserved

- `coding_g0_fix1` returned terminal, exactly four assigned files changed and current diff inspected. Transport records immutable exact UTF-8 body plus independent parsed JSON; replay verifies response equality and unchanged node/model/upstream/tool-delivery counts and checkpoint/mapping hashes, failing nonzero on mismatch.
- Eight new regressions first failed against old code (exit 1); full corrected pinned suite exited 0 with 24 passing tests. Ruff lint/format exited 0. Fresh real Hermes/Ollama combined run exited 0 in 55.7283s, three client calls, two reads, five model/node/upstream requests; real compression 28→6, both response/counter/state replays unchanged. Historical mutated evidence retained explicitly invalid for trace fidelity.
- Coordinator targeted rerun: `$env:CG_RD1_HERMES='1'; .venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q -k 'retains_exact_wire or cli_replay'`: exit 0, two passed/22 deselected in 7.94s. Independent JSON assertions exited 0 for two unchanged replay observations and five recorded body/parsed request pairs. Current aggregate SHA256 `72f6e6325bcdc07e42d54a1190770ef42d821b90f8c8b2a7425c9b6b52c269e6`.
- G0 cycle 2 consumed before spawning sole synthesizer `review_g0_c2`. G0 is now 2/3; G1–G6 remain 0/3. Prior cycle FAIL and exact findings preserved. G1 remains waiting for independent verdict, no acceptance weakened.
