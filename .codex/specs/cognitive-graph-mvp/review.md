# Cognitive Graph MVP independent reviews

No product synthesizer has been spawned. G0–G6 each have 0/3 consumed cycles.
Only the assigned independent review-agent may append authoritative verdicts.
No setup re-review is planned; G-TEAM-SETUP previously reached PASS at 3/3.
Required acceptance and live gates remain open until executable evidence proves them.

## Task Group G0-research - Cycle 1 - 2026-10-03

Reviewing: Wave 0 - RD1 Hermes continuation and RD2 graph-editor research,
current files and committed research diff `c3240a6..8fb9c1c`.
Synthesizer: `review_g0_c1` (independent review-agent). Analysts: none requested.
The initialization paragraph above is historical; tasks/decisions correctly
record this group's consumed cycle as 1/3. G1 remains gated on this verdict.

### Critical / Severe / High

None. The observed defects are evidence/verifier defects, not proof that the
successful live continuation itself failed.

### Medium / Low / Warning

1. **Medium - G0-C1-F1: captured upstream requests change after transmission.**
   [`experiments/hermes_bridge.py:144`] stores `request` with the caller-owned
   messages list (`:131`); `start` subsequently appends the returned assistant
   message to that same list (`:219`). Consequently the first two native
   upstream requests in the committed trace include the assistant calls that
   those requests actually generated. The first example begins at
   `experiments/hermes-traces.json:500`. This contradicts the actual-call
   evidence description at `docs/research/hermes-protocol.md:22` and makes
   model-context reconstruction from those records unreliable.
   **Evidence class: empirically reproduced, high confidence.** Capturing
   `urllib.request.Request.data` produced wire roles `['user']`; after the
   normal caller append the trace showed `['user', 'assistant']`.
   **Correction:** snapshot the exact serialized request at the transport
   boundary, add a regression comparing recorded data with transmitted bytes
   after subsequent history mutation, rerun the affected real experiment, and
   regenerate trace/source hashes and associated documentation. Preserve prior
   evidence as historical where appropriate; do not relabel mutated objects
   as actual transmitted requests. This is a required RD1 trace-fidelity gate.

2. **Medium - G0-C1-F2: the live replay verifier can succeed on a failed replay.**
   [`experiments/hermes_bridge.py:705`] records `exact_replay_matches` but never
   asserts it; the success guard at `:711` checks only completion/status/tool
   count. **Evidence class: empirically reproduced, high confidence.** An
   isolated real-Hermes run with only the final replay result deliberately
   changed returned normally with `completed=True` and
   `exact_replay_matches=False` (process exit 0). Thus the documented live
   command cannot enforce its claimed replay property. Current original and
   reviewer live traces both have true replay values; this is not a claim
   that their actual replay failed.
   **Correction:** make any replay mismatch fail the experiment nonzero;
   assert unchanged node/upstream execution counts around replay, and add a
   fault-injection regression proving the verifier rejects a mismatched
   response. Retain the existing successful replay and changed-result tests.
   This is a required executable-verification gate, independently of severity.

### Suggestion

None.

### Spec Alignment

The assigned gate is root section 11 RD1/RD2, not production A01-A16 completion.
Full root specification, AGENTS.md, requirements/spec/design/tasks/decisions,
architecture advisory, research reports, current experiment source/tests and
review history were read. Truncated initial combined reads were followed by
focused reads. Requirement IDs, acceptance IDs and stable groups remain intact.

RD1 independently demonstrates actual Hermes transport, original file executor,
nonstream and fragmented SSE continuation, distinct external IDs, deterministic
internal-ID collisions, owner restoration, latest-segment routing, serial
batches, SQLite bridge reconstruction and real compressor behavior. The fresh
real Ollama run completed, and independent assertions confirmed exact owner
result routing and both successful response replays. Research model settings
are explicitly distinguished from the future client parameter contract.
The trace/verifier defects above prevent accepting the complete RD1 evidence
deliverable despite this positive functional evidence.

RD2 meets its research obligations: both actual library canvases, named
many-to-many diamond inputs, feedback arc, scope/controller/seed controls,
prompt editing, positions and JSON round-trip. The five behavioral Chromium
cases passed independently; the sixth worker case only writes the screenshot.
The committed screenshot was visually inspected without rewriting it. The
chosen React Flow 12.12.0 is consistent with the executable comparison and
recorded MIT license. No frontend scheduler semantics were introduced.

### Cross-Slice Consistency

RD1/RD2 and environment scopes are disjoint; no production/bootstrap/lockfile
owner conflict was found. Research dependency pins match installed package and
lock metadata. G1 owns the later production contracts and manifests. The
architecture advisory remains provisional and cannot substitute for runtime
evidence. Its control-JSON, atomic recovery and partial-wait recommendations
are later implementation obligations, not extra hidden G0 acceptance tests.

The dirty installed Hermes checkout is expressly qualified: 18 normalized
exercised source files match SHA
`caed552de1c8a8f9983bc555512412a1ac0e0a9e`, not an attestation of every installed
file or dependency. This qualification is preserved. Prototype partial-result
envelopes and sequential owner startup are documented research limitations;
they must not become production behavior.

### Security And Operations

The harness binds loopback, offers only the original Hermes `read_file`, checks
the exact owned fixture path before delivery, isolates HERMES_HOME, suppresses
dotenv discovery, and disables research context/memory/MCP refresh. HTTP auth
headers are absent from captured bodies. No secrets, global configurations,
user files, external services, deployment resources or implementation files
were changed by this reviewer. Only this review file is an authored change;
tests/builds generated ignored local artifacts and dedicated fixtures.

Ollama remains external to the application. The existing host-alias failures
are correctly retained as future container-route evidence gaps. No deployment
or Windows/WSL2 Compose acceptance is inferred from host reachability.

### Verification And Test Adequacy

All commands below ran from `D:/Sources/creep` with existing project-local tools;
no installation or configuration change was needed.

| Exact command | Exit | Independent result |
| --- | ---: | --- |
| `$env:CG_RD1_HERMES='1'; .venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q` | 0 | 16 passed in 16.89s, including four actual Hermes executions |
| `.venv/hermes-research/Scripts/python.exe -m ruff check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | All checks passed |
| `.venv/hermes-research/Scripts/python.exe -m ruff format --check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | Two files formatted |
| `npm --prefix experiments/editor run typecheck` | 0 | Strict TypeScript, library checks included |
| `npm --prefix experiments/editor test` | 0 | Six unit tests passed |
| `npm --prefix experiments/editor run build` | 0 | Production bundle built |
| `npm --prefix experiments/editor run test:e2e -- --grep-invert 'capture reproducible research screenshot'` | 0 | Five behavioral Chromium cases passed in 5.7s |
| `npm --prefix experiments/editor ls --depth=0` | 0 | Installed direct pins match manifest |
| `.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/review-g0-c1-20261003-2148 --owners 2 --stream --restart --compress --serial-tools --upstream http://127.0.0.1:11434/v1 --model gemma4:12b --trace .venv/review-g0-c1-20261003-2148.json` | 0 | Live completion in 58.9422s; three Hermes requests, two real reads, five node/final upstream requests; compression 28 to 6 |

Fresh live artifact SHA256:
`7540a87d75cbab0620a143e954f31ea430ce9bbe1db7829aac01b4c61b6fd898`.
Committed trace SHA256:
`add3babddf3b1ea927eee687cb59d7bbe8e592853bf7734d8ba06e4db4c2545d`.
Both remain subject to F1 for upstream request contents. Independent JSON
assertions, run through the same Python interpreter on stdin, confirmed:
18 source matches; three client requests; two reads; serial batch sizes [1,1];
distinct external IDs; each owner receives only its own fixture token and
internal ID; both replay flags true; unchanged latest compression ID/results;
and recorded research source hashes match current files. Exit 0.
An initial inspection assumed a flat trace and exited 1 with KeyError
`completed`; it was corrected to the documented aggregate's
`authoritative_final_experiment`, not counted as a product failure.

Pin/lock integrity assertions also exited 0 for all 18 direct frontend
dependencies. Lock SHA256
`058006972d96f330a17318b1cc21f16659819d7d7514f5eb1a8d9d970466d71f` and screenshot
SHA256 `054d3750038bdbf159cffb2efcd6ce4dce5972dd71dc9d108971105d8d2a627e`
match recorded evidence. Worker clean-install and six-case browser results were
read and reconciled; reinstall and screenshot generation were not repeated.
Observed transient dynamic-handle warnings resolved before edge assertions;
the standalone bundle's `use client` warning is not a runtime failure.

Reproduction F1 (stdin Python under the same interpreter, exit 0 confirming
the defect; `TemporaryDirectory` contains only reviewer-created state):

```python
import io, json, sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0, 'experiments')
from hermes_bridge import ResearchBridge
with TemporaryDirectory(prefix='review-g0-trace-') as temp:
    bridge = ResearchBridge(Path(temp)/'state.db', Path(temp)/'fixture.txt',
        upstream='http://127.0.0.1:11434/v1', model='gemma4:12b')
    messages = [{'role': 'user', 'content': 'fixture only'}]
    sent = []
    response = {'choices': [{'finish_reason': 'tool_calls', 'message': {
        'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'native',
        'type': 'function', 'function': {'name': 'read_file', 'arguments': '{}'}}]}}]}
    def transport(req, timeout):
        sent.append(json.loads(req.data))
        return io.BytesIO(json.dumps(response).encode())
    with patch('urllib.request.urlopen', transport):
        answer = bridge.model_request(messages)
    messages.append(answer)
    assert sent[0] != bridge.trace[0]['upstream_request']
    bridge.close()
```

Reproduction F2 (stdin Python under the same interpreter, exit 0 confirming
the defect; original client/executor run, deterministic research provider):

```python
import copy, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, 'experiments')
from hermes_bridge import ResearchBridge, run_hermes
original = ResearchBridge.handle
count = 0
def corrupt_only_replay(self, request, namespace='anonymous'):
    global count
    count += 1
    result = original(self, request, namespace)
    if count == 3:
        result = copy.deepcopy(result)
        result['choices'][0]['message']['content'] = 'REPLAY_REGRESSION_SENTINEL'
    return result
with patch.object(ResearchBridge, 'handle', corrupt_only_replay):
    result = run_hermes(Path('.venv/review-g0-c1-replay-verifier-20261003'))
checks = [t['exact_replay_matches'] for t in result['client_trace']
          if 'exact_replay_matches' in t]
assert result['completed'] and checks == [False]
```

When reproducing either live fixture command again, use a new dedicated
directory; never overwrite unrelated files. Fault injection occurred only in
the reviewer process; production/research sources were not edited.

### Open Live Validation

G0 requires corrected immutable upstream traces and a live replay verifier that
fails on mismatch, with regression evidence. No analyst result is missing.
RD2 has no outstanding research gate.

Later required gates remain open: production concurrent scheduler and loops,
strict model control JSON, durable atomic process/container recovery,
TTL/cancel/late-result handling, direct-mode/SSE/error integration, immutable
snapshots and revision handling, production UI CRUD/publication/history,
and clean Windows/WSL2 Compose with actual backend-container Ollama routing.
These belong to G1-G6/A01-A16 and are not claimed by this research review.

### Verdict: FAIL

Reason: RD1's required trace-fidelity and executable replay-verification gates
remain open (two Medium findings); functional live continuation and RD2 pass
their independently executed checks. G0 has consumed 1/3 cycles. A scoped fix
wave and affected reruns may precede cycle 2; no severity escalation is used
to obtain this verdict.

## Task Group G0-research - Cycle 2 - 2026-10-03

Reviewing: Wave 0 / fix wave 1 - corrected RD1 transport evidence and replay
verifier, with unchanged RD2/environment cross-consistency. Independent sole
synthesizer: `review_g0_c2`; no analysts requested or missing. Counter 2/3 was
recorded in tasks/decisions before this spawn. Reviewed current HEAD
`33fc75b447b481f0f2cf94f0872e93d233cb982e`, correction diff
`d3c17d2..33fc75b`, and current working files. The four research changes are
`experiments/hermes_bridge.py`, `experiments/test_hermes_bridge.py`,
`experiments/hermes-traces.json`, and `docs/research/hermes-protocol.md`.
The two other files in that committed diff are coordinator-owned task/decision
records. No implementation or dependency file was edited by this reviewer.

### Critical / Severe / High

None.

### Medium / Low / Warning

None currently outstanding in this cycle's G0 scope. Both prior Medium
acceptance-gate findings are closed on current evidence:

- **G0-C1-F1 closed — empirically confirmed.**
  `experiments/hermes_bridge.py:146` constructs the transmitted request before
  recording its exact UTF-8 body and separately parsed snapshot; `:157` reads
  the exact response bytes and independently parses the recorded response and
  returned object. `experiments/test_hermes_bridge.py:16` intercepts the actual
  urllib Request data, mutates history, schema and returned-message content,
  and asserts byte and parsed-object equality for both directions. It passes.
  All five corrected real upstream request/response pairs match their recorded
  bodies; the first two requests contain no generated assistant tool calls.
  The committed aggregate equals its raw live source, and the complete prior
  aggregate is retained with an explicit trace-fidelity-invalid label rather
  than presented as corrected wire proof.
- **G0-C1-F2 closed — empirically confirmed.**
  `experiments/hermes_bridge.py:725` observes model/node/upstream/tool-delivery
  and actual Hermes tool counts plus checkpoint/mapping hashes; `:751` raises
  on any response mismatch or changed observation. Reconstruction preserves
  the counters at `:555`. The six injections at
  `experiments/test_hermes_bridge.py:218` reject corruption of either serial
  replay response and changed model/node/delivery/upstream counts. The actual
  CLI subprocess at `:261` exits 1 with the expected mismatch error and writes
  no success artifact. Reviewer-only checkpoint and mapping mutation probes
  also raised the expected guard. The fresh real run independently verified
  both original response replays with identical before/after observations.

### Suggestion

None.

### Spec Alignment

Read full root specification and AGENTS.md, requirements/spec/design/tasks/
decisions, architecture advisory, prior review, current research source/tests,
current protocol report and aggregate, and unchanged editor/environment
reports. Initially truncated combined reads were followed by focused reads.
The acceptance boundary is root section 11 RD1/RD2; production A01-A16 remains
open. IDs R01-R11 and stable groups G0-G6 are preserved.

RD1 now supplies reproducible real Hermes continuation, native model tools,
owner isolation, serial batches, SSE and nonstream tests, durable bridge
reconstruction, latest-segment routing, compressor behavior, exact replay,
source/runtime pins, and corrected actual transport evidence. The eight new
regressions' old-source failure evidence is recorded in the aggregate; the
current reviewer independently executed all corrected cases. This closes the
two defects in the cycle 1 research deliverable without treating a prototype
as production acceptance.

### Cross-Slice Consistency

RD2 and environment files are unchanged by the correction. The cycle 1
independent strict TypeScript, six unit tests, five behavioral browser tests,
build, screenshot inspection and pin validation remain applicable; there is
no new editor change that warrants repeating that suite. Current lock hash
`058006972d96f330a17318b1cc21f16659819d7d7514f5eb1a8d9d970466d71f` and screenshot
hash `054d3750038bdbf159cffb2efcd6ce4dce5972dd71dc9d108971105d8d2a627e` still
match. React Flow 12.12.0/MIT selection remains consistent with RD2 evidence.

The installed Hermes dirty-checkout qualification is retained: 18 exercised
files match normalized pinned source, not a blanket clean-install claim.
Research sequential startup, one tool per owner, partial-result test envelope,
in-process reconstruction and model-specific thinking settings remain clearly
qualified. The SA recommendations are provisional G1 input, not new G0 gates.
Production loop-control JSON, process recovery and container routing remain
explicitly open even where an environment/advisory paragraph anticipates them.

### Security And Operations

Fresh live tests used only new dedicated directories under `.venv`, loopback
HTTP, isolated HERMES_HOME, suppressed dotenv discovery, and the original
Hermes read_file implementation restricted to generated fixture paths. No
secrets, unrelated files, global configuration, installed Hermes files,
external service configuration or deployment resources were modified. Source
pins and dependency versions were checked without reinstalling anything.
Only this review file is an authored versioned change; runtime fixtures and
test outputs are ignored local evidence. No agents were spawned.

Ollama remains external. The fresh read-only inventory confirmed server
0.33.3 and gemma4:12b digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
The live run independently rechecked Hermes SHA
`caed552de1c8a8f9983bc555512412a1ac0e0a9e` and all 18 normalized source matches.
No host probe is represented as backend-container networking proof.

### Verification And Test Adequacy

Executed from `D:/Sources/creep` using existing project-local pinned tooling:

| Exact command | Exit | Independent outcome |
| --- | ---: | --- |
| `$env:CG_RD1_HERMES='1'; .venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q` | 0 | 24 passed in 47.50s; 13 contract/transport cases and 11 real Hermes cases, including negative verifier/CLI cases |
| `.venv/hermes-research/Scripts/python.exe -m ruff check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | All checks passed |
| `.venv/hermes-research/Scripts/python.exe -m ruff format --check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | Two files already formatted |
| `.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/review-g0-c2-20261003-fresh01 --owners 2 --stream --restart --compress --serial-tools --upstream http://127.0.0.1:11434/v1 --model gemma4:12b --trace .venv/review-g0-c2-20261003-fresh01.json` | 0 | Actual completion in 55.7459s; three Hermes requests, two reads, five node/final model requests; both enforced replays unchanged; compression 28 to 6 |

Fresh live trace SHA256:
`bcad4d153a3771274f9e0af801126d972c36eb8fa98818608b75f9c83fd1460a`.
Current aggregate SHA256:
`72f6e6325bcdc07e42d54a1190770ef42d821b90f8c8b2a7425c9b6b52c269e6`.
Source hashes match the protocol report and aggregate: bridge
`b27feb69b1a543f2b3bbb8c57f49de0188128888251677bb30a8c96ecb1532f2`, tests
`ddb0e7eb9c0d8ad6349c23a964a9377c9ffbb7eb6d1c5ef8bcc7a51ee5ac112b`.

Independent Python assertions through the same interpreter on stdin exited 0:
source hashes and all research package pins; raw authoritative trace hash and
equality with the aggregate; historical aggregate JSON equality with
`git show d3c17d2:experiments/hermes-traces.json`; five body/parsed pairs per
current/fresh run; no generated assistant calls in initial requests; two
unchanged replays; exact owner-specific fixture content/internal-ID restoration;
all 18 source matches; compression 28-to-6 with unchanged latest IDs/results;
and current Ollama version/model digest. These checks inspect actual records
in addition to relying on the CLI's success summary. The separate compression
model call is not counted among the five graph node/final requests.

Reviewer-only state-mutation verification used the following exact Python
payload piped with PowerShell `@' ... '@ | .venv/hermes-research/Scripts/python.exe -`.
Exit 0, output `checkpoint rejected` and `mapping rejected`. Use new fixture
names for any rerun. It patches only the reviewer process and dedicated DB:

```python
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, 'experiments')
from hermes_bridge import ResearchBridge, run_hermes
original=ResearchBridge.handle
for fault in ('checkpoint','mapping'):
    call_count=[0]
    def inject(self, request, namespace='anonymous'):
        call_count[0]+=1
        response=original(self, request, namespace)
        if call_count[0]==3:
            if fault=='checkpoint':
                state=self.state(); state['review_fault']=True; self.save(state)
            else:
                self.db.execute("UPDATE calls SET arguments_hash='review_fault'"); self.db.commit()
        return response
    with patch.object(ResearchBridge,'handle',inject):
        try:
            run_hermes(Path('.venv/review-g0-c2-20261003-fault-'+fault))
        except RuntimeError as exc:
            assert str(exc)=='Exact replay execution or checkpoint changed',str(exc)
            print(fault,'rejected')
        else:
            raise AssertionError(fault+' was not rejected')
```

The existing negative CLI test validates a real subprocess exit, not merely
an internal return flag. Transport regression tests use the actual serialized
Request bytes and retain response whitespace/non-ASCII request data, so they
can detect the original aliasing fault. Source/dependency pin assertions passed.
No repository CI workflow exists yet; required G0 Python checks ran, and the
unchanged RD2 check evidence was reconciled. Read-only discovery of absent
descendant AGENTS.md/.github returned no matches/missing directory; these
discovery results are not claimed as successful verification commands.

### Open Live Validation

No required G0 research gate or requested analyst evidence remains open.

G1-G6/A01-A16 still require production concurrent scheduling, fan-in and seeded
loops, model control JSON, immutable revisions/snapshots, atomic durable
continuation and actual process/container recovery, TTL/cancel/late-result
behavior, direct-mode/SSE/error integration, full production UI, and clean
Windows/WSL2 Compose with real backend-container Ollama routing. They also
require clean runtime/toolchain delivery evidence and target concurrency
measurements. Research test success closes none of these production gates.

### Verdict: PASS

G0-research's RD1/RD2 acceptance and required verification are demonstrated;
both cycle 1 findings are closed, with no current blocking finding or missing
G0 evidence. G0 has consumed 2/3 cycles. This verdict permits G1 contract work
and is not an MVP completion verdict.

## Task Group G1-contracts - Cycle 1 - 2026-10-03

Reviewing: Wave 1 - all 26 `coding_bootstrap` files listed in tasks.md.
Independent sole synthesizer: `review_g1_c1`; no analysts requested or missing.
Cycle 1/3 was reserved in commit `9952639` before this spawn. G0 remains PASS
at 2/3; its history above is unchanged. G1 files are untracked new product
files and were inspected directly, not treated as an empty diff. No downstream
writer was active. Only this review file was authored here.

### Critical / Severe / High

- **G1-C1-F1 — High: strict client contract rejects actual Hermes tool
  continuations.** `backend/app/contracts/api.py:55` defines ToolMessage with
  role, tool_call_id and content but no optional name. The base at
  `backend/app/contracts/graph.py:25` forbids extras. Of three actual Hermes
  requests in the authoritative immutable G0 fixture, the first validates,
  the second fails at `messages[5].tool.name`, and the third fails at
  `messages[3].tool.name` and `messages[5].tool.name`. Generated frontend JSON
  Schema independently rejects those same continuations under Ajv. Thus this
  frozen request contract would return 400 before routing for the proven
  client, breaking R01/R03 and A07-A10. **Evidence: empirically reproduced
  DTO/schema failure using pinned real-client traces; no endpoint execution
  claimed.** Correction: preserve optional tool-result `name`, regenerate
  schema/TypeScript, document it, and regress all three recorded requests
  without stripping fields. Keep other unsupported semantics rejected.
  The synthetic fixture at `backend/tests/contracts/test_contracts.py:93`
  omits name, explaining why the green suite missed this requirement.

### Medium / Low / Warning

- **G1-C1-F2 — Medium, required contract/evidence gap: known upstream wire
  normalization is not frozen.** `backend/app/contracts/interfaces.py:471`
  returns strict ChatCompletionResponse (`backend/app/contracts/api.py:171`),
  but the concrete handoff at `docs/api.md:366` does not define conversion of
  known Ollama metadata. All five authoritative G0 wire responses fail that
  DTO: each has `system_fingerprint` and `usage.prompt_tokens_details`; both
  tool responses also have `tool_calls[].index`. **Evidence: empirically
  reproduced raw-response/DTO mismatch; missing policy is static-verifiable.**
  This is not a runtime failure claim against an unimplemented G3 adapter.
  The coordinator clarified during review that G3 must explicitly normalize
  known transport metadata into strict internal/public DTOs, preserving
  semantic fields and not silently dropping unknown meaningful fields. That
  clarification is absent from the durable handoff and tests. Correction:
  freeze the precise allowed conversion and owner in docs/api.md, and cover
  all five pinned responses with contract fixtures asserting preserved model,
  ID/created, content, tool IDs/names/raw argument strings, finish_reason and
  aggregate usage. Do not use blanket extra-field ignoring. G3 must later
  exercise actual HTTP/SSE normalization. This missing G1 acceptance evidence
  blocks freeze independently of severity.

### Suggestion

None.

### Spec Alignment

Read the complete root specification and AGENTS.md, installed spec/review
skills, current requirements/spec/design/tasks/decisions, acceptance ledger,
SA advisory/reconciliation, prior review, current sources, generated outputs,
manifests/locks and tests. Truncated reads were followed by focused reads.
G1 is contract/bootstrap acceptance; A01-A16 remain correctly OPEN.

Other reviewed boundaries align statically: mandatory null-capable feedback
seeds, disjoint loop syntax, lexical all-port plans, optional final LLM for
passthrough, immutable snapshot/hash and detached access, non-null activation
identity, provider-round/call-ordinal tool ownership, quiescent exposure,
fixed UTC deadlines, source-batch response cursors and atomic claim sealing,
CAS/terminal guards, conditional disconnect, safe waiting recovery and shared
admission/full-exchange permits. Their concurrency/crash/timeout behavior
still requires downstream tests; Protocols do not prove runtime behavior.

### Cross-Slice Consistency

Generated outputs match Python exactly, including F1. The drift regression
actually changes a temporary output and requires exit 1. Strict TS includes
library checks. SA-G1-01 through SA-G1-07 resolutions are present at unchanged
reconciliation hashes. No analyst evidence is missing. F1/F2 demonstrate why
G0 research success cannot substitute for validating new production DTOs.

Eight Python direct pins match uv.lock and installed isolated packages;
non-project Python artifacts use PyPI and SHA256 hashes. Eleven frontend
direct pins match npm lock and installed versions. Current hashes:

- uv.lock: `21b6904c150ab4c13a02f47ab4e4c9825d5cf6d331554595381a82e8b245a9f0`
- npm lock: `229187d9a35f662a2b508510c72736286fa555fa747de20fc5d68bb83f341242`
- interfaces.py: `1199677d3ce6d923688ef8197b0db9545506ab2dcec1b57e5f1948302771e1b6`
- docs/api.md: `2cc59eba0f3276b7f27f988da8ee9dabbaf2c5503f78cb05dd4440717101d8d8`

### Security And Operations

DTO tests demonstrate strict semantic keys, safe graph IDs, positive limits,
finite JSON, explicit seeds, and synthetic-token repr/serialization exclusion.
Future HTTP authentication, log redaction, symlink safety, body-size enforcement
and actual concurrency remain implementation gates. No tool executor/cloud
dependency/inference service is introduced. No secrets, user data, external
service, Docker resource, global config, dependency installation or product
file was changed here. No live call was necessary; sanitized G0 evidence was
used read-only.

### Verification And Test Adequacy

Executed from `D:/Sources/creep` using current pinned local tooling:

| Command / probe | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py lint` | 0 | Locked Ruff lint; 11 files pass format; schema drift and both strict TS projects pass |
| `python scripts/dev.py test-contract` | 0 | 49 Python cases in 1.41s and five frontend cases; drift passes |
| Python reproduction below, literal here-string piped to `backend/.venv/Scripts/python.exe -` | 0 | Confirms two rejected actual continuations and five rejected raw responses |
| JavaScript reproduction below, literal here-string piped to `node -` | 0 | Generated schema confirms `[true,false,false]` for real Hermes requests |
| Local Python manifest/lock/installed-version/hash assertions | 0 | Eight Python/eleven frontend pins and hashes above match; Python 3.11.15 |
| `python scripts/dev.py test-runtime`, `test-graphs`, `test-e2e`, `smoke-hermes`, `smoke-compose`, `build`, `frontend` | 2 each | Missing prerequisites fail explicitly, never PASS |
| `dev.execute([sys.executable,'-c','raise SystemExit(7)'])` in isolated Python | 7 propagated | Outer assertion probe exits 0 after checking exact propagation |

Wrapper uses uv0.11.28 with `--locked`, repository Ruff config and npm scripts;
Make delegates the same targets. No CI workflow exists yet; G5 owns it.
An initial inline Node probe failed in PowerShell quoting at `$ref` (exit 1)
before Node execution; corrected literal here-string succeeded. This is a
reviewer command error, not a product defect or a passed test.

Python reproduction payload (no source writes/network):

```python
import json, sys
sys.path.insert(0, 'backend')
from app.contracts.api import ChatCompletionRequest, ChatCompletionResponse
from pydantic import ValidationError
with open('experiments/hermes-traces.json', encoding='utf-8') as source:
    trace = json.load(source)['authoritative_final_experiment']
requests = [x['client_request'] for x in trace['client_trace']
            if 'client_request' in x]
accepted = []
for request in requests:
    try:
        ChatCompletionRequest.model_validate(request)
        accepted.append(True)
    except ValidationError as error:
        assert all(e['type'] == 'extra_forbidden' and e['loc'][-1] == 'name'
                   for e in error.errors(include_input=False))
        accepted.append(False)
assert accepted == [True, False, False]
responses = [json.loads(x['upstream_response_body_utf8'])
             for x in trace['upstream_trace'] if 'upstream_response_body_utf8' in x]
assert len(responses) == 5
for response in responses:
    try:
        ChatCompletionResponse.model_validate(response)
    except ValidationError as error:
        assert all(e['type'] == 'extra_forbidden'
                   for e in error.errors(include_input=False))
    else:
        raise AssertionError('Unexpectedly accepted raw response')
```

Frontend reproduction payload, piped as a literal here-string to `node -`:

```javascript
const fs = require('fs');
const Ajv = require('./frontend/node_modules/ajv/dist/2020').default;
const schema = JSON.parse(fs.readFileSync('frontend/src/contracts/schema.json','utf8'));
const validate = new Ajv({strict:false,allErrors:true}).compile({
  ...schema, $ref:'#/$defs/ChatCompletionRequest'
});
const trace = JSON.parse(fs.readFileSync('experiments/hermes-traces.json','utf8'))
  .authoritative_final_experiment;
const results = trace.client_trace.filter(x => x.client_request)
  .map(x => validate(x.client_request));
if (JSON.stringify(results) !== '[true,false,false]') process.exit(1);
```

### Open Live Validation

G1 corrected real-client compatibility and explicit provider-normalization
contract fixtures remain required. No G1 live runtime PASS was claimed.
All G2-G6 production gates remain OPEN: DAG/seeded loops, SQLite transitions
and restart, tool routing/replay, JSON/SSE/errors/auth, UI/history, production
Hermes/Ollama and Windows/WSL2 Compose/network/volume/restart, target metrics.
The earlier rejected Docker diagnostic proves none of these.

### Verdict: FAIL

Reason: one High Hermes compatibility defect and one Medium missing required
upstream-boundary contract/evidence prevent G1 freeze. G1 consumed 1/3 cycles;
one scoped correction wave and affected checks may precede cycle 2. Severity
was not adjusted to force the verdict. Dependent implementation must wait.

## Task Group G1-contracts - Cycle 2 - 2026-10-03

Reviewing: Wave 1 correction - the six files in G1 fix wave 1, with regression
consistency against the existing contract/bootstrap surface.
Independent sole synthesizer: `review_g1_c2`; no analysts requested or missing.
Cycle 2/3 was reserved in commit `cc6ac73` before this spawn. G0 remains PASS
at 2/3. This is targeted verification of the prior findings, not a new group
or counter. Current untracked product files were inspected directly.

### Critical / Severe / High

None remaining. **G1-C1-F1 (High) closed.**
`backend/app/contracts/api.py:59` preserves optional tool-result name;
`frontend/src/contracts/generated.ts:55` and the generated JSON Schema agree.
All three `authoritative_final_experiment.client_trace` requests validate in
Python and Ajv, including both previously rejected continuations. Exact
serialized histories, schemas, names, raw arguments and result strings remain
unchanged; validation does not mutate the fixture. Additional unknown tool
message fields and unsupported client `reasoning_effort` remain rejected.
Evidence class: empirically confirmed DTO/generated-schema behavior, not
production HTTP or live Hermes execution.

### Medium / Low / Warning

None remaining in this correction. **G1-C1-F2 (Medium required G1 gate) closed.**
`backend/app/contracts/api.py:181` supplies the pure strict upstream factory.
Private DTOs validate metadata before removal; nonstream tool indices are
checked against array order at `backend/app/contracts/api.py:214`. The factory
removes only the declared fingerprint, prompt-token detail container and
nonstream call index. Unknown nested metadata and malformed semantic fields
are rejected rather than ignored. All five authoritative UTF-8 wire response
bodies normalize successfully, preserving ID, model, time, object, choices,
content, call IDs/names/raw arguments, finish reason and aggregate usage.
Inputs are unchanged, and later input mutation cannot alter the parsed DTO.
`docs/api.md:98` freezes the conversion and sanitized error responsibility;
`docs/api.md:123` explicitly leaves HTTP/SSE normalization and cleanup to G3;
`docs/api.md:395` names the consuming adapter. Evidence class: empirically
confirmed pure-boundary behavior plus static-verifiable handoff, not an
implemented transport claim.

### Suggestion

None.

### Spec Alignment

Read the authoritative specification, AGENTS.md, installed spec/review skills,
durable requirements/design/tasks/decisions and relevant spec contracts,
prior review and SA reconciliation. The correction preserves R01/R03's
actual pinned client profile without broadening accepted client semantics.
No product requirement or A01-A16 acceptance criterion was removed. G1's
required corrected fixture and normalization evidence is now demonstrated.
Other unchanged G1 contracts retain their prior reviewed boundaries; their
scheduler/storage/HTTP implementations remain downstream work.

### Cross-Slice Consistency

Schema regeneration/drift checks match Python, and both strict TypeScript
projects pass. The frontend uses the generated optional-name type and validates
the actual fixtures. Tests use only `authoritative_final_experiment`, never
the explicitly invalid historical trace. The trace, both dependency locks,
and interfaces.py retain the previously reconciled SHA256 values:

- trace: `72f6e6325bcdc07e42d54a1190770ef42d821b90f8c8b2a7425c9b6b52c269e6`
- uv.lock: `21b6904c150ab4c13a02f47ab4e4c9825d5cf6d331554595381a82e8b245a9f0`
- npm lock: `229187d9a35f662a2b508510c72736286fa555fa747de20fc5d68bb83f341242`
- interfaces.py: `1199677d3ce6d923688ef8197b0db9545506ab2dcec1b57e5f1948302771e1b6`

Current corrected api.py is
`681b38303bc8d495eeed6d3886bc8665e2de960020ec18b45cdc3d79e86a6c83`;
docs/api.md is
`2b058eee0815e9a0cfbe96093d151991ab572e35bdc2e937a2b7c71b47cc698a`.

### Security And Operations

The shared base still forbids extras and coercion. The public response
constructor continues to reject raw upstream metadata; normalization is an
explicit separate boundary. No blanket extra-field ignoring, tool executor,
network call, retry, secret access or runtime configuration change was added
by this fix or review. The reviewer wrote only this review record; no product
source, fixture, lock, configuration or external resource was changed.

### Verification And Test Adequacy

Executed from `D:/Sources/creep` with current project-local pinned tooling:

| Command / probe | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py lint` | 0 | Ruff lint, 11-file format check, schema drift, both strict TypeScript projects pass |
| `python scripts/dev.py test-contract` | 0 | 71 Python tests in 1.46s; nine frontend tests in 217ms; generated contracts match |
| Independent literal Python probe piped to `backend/.venv/Scripts/python.exe -` | 0 | Three exact client histories and five exact normalized wire responses; strict public constructor, input immutability and detached parsed output verified |
| Same Python probe, adversarial metadata/semantic mutations | 0 | 15 additional negative cases rejected; ordered two-call response and four documented allowed metadata combinations accepted |
| Independent literal JavaScript probe piped to `node -` using `frontend/node_modules/ajv/dist/2020` | 0 | All three untouched actual requests accepted; unsupported top-level semantics, tool-message extras and numeric names rejected |
| `Get-FileHash ... -Algorithm SHA256` for the six evidence files above | 0 | All expected hashes match |

The Python regressions at `backend/tests/contracts/test_contracts.py:69` and
`:81` compare entire parsed payloads with exact original data after only the
three documented metadata removals. The 13 committed negative cases at
`:112` and strict tool-message regression at `:122` execute actual validation.
Frontend fixtures at `frontend/src/contracts/contracts.test.ts:18` exercise
all three actual requests through Ajv without fixture rewriting. The suite
also retains the prior real schema-drift failure regression.

The independent additional Python negatives tested object-valued fingerprint,
array-valued token details, fractional/nonfinite cached tokens, boolean/float/
negative call index, unknown call/function/choice fields, wrong call type or
message role, inconsistent finish reason, choice index 1, and duplicate call
ordinals in a two-call response. Accepted metadata combinations included null,
empty detail object, null cached count and integer zero. These are executed
boundary checks, not inferred results or production runtime tests.

The wrapper was inspected: it invokes uv with `--locked`, repository Ruff
configuration and npm scripts; Make delegates the same targets. There is no
CI workflow yet; G5 owns its implementation. Owner-reported fail-first runs
are preserved in decisions.md; this reviewer independently ran the corrected
current regressions and probes, not a reconstructed pre-fix tree.

### Open Live Validation

No required G1 gate remains open. All G2-G6 production/live gates remain OPEN:
DAG/seeded loops and concurrency, SQLite transactions/recovery/replay,
production JSON/SSE/error/auth transport, UI/history, actual Hermes/Ollama,
Windows/WSL2 Compose/container routing/volume/restart, and target performance
measurements. A01-A16 are not closed by this contract review or G0 prototypes.
The previously rejected Docker diagnostic proves none of these behaviors.

### Verdict: PASS

G1 contract/bootstrap freeze passes cycle 2 with both prior findings closed,
no current findings and all required G1 evidence collected. G1 has consumed
2/3 cycles. This verdict permits dependent implementation; it is not MVP
completion or a production/live acceptance verdict.

## Task Group G2-runtime - Cycle 1 - 2026-10-04
Reviewing: Wave 2 module implementation - scheduler, admission, clock, SQLite state and durable events.
Synthesizer: review_g2_c1. Analysts: none requested. G2 budget consumed: 1/3.
Current files were reviewed directly: all 12 assigned runtime/storage source and test files are new untracked product files. An empty Git diff was not treated as an empty change.

### Critical / Severe / High

- **High F1 — terminal failure does not prevent response delivery.** [backend/app/runtime/engine.py:128](../../../backend/app/runtime/engine.py#L128) returns a saved response before checking the run's terminal status. **Empirically reproduced:** after a real SQLite-backed fake-provider run commits its first tool envelope, explicitly cancel it, confirm status `cancelled`, then call `runtime.await_response(run_id, "anonymous", 0)`: it still returns `finish_reason=tool_calls`. The probe deliberately waits on storage, without consuming the response before cancellation. A pending initial HTTP waiter can consequently receive calls after explicit cancellation; the same ordering applies to failed/interrupted runs with saved envelopes. This violates A14 and the cancellation boundary, and conflicts with the repository's failed-run replay rejection. **Correction:** reject failed/cancelled/interrupted state before delivering any saved envelope, preserving legitimate completed-success responses and the separately authorized detach-after-exposure behavior. Add deterministic cancellation/expiry/interruption-before-delivery regressions, including a waiting response task.

- **High F2 — final controller string payload loses required JSON encoding.** [backend/app/runtime/engine.py:743](../../../backend/app/runtime/engine.py#L743) renders every string payload as ordinary text without considering the external response format. **Empirically reproduced:** submit the valid feedback graph with `response_format={"type":"json_schema","json_schema":{"name":"answer","strict":true,"schema":{"type":"string"}}}`. The provider receives a controller payload schema of `{"type":"string"}` and returns valid `{"payload":"hello","control":{"decision":"stop"}}`; the run completes with external content `hello`, which is invalid JSON. A numeric-looking string could silently become the wrong JSON type. This breaks section 4.1's final external response-format contract. **Correction:** render controller payloads according to the requested external format, using JSON serialization for JSON formats, while preserving ordinary text behavior and already formatted non-controller content. Cover string/escaped string/object/scalar payloads, ordinary text, persisted envelope and recovery behavior.

### Medium / Low / Warning

- **Medium F3 — schema rebasing changes literal data.** [backend/app/runtime/engine.py:601](../../../backend/app/runtime/engine.py#L601) recursively traverses every object/list value, treating literal objects under `const`, `enum`, `default` or `examples` as schemas. **Empirically reproduced:** the accepted schema `{"type":"object","const":{"$ref":"#/literal"}}` validates `{"$ref":"#/literal"}` before rebasing; after `_embed_payload_references`, the const becomes `{"$ref":"#/properties/payload/literal"}` and the same instance fails the pinned JSON Schema validator. Thus a legitimate client constraint is changed before inference. **Correction:** rebase references only in schema-bearing locations, or use an embedding approach that preserves schema resource/reference semantics. Add regressions proving literal data remains byte/value-equivalent alongside working actual local references.

### Suggestion

None.

### Spec Alignment

Reviewed the complete root specification, AGENTS.md, installed team-spec-workflow/team-review-cycle procedures, current durable requirements/spec/design/tasks/decisions/acceptance, prior review history and docs/api.md. The coordinator's durable reservation identifies this as G2 cycle 1; no counter was inferred or reset.

The implemented module provides meaningful evidence for R04/R05/R06/R07/R09 and deterministic portions of A03-A06/A08-A10/A13-A14/A16: concurrent diamond startup with an all-input lexical barrier; explicit optional null; immutable snapshots/context; separate scopes, seeded feedback from non-controller members and constant input members; strict controller enum and emergency failure; durable attempts, partial results, replay association, cancellation and recovery; shared bounded admission. Required/forced first activation rounds transition to auto only after durable owner results, and global none is retained.

F1 and F2 leave required module behavior unsatisfied. F3 changes an accepted client schema. Existing green checks do not waive these defects. No requirement, acceptance scenario or exclusion was changed by this review.

### Cross-Slice Consistency

Constructors and protocol methods match current contracts. Runtime consumes the graph validator, provider and tool bridge rather than implementing their transports or external execution. Its per-owner provider_round convention matches the durable decision. Optional ActivationRecord.finish_reason is consumed and preserved; the current additive G1 review gate remains separate.

Production G3 bridge/provider and G4 UI were concurrent disjoint writers. Their incomplete implementation was not used to claim G2 behavior or treated as a G2 defect. G2 tests use explicit test-only providers/bridge while executing actual scheduler, validator, admission and SQLite. No analysts were requested and no requested review result is missing.

### Security And Operations

No product tool executor, model-weight switch, cloud resource, secret read, deployment or live resource mutation was introduced or performed. SQLite transactions run synchronously on one dedicated thread, with WAL, foreign keys and FULL synchronization empirically queried. Persistent CAS/unique identities, first terminal reason, immutable accepted result and rollback checks were inspected and exercised. Admission retains waiting-tool capacity; production shared graph/direct inference permits belong to G3/G6.

F1 is a cancellation/effect-delivery defect even though the backend itself does not execute the returned tools. No external tool was executed by the probes.

### Verification And Test Adequacy

Executed from `D:/Sources/creep` using the project-local environment selected by locked uv. Python 3.11.15, pytest 9.1.1, Ruff 0.16.10 and jsonschema 4.26.0 are pinned in the existing manifests/lock. The development wrapper was inspected: test-runtime dispatches the two actual runtime/storage test directories with `uv --system-certs run --project backend --locked pytest ... -q`. Scoped lint/format checks use the same repository configuration as CI; broader UI/build/live gates remain assigned to their groups.

| Command | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py test-runtime` | 0 | 41 passed in 11.72s |
| `uv --system-certs run --project backend --locked pytest backend/tests/contracts backend/tests/graphs backend/tests/runtime backend/tests/storage -q` | 0 | 173 passed in 13.08s |
| `uv --system-certs run --project backend --locked ruff check backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | 12 files already formatted |
| PowerShell inline probes via `uv --system-certs run --project backend --locked python -c $probe` | 0 | All three defects empirically reproduced; consolidated exact probe below |
| Additional inline guard probe using the same locked Python invocation | 0 | 4 active + 20 queued leases, 25th rejected with 429, all released; SQLite 3.53.1 on a thread different from the event-loop thread with journal_mode=wal, foreign_keys=1, synchronous=2; max_tool_rounds=1 rejects the second exposure with budget_exceeded and no successful final output |
| `git status --short --untracked-files=normal`, `git diff --stat`, source reads/hashes | 0 | New untracked product scope confirmed; peer work preserved |

The guard probe used `BoundedAdmissionController(4,20)` with 24 concurrent acquisitions and a 25th acquisition, then released every lease. Its SQLite checks executed through `store._call` against the initialized production repository. Its tool budget check used `Settings(max_tool_rounds=1)`, the real runtime/repository and a provider that requests a tool every round; after accepting the first envelope, `await_response(...,1)` raised `budget_exceeded`, with saved failed status and exactly one tool round.

Existing tests include real SQLite closure/reconstruction, accepted-before-resume recovery, stale-frontier CAS rejection, atomic response/claim rollback injection, owner/global identity rollback, expiry-vs-full-acceptance, committed event catch-up, concurrent duplicate claims and first-subsequent response association. These are substantial module checks, but they did not exercise the three reproduced defects. Recovery tests reconstruct objects/connections in one process; they do not prove a production process/container restart.

Source SHA256 at review:
- engine.py: `88ae07ef64c785e893397f690644cdf7b09e9d1cee49e072969efd0c097002ee`
- repository.py: `c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15`
- admission.py: `2f6e24c9ecd88aeb085724ff0c7d7cc5a8bc869bde3ab231a625dfd344c766ad`
- events.py: `009ca00b126e399d5c279be9c254f74f2e8fbca5af6cd4963ba1ea5a662b00ff`
- uv.lock: `21b6904c150ab4c13a02f47ab4e4c9825d5cf6d331554595381a82e8b245a9f0`

Reproduce F1-F3 from the repository root in PowerShell. Exit 0 here means the assertions confirmed the defects on the reviewed implementation; it does not mean acceptance passed. Temporary SQLite fixtures are isolated and automatically removed.

```powershell
$probe = @'
import asyncio, copy, json, sys, tempfile
from pathlib import Path
sys.path[:0] = [str(Path("backend").resolve()),
               str(Path("backend/tests/runtime").resolve())]
from test_scheduler import (Provider, create_runtime, edge, graph, input_node,
                            llm, node_request, output_node, response, submission)
from test_loops import loop_graph
from test_recovery import TOOLS, tool_runtime, wait_until
from app.runtime.engine import AsyncGraphRuntime
from jsonschema import Draft202012Validator

async def main():
    async def text_provider(request):
        if node_request(request) == "draft":
            return response("draft")
        return response('{"payload":"hello","control":{"decision":"stop"}}')
    with tempfile.TemporaryDirectory() as path:
        runtime, store = await create_runtime(Path(path), Provider(text_provider))
        try:
            policy = {"model": "cg/g", "response_format": {"type": "json_schema",
                      "json_schema": {"name": "answer", "strict": True,
                                      "schema": {"type": "string"}}}}
            run = await runtime.submit(submission(loop_graph(), client=policy))
            result = await asyncio.wait_for(
                runtime.await_response(run.run_id, "anonymous"), 3)
            content = result.completion().choices[0].message.content
            assert content == "hello"
            try:
                json.loads(content)
            except json.JSONDecodeError:
                print("F2 reproduced: completed string payload is not JSON")
            else:
                raise AssertionError("F2 not reproduced")
        finally:
            await runtime.shutdown()
            await store.close()

    async def tool_provider(request):
        return response(None, [{"id": "internal", "type": "function",
                        "function": {"name": "read", "arguments": "{}"}}])
    with tempfile.TemporaryDirectory() as path:
        runtime, store, _ = await tool_runtime(Path(path), Provider(tool_provider))
        try:
            value = graph(nodes=[input_node("i"), llm("a", True), output_node()],
                          edges=[edge("i", "a", "question"), edge("a", "o", "answer")])
            run = await runtime.submit(submission(value, tools=TOOLS))
            await wait_until(store, run.run_id, lambda cp: bool(cp.responses))
            assert (await runtime.cancel(run.run_id, "anonymous")).status == "cancelled"
            result = await runtime.await_response(run.run_id, "anonymous")
            assert result.completion().choices[0].finish_reason == "tool_calls"
            print("F1 reproduced: cancelled run still returns tool_calls")
        finally:
            await runtime.shutdown()
            await store.close()

    schema = {"type": "object", "const": {"$ref": "#/literal"}}
    instance = {"$ref": "#/literal"}
    assert Draft202012Validator(schema).is_valid(instance)
    rewritten = copy.deepcopy(schema)
    AsyncGraphRuntime._embed_payload_references(rewritten)
    assert not Draft202012Validator(rewritten).is_valid(instance)
    assert rewritten["const"]["$ref"] == "#/properties/payload/literal"
    print("F3 reproduced: rewriting changes literal const semantics")

asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $probe
```

Observed output:
```text
F2 reproduced: completed string payload is not JSON
F1 reproduced: cancelled run still returns tool_calls
F3 reproduced: rewriting changes literal const semantics
```

### Open Live Validation

Still OPEN, owned by later integration/delivery gates: actual provider/bridge/HTTP integration; globally shared graph/direct inference under real JSON/SSE; production image SQLite 3.40.1 runtime behavior; actual process/container waiting-ID restart and persistence; real pinned Hermes/Ollama execution; Windows/WSL2 Compose routing/volume/SSE; real UI integration and target timing comparisons. Native SQLite 3.53.1 module checks and G0 experiments do not close those gates. This review does not claim A01-A16 production completion.

### Verdict: FAIL

Reason: two current High required-contract defects and one Medium schema-preservation defect remain empirically reproducible. G2 cycle 1/3 is consumed; the coordinator may assign one scoped fix wave before cycle 2. Reviewer changed only this review artifact, with no implementation edits or commits.

## Task Group G2-runtime - Cycle 2 - 2026-10-04
Reviewing: Wave 2 module implementation plus fix wave 1 - all 12 assigned runtime/storage source and test files, with targeted F1-F3 regression verification.
Synthesizer: review_g2_c2. Analysts: none requested. G2 budget consumed: 2/3, reserved in tasks/decisions before spawn (commit `40a0e67`). One cycle remains.
Current untracked product files were read directly; the empty tracked implementation diff did not define the review surface. Concurrent API and delivery work was preserved.

### Critical / Severe / High

None currently demonstrated in this slice. Cycle-1 High F1 and F2 are closed by current source, fresh regression tests and independent reruns of the original probes.

### Medium / Low / Warning

- **Medium F4 — an empty schema resource ID breaks final-controller local references.** [backend/app/runtime/engine.py:597](../../../backend/app/runtime/engine.py#L597) treats the presence of any `$id` as establishing an independent embedded resource and returns without rebasing; the same assumption exists in nested traversal at line 603. **Evidence class: empirically reproduced, with high confidence in the schema transformation defect.** Both valid Draft 2020-12 schemas with `"$id":""` and `"$id":"#"`, a `$defs.Text` string schema and `"$ref":"#/$defs/Text"` pass the pinned schema meta-validator, validate the original payload and pass the public ChatCompletionRequest DTO. Through the actual runtime's `_request`, the emitted controller schema instead resolves the unchanged pointer at the controller root, where `Text` does not exist. The pinned validator reports `PointerToNowhere`. A deterministic schema-validating fake provider produces a real scheduler/SQLite `failed/upstream_error` outcome. This is a local executable proof; no claim is made that a real Ollama/model was exercised by this probe. **Impact:** a supported client final-response constraint becomes an unusable upstream constraint solely because the graph ends in a controller. **Correction:** preserve resource identity and reference semantics when embedding, accounting for IDs that resolve to the containing resource rather than blindly treating every ID key as a new root. Preserve caller IDs/literal data and cover root/nested empty IDs, fragment-only IDs, ordinary absolute/relative IDs and declared-dialect resource boundaries through the emitted controller schema. Do not silently narrow the accepted schema profile. This Medium defect also fails a required section 4.1/G2 format-preservation acceptance condition; no severity escalation is needed to block PASS.

### Suggestion

None.

### Spec Alignment

Read the authoritative source and AGENTS.md, installed team-spec-workflow/team-review-cycle procedures, current durable requirements/spec/design/tasks/decisions/acceptance, prior review findings and API contracts. The coordinator confirmed that no durable accepted profile restricts schemas to a single dialect; no new restriction was introduced.

R04/R05/R06/R07/R09 and deterministic module portions of A03-A06/A08-A10/A13-A14/A16 remain substantially demonstrated: lexical all-input diamond barriers, disjoint seeded scopes, constant input members and non-controller feedback, strict controller decisions and budget failure, immutable snapshots, per-owner internal rounds, quiescent serial exposure, durable replay/claim association, separate wait/active/queue accounting, cancellation and uncertain recovery. F4 leaves the final response-format preservation requirement unsatisfied.

Prior findings:
- **F1 closed:** [engine.py:129](../../../backend/app/runtime/engine.py#L129) checks failed/cancelled/interrupted before saved envelopes. The original cancel-before-delivery probe now raises cancelled. Six regressions cover saved-envelope and blocked-delivery cancellation/failure/expiry/interruption; exposure-preserving detachment and completed-success replay remain covered.
- **F2 closed:** [engine.py:802](../../../backend/app/runtime/engine.py#L802) serializes controller payloads as JSON for json_object/json_schema. The original hello string probe now returns the JSON string `"hello"`. Tests cover escaped/numeric-looking/null-looking strings, null, bool, number, object, array, ordinary text, non-controller no-double-encoding, saved envelopes and recovery/replay.
- **F3 original literal-mutation case closed:** current traversal preserves const/enum/default/examples/extension data. The original const object containing `$ref` remains identical and validates. Resource/reference preservation is not completely correct yet, as shown by separate F4.

### Cross-Slice Consistency

The 12-file G2 surface and current frozen constructors/protocols remain consistent. No public signatures, dependency manifests or locks were changed by this fix wave. Runtime still delegates transport and external tool exposure to the provider/bridge; it does not execute tools. Actual current provider/bridge tests were included in the stable-module regression command, including their runtime/storage seam.

No analysts were requested or missing. API composition and delivery helpers were concurrent disjoint work and were not treated as completed integration evidence. G1 additive review remains a separate open gate.

### Security And Operations

No external tool execution, credentials, network probe, deployment, live-resource mutation or implementation edit was performed by this reviewer. Temporary SQLite fixtures were isolated. Storage/admission/event source and tests were re-read: dedicated serialized SQLite transactions, durable identities/CAS, immutable accepted results, first-terminal handling, fixed wait deadline, atomic claim sealing/rollback, event catch-up and admission retention remain covered. The schema probe uses the existing development-only jsonschema pin; it adds no production dependency.

### Verification And Test Adequacy

Commands ran from `D:/Sources/creep` using the repository's locked uv environment (Python 3.11.15, pytest 9.1.1, Ruff 0.16.10, jsonschema 4.26.0). The wrapper and CI configuration were inspected. The target dispatches the actual runtime/storage tests; scoped Ruff uses repository rules. API files still being written were excluded from the stable regression scope rather than being reported as fully integrated.

| Command | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py test-runtime` | 0 | 71 passed in 12.33s |
| `uv --system-certs run --project backend --locked pytest backend/tests/contracts backend/tests/graphs backend/tests/runtime backend/tests/storage backend/tests/providers backend/tests/tools -q` | 0 | 286 passed in 18.77s |
| `uv --system-certs run --project backend --locked ruff check backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | 12 files already formatted |
| Original F1-F3 probes, inverted to assert corrected behavior, via `uv --system-certs run --project backend --locked python -c $probe` | 0 | Cancelled saved tools rejected; controller string JSON preserved; literal const unchanged |
| Additional emitted-controller schema probes using the same locked invocation | 0 | Good instances accepted and bad rejected for escaped JSON pointers, anchors, dynamic anchors, anonymous Draft 2019 recursive references and recursive root pointers |
| F4 full runtime reproduction below, same locked invocation | 0 | Both empty-ID cases confirmed defective; exit 0 means the assertions reproduced the defect, not acceptance passed |
| `git status --short --untracked-files=normal`, `git diff --stat`, source reads/hashes | 0 | Current untracked implementation scope and preserved peer work confirmed |

The 30 new runtime/storage cases are meaningful and close the original reproductions, but do not cover F4. Green suite results therefore do not establish all required G2 acceptance.

Exploratory evidence was bounded carefully: declared Draft 4 legacy `id` handling failed a Draft4Validator wrapper probe, while one Draft202012Validator wrapper variant passed; the attempted assertion of failure for that latter variant exited 1 and was discarded as an unsupported hypothesis. A percent-encoded initial-slash reference probe also exited 1 before transformation because the pinned validator rejected the original reference, so it is not a product finding. No real Ollama failure is inferred from either. An extension-location reference probe demonstrated another transformation edge, but F4 is based on the simpler standard-keyword empty-ID reproduction below.

Source SHA256 at review:
- engine.py: `fda84f31f1108f9aedb3b0c4963d2b685854bbb51255e58efd105d9eb6a3dcb9`
- repository.py: `c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15`
- admission.py: `2f6e24c9ecd88aeb085724ff0c7d7cc5a8bc869bde3ab231a625dfd344c766ad`
- events.py: `009ca00b126e399d5c279be9c254f74f2e8fbca5af6cd4963ba1ea5a662b00ff`
- test_scheduler.py: `6ae10d439c2ffea63c6fefab0fe9cd3a4ce33492843584ee295e72a4c387accc`
- test_loops.py: `0cc07e31cdb177805cd38d899ea150761ab13a2ae79e2c128d6cf48ffc0170ec`
- test_recovery.py: `1d59c907f818b7eba546ba072bc4d417e7029b7078136f59fb0cde43922f9bd1`
- uv.lock: `21b6904c150ab4c13a02f47ab4e4c9825d5cf6d331554595381a82e8b245a9f0`

Exact F4 reproduction (PowerShell, no stdin/TTY, no network):
```powershell
$probe = @'
import asyncio, json, sys, tempfile
from pathlib import Path
sys.path[:0] = [str(Path("backend").resolve()),
               str(Path("backend/tests/runtime").resolve())]
from test_scheduler import Provider, create_runtime, node_request, response, submission
from test_loops import loop_graph
from app.contracts.api import ChatCompletionRequest
from app.contracts.errors import CGError, ErrorCode
from jsonschema import Draft202012Validator

async def check(identifier):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": identifier,
        "$defs": {"Text": {"type": "string"}},
        "type": "object",
        "properties": {"value": {"$ref": "#/$defs/Text"}},
        "required": ["value"],
    }
    payload = {"value": "ok"}
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    assert not Draft202012Validator(schema).is_valid({"value": 123})
    client = {
        "model": "cg/g", "messages": [{"role": "user", "content": "test"}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "answer", "schema": schema, "strict": True}},
    }
    ChatCompletionRequest.model_validate(client)
    failures = []

    async def handler(request):
        if node_request(request) == "draft":
            return response("draft")
        emitted = request.response_format.json_schema.schema_
        try:
            Draft202012Validator(emitted).validate({
                "payload": payload, "control": {"decision": "stop"}})
        except Exception as error:
            failures.append(type(error).__name__ + ": " + str(error))
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Invalid emitted schema") from None
        return response(json.dumps({"payload": payload, "control": {"decision": "stop"}}))

    with tempfile.TemporaryDirectory() as directory:
        provider = Provider(handler)
        runtime, store = await create_runtime(Path(directory), provider)
        try:
            run = await runtime.submit(submission(loop_graph(), client=client))
            try:
                await asyncio.wait_for(runtime.await_response(run.run_id, "anonymous"), 3)
            except CGError as error:
                assert error.code == ErrorCode.UPSTREAM_ERROR
            else:
                raise AssertionError("Expected embedding defect was not reproduced")
            assert len(failures) == 1 and "PointerToNowhere" in failures[0]
            assert len(provider.requests) == 2
            assert (await store.get_run(run.run_id, "anonymous")).status == "failed"
            assert client["response_format"]["json_schema"]["schema"] == schema
            print(f"$id={identifier!r}: original valid, DTO accepted; emitted schema "
                  "PointerToNowhere; real runtime/SQLite failed with upstream_error")
        finally:
            await runtime.shutdown()
            await store.close()

async def main():
    await check("")
    await check("#")

asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $probe
```

Observed output:
```text
$id='': original valid, DTO accepted; emitted schema PointerToNowhere; real runtime/SQLite failed with upstream_error
$id='#': original valid, DTO accepted; emitted schema PointerToNowhere; real runtime/SQLite failed with upstream_error
```

### Open Live Validation

G3-G6 gates remain OPEN: completed production HTTP/provider composition and shared graph/direct JSON/SSE behavior; corrected engine/provider/HTTP inside the actual rebuilt image; real process/container waiting-ID restart; pinned real Hermes/Ollama; Windows/WSL2 Compose connectivity/volume/SSE; real UI integration and target-hardware timing. Earlier Linux/SQLite 3.40.1 persistence checks used an older image and do not establish these corrected-runtime or integrated behaviors. Current tests close/reconstruct objects and SQLite connections in one process, not a production process/container restart. This review does not claim A01-A16 production completion.

### Verdict: FAIL

Reason: F4 violates required final-controller schema preservation despite closure of the original two High and one Medium findings. Current counts: Critical 0, Severe 0, High 0, Medium 1, Low/Warning/Suggestion 0. G2 has consumed 2/3 cycles; only one terminal cycle remains after any coordinator-owned scoped fix and required regressions. No reset, replacement loophole or fourth cycle is authorized. Reviewer modified only this review artifact, with no implementation edits or commits.
