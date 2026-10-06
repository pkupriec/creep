# Cognitive Graph MVP independent reviews

> Coordination shortcut: read [`current-state.md`](current-state.md) first.
> This file is the full append-only review history. Read assigned group
> sections and current evidence rather than the entire file for routine work.

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


## Task Group G4-ui - Cycle 1 - 2026-10-04
Reviewing: Waves 2 and 3 - graph files/API/compiler and React editor/history, including actual-backend browser integration.
Synthesizer: review_g4_c1. Analysts: none requested. G4 budget: 1/3, reserved before spawn in tasks/decisions at commit `5820126`. Exactly 24 assigned current files were reviewed, including untracked implementation files; an empty tracked diff was not treated as an empty implementation. Only this artifact was changed by the reviewer. Concurrent runtime and delivery work was preserved.

### Critical / Severe / High

None demonstrated in the assigned scope.

### Medium / Low / Warning

- **Medium F1 - reopening the same graph preserves stale inspector settings and can overwrite the newly loaded generation policy.** [frontend/src/editor/Editor.tsx:29](../../../frontend/src/editor/Editor.tsx#L29), [Editor.tsx:118](../../../frontend/src/editor/Editor.tsx#L118), and [frontend/src/App.tsx:79](../../../frontend/src/App.tsx#L79). **Evidence class: empirically reproduced; high confidence.** The generation textarea is independent React state, refreshed only on node click/addition. App replaces the graph from the API while retaining the Editor component keyed only by graph ID. In real Chromium with production FastAPI/file storage, select `think` at revision 1, update temperature to 0.7 through the API at revision 2, then reopen the same graph from the list. Graph/export correctly contains 0.7, but the selected node's textarea still contains the previous null. Clicking Apply generation settings and Save writes null at revision 3, confirmed by a fresh GET. This breaks section 8/A12 API-backed reload and generation editing; backend revision checks cannot prevent applying a stale form to a newly loaded revision. Other independent inspector drafts share this static lifetime concern; the runtime proof is specifically generation. **Correction:** explicitly reset or rebase inspector drafts on authoritative graph replacement (open, conflict reload, same-ID import), preserving deliberate edits within the current loaded graph. Add browser regressions proving displayed/applied settings match the loaded revision and do not restore old generation/edge/scope values.

- **Medium F2 - invalid Unicode in a node prompt returns 500 storage_error instead of 400 invalid parameter.** [backend/app/api/graphs.py:70](../../../backend/app/api/graphs.py#L70), with encoding failure at [backend/app/graphs/repository.py:146](../../../backend/app/graphs/repository.py#L146). **Evidence class: empirically reproduced; high confidence.** ASCII JSON with `nodes[1].system_prompt` containing an escaped unpaired surrogate (`invalid\ud800`) passes model validation and raises UnicodeEncodeError during snapshot UTF-8 encoding. Through actual composed `create_app`, POST create and PUT save both return HTTP 500/code `storage_error`. No invalid file is created; existing draft bytes remain unchanged. A surrogate in the constrained graph name already returns 400, so this finding is limited to the proven prompt path; equivalent unrestricted nested strings need regression coverage. Shared management `read_body` checks canonical UTF-8 encodability, while this separate graph parser does not. **Correction:** check the complete decoded graph request for canonical UTF-8 compatibility before repository operations and return sanitized `invalid_parameter`/400 for invalid input. Preserve valid supplementary Unicode, duplicate rejection, limits and prior draft bytes; cover create/save through composed HTTP handlers. Required section 4.1 invalid graph/parameter error behavior remains unsatisfied.

### Suggestion

None. Existing Vite dependency directive and bundle-size warnings were observed without inventing a material defect.

### Spec Alignment

Read the root specification/AGENTS.md, installed team-spec-workflow/team-review-cycle procedures, current durable requirements/spec/design/tasks/decisions/acceptance and prior review history. Reviewed graph contracts, generated schemas/types and API seams as needed. No acceptance/profile was weakened.

Assigned R07-R09 and A04/A06/A12/A13/A16 portions have substantial evidence: strict syntax/topology, named all-provider ports, lexical plans, feedback seeds, controller-final boundaries, disjoint scopes, immutable publications/snapshots, expected revisions, path checks, import/export/publication, prompt/generation/tool fields, feedback editing, named inputs, history/filtering, readiness, manual results, cancellation and process persistence. F1 leaves reload/edit consistency open; F2 leaves malformed-request errors open. Global runtime semantics and whole-product A01-A16 closure were not assigned here.

### Cross-Slice Consistency

Graph routes use the composition root's shared authorization. UI consumes generated schema/types and current management responses. Tokens remain in memory and fetch headers; authenticated SSE reconnects with Last-Event-ID, validates event/run identity, and never retries mutations automatically. History/detail restore API state, and browser tests demonstrate immutable run snapshots during edits.

The exact surface is graph backend eleven files plus frontend thirteen files. No analyst evidence is missing. Separate concurrent runtime corrections and final G1 additive contracts remain independent review gates; no G2/G3/G5/G6 verdict is issued here.

### Security And Operations

Graph tests cover all six authenticated routes, traversal/device identifiers, real Windows junction escape, corrupt highest publication refusal, bounded requests/files, atomic replacement/fsync fault preservation, immutable publications and racing revisions. Native Windows file-symlink privilege is unavailable; the test exercises an actual directory junction instead. Earlier Linux symlink/fsync evidence belongs to G5 and was not relabeled as a new reviewer execution.

No user secrets, installed client configuration, real tools, user Ollama state, external connectors, Docker resources or deployment were touched. Browser tests use a synthetic token, dedicated temporary data, actual FastAPI/SQLite and a mock Ollama HTTP endpoint; no browser request stubs. They do not prove real Hermes/Ollama. Standard browser run owned backend process trees 29452 -> 49080 -> 42776, stopped all, and retained `C:/Users/pkupr/AppData/Local/Temp/cg-ui-e2e-iFiizn`. Final F1 probe owned/stopped PID 50108 and retained `.../cg-ui-e2e-4yIgXR`. Final independent listener check found no listeners on 8000/5173; ports released to coordinator, no further reviewer listener use.

### Verification And Test Adequacy

Pinned tools: Python 3.11.15/locked uv, pytest 9.1.1, Ruff 0.16.10, TypeScript 5.9.3, Vitest 5.0.3, Playwright 1.61.1/cached Chromium. Wrapper/package/CI were inspected for scope. Production build finished before browser execution. Frontend unit discovery correctly excludes browser tests. All required baseline commands executed; none substitute for the failing regressions below.

| Command | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py test-graphs` | 0 | 52 passed in 0.91s |
| `npm --prefix frontend test` | 0 | 21 passed in three files |
| `npm --prefix frontend run typecheck` | 0 | Both TypeScript projects passed |
| `npm --prefix frontend run build` | 0 | Production build passed; main JS 508.57 kB/153.82 kB gzip; directive/size warnings |
| `npm --prefix frontend run test:e2e` | 0 | Four actual-backend scenarios passed in 12.7s; two actual process restarts; completed history and original pending ID survived |
| `uv --system-certs run --project backend --locked ruff check backend/app/graphs backend/app/api/graphs.py backend/tests/graphs`, then the same invocation with `ruff format --check` | 0 | All checks passed; seven files already formatted |
| `node frontend/node_modules/@playwright/test/cli.js test --config C:/Users/pkupr/AppData/Local/Temp/cg-g4-review-sjpw9oae/playwright.config.ts --grep 'generation reload shows'` | 1 | One failed: displayed temperature null versus actual 0.7; Apply/Save persisted null at revision 3 |
| Temporary browser keyboard-deletion probe in the same fixture | Case passed | `think` and both attached edges absent; hypothesized deletion bug disproved |
| F2 composed HTTP probe below via locked `python -c $cgProbe` | 0 | Reproduced POST/PUT 500 storage_error; old bytes unchanged. Exit 0 confirms the defect assertions, not acceptance |
| `Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue` filtered for 8000/5173 | 0 | Empty final result |

Exploratory accounting: initial temporary invocation used `--grep review`, which also matched the filename and ran six tests: four passed/two failed. One failure was reviewer fixture encoding (`think Â· ...` instead of `think · ...`) from an implicit Windows decode while copying the test, corrected only in the temporary copy and excluded from findings; original repository four-case suite had already passed. The other was F1, then isolated and extended to prove persisted overwrite. An initial invalid-Unicode hypothesis for graph name was disproved by 400; follow-up isolated the unrestricted prompt and final composed API proved F2 for both create/save. Discarded hypotheses are not findings. The first attempt to append this report had a PowerShell parser error from nested here-string delimiters; it executed no Python and changed no file. This successful append preserves the prior review bytes.

F1 exact reproduction using retained temporary fixture/config (runnable command above): create `review-reload`, select `think`, export revision 1, PUT generation temperature 0.7/expected_revision 1, reopen its same graph-list entry, export/read textarea, Apply generation settings, Save, and GET revision 3. Observed `actual.temperature=0.7`, `displayed.temperature=null`, then persisted `temperature=null`. Assertion `expect(JSON.parse(displayed).temperature).toBe(0.7)` fails. The temporary test is a copy of repository `mvp.spec.ts` with absolute local @playwright import/root and appended scenario; original fixture lifecycle and real backend are retained. To reproduce manually, use two browser tabs or a management PUT for the concurrent update; no external service is needed beyond the existing test fixture.

Exact F2 reproduction, PowerShell literal code argument, no stdin/listener requirement:
```powershell
$cgProbe = @"
import asyncio, json, sys, tempfile
from pathlib import Path
sys.path[:0] = [str(Path('backend').resolve()),
               str(Path('backend/tests/graphs').resolve())]
from test_validator import make_graph
from app.main import create_app
from app.contracts.config import Settings
import httpx
async def main():
    with tempfile.TemporaryDirectory(prefix='cg-g4-unicode-') as directory:
        app = create_app(Settings(data_dir=directory,
                                 ollama_base_url='http://127.0.0.1:1/v1'))
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                base_url='http://test'
            ) as client:
                good = make_graph()
                assert (await client.post('/api/graphs', json=good)).status_code == 201
                file = Path(directory) / 'graphs/test.json'
                before = file.read_bytes()
                invalid = make_graph()
                invalid['nodes'][1]['system_prompt'] = 'invalid\ud800'
                for method, route, payload in [
                    ('POST', '/api/graphs', dict(invalid, id='invalid')),
                    ('PUT', '/api/graphs/test', {'graph': invalid, 'expected_revision': 1})
                ]:
                    reply = await client.request(method, route, content=json.dumps(payload),
                                                 headers={'Content-Type': 'application/json'})
                    print(method, reply.status_code, reply.text)
                    assert reply.status_code == 500
                    assert reply.json()['error']['code'] == 'storage_error'
                assert file.read_bytes() == before
                assert not (Path(directory) / 'graphs/invalid.json').exists()
asyncio.run(main())
"@
uv --system-certs run --project backend --locked python -c $cgProbe
```

Source SHA256 (ordered 24-path/hash inventory aggregate `54ff3f31a53604c1d6fbc863570296ad02061966903231a58bdcb7fd6d4702bd`):
- `frontend/src/editor/Editor.tsx`: `c44522d12f11a8547b97f23fe9af783170ed7eb22ebb4d802017310a17758367`
- `frontend/src/App.tsx`: `ec628a591ccfadaf807875ad5a485f65963e3b150891b0f8972020c3dae738b3`
- `backend/app/api/graphs.py`: `6edbc9e25bb9e8966e01eae1fd38b4841d392446b9dfbb9f423ac8c64dbc8e07`
- `backend/app/graphs/repository.py`: `ea9dd546c16f55e9e3695fb58d9a8f7670452d180aec0a0c3acd2cbe1a721249`
- `backend/app/graphs/validator.py`: `c1b51dde9c65de68b46aa30307726878e1cc3031d9a757a3172bcc3204f02f0e`
- `frontend/e2e/mvp.spec.ts`: `0e506b7e077289269c9d6739e7d3d62e030bc7f9f455dc18b6204fb718b2610b`

### Open Live Validation

F1/F2 corrections and regressions remain required G4 gates. No requested baseline command or analyst evidence is missing. Real Hermes/Ollama, rebuilt Compose routing/Nginx SSE/volume/container restart on Windows/WSL2, target timings and final whole-product acceptance remain G5/G6 gates. Native backend/mock-upstream browser evidence does not close them.

### Verdict: FAIL

Reason: two empirically reproduced Medium defects violate required API-backed editor reload/generation consistency and malformed graph request error handling. Critical 0, Severe 0, High 0, Medium 2, Low/Warning/Suggestion 0. G4 consumed 1/3 cycles; coordinator may assign one scoped fix wave and regressions before cycle 2. No implementation fixes, commits, pushes or deployments were performed.

## Task Group G2-runtime - Cycle 3 - 2026-10-04

Reviewing: Wave 2 runtime/storage plus final fix wave 2, including the final-format production-validator consumer and G3 API seams.
Synthesizer: `review_g2_c3`; analysts: none requested. The completed `sa_g2_schema` advisory was read and reconciled against current source and executable evidence; its recommendations are not an independent verdict. This is the terminal third cycle, reserved before spawn in tasks/decisions at `b53dbb3`. The 12 assigned runtime/storage source/test files remained frozen. The reviewer changed only this appended review section.

### Critical / Severe / High

None currently demonstrated in the assigned slice. Original High F1 and F2 remain closed.

### Medium / Low / Warning

- **Medium F5 — legacy schema rebasing omits Draft 3 schema-valued keywords.** [backend/app/runtime/engine.py:657](../../../backend/app/runtime/engine.py#L657) and [engine.py:671](../../../backend/app/runtime/engine.py#L671) enumerate schema children without Draft 3 `extends` or schema alternatives in `type`. The same function explicitly accepts Draft 3 and selects rebasing for its root `$ref` at [engine.py:611](../../../backend/app/runtime/engine.py#L611) and [engine.py:631](../../../backend/app/runtime/engine.py#L631). **Evidence class: empirically reproduced; high confidence in the transformation defect, no native Ollama claim.** For each of two valid declared Draft 3 schemas, the pinned original-schema validator accepts `"ok"` and rejects `3`, and the public request DTO accepts the schema. Through the actual runtime request builder, `#/definitions/Text` inside `extends` or a `type` schema alternative is left pointing at the outer controller root and raises `PointerToNowhere`. The actual scheduler with a schema-validating fake provider and actual SQLite then commits `failed/upstream_error`, with two provider calls, zero success envelopes and an unchanged saved client policy. This is a supported final-format preservation failure, not an invalid input or a missing live-provider capability. **Specific correction for user disposition:** make traversal and reference rebasing dialect-aware for all schema-bearing locations of each retained dialect, including Draft 3 `extends` (single/list forms) and schema-valued `type`/`disallow` alternatives; retain literal data and resource boundaries. Add original-good/original-bad versus emitted-request regressions through runtime/SQLite. Do not silently narrow the accepted dialect profile. Because this is cycle 3, this recommendation is preserved for user disposition and does not authorize another automatic fix/review cycle.

### Suggestion

None.

### Spec Alignment

Read the authoritative source specification, project guidance, installed team-spec-workflow/team-review-cycle skills, current requirements/spec/design/tasks/decisions/acceptance, relevant prior independent reviews, completed SA advisory and current API/contract documentation. The new product files are untracked; `git ls-files --others --exclude-standard` confirms the exact 12-file surface. An empty tracked implementation diff was not treated as absence of implementation.

R04/R05/R06/R07/R09 and deterministic G2 portions of A03-A06/A08-A10/A13-A14/A16 have substantial current executable evidence: lexical all-input fan-in; concurrently started diamond experts; independent seeded scopes and immutable external loop inputs; controller-only exits and execution budgets; per-owner tools; immutable snapshots; durable claims, partial acceptance and first-next-response replay; fixed wait deadlines; independent queue/active/wait accounting; shared admission; cancellation/detachment; uncertain recovery and retention. The fresh 212 runtime/storage cases use actual scheduler/validator/SQLite with fake providers and clocks where appropriate. They are module evidence, not real Hermes/Ollama or container evidence.

Prior findings and advisory disposition:

- **F1 closed:** current `await_response` checks failed/cancelled/interrupted before reading saved envelopes (engine.py:129). Fresh saved-envelope and blocked-waiter tests cover cancellation, failure, expiry and interruption. Completed-success replay and exposure-preserving initial detach remain covered separately.
- **F2 closed:** final controller/native string values are JSON encoded under JSON formats; raw ordinary provider JSON remains byte-equivalent. Tests exercise quoted/numeric-looking/null-looking strings, objects/scalars, saved envelopes, reconstruction and replay. Valid ordinary `length` is preserved; invalid/truncated JSON is explicitly rejected before success as documented.
- **F3 closed for the original literal-data mutation:** const/enum/default/examples/extension literal values remain unchanged. Fresh good/bad constraint and dual-use literal/activated-reference tests execute the actual emitted schema.
- **F4 closed for its original root/nested empty or `#` resource-ID cases:** the fresh suite exercises detached-resource normalization, declared dialects, root references, relative/absolute IDs, anchors, recursive/dynamic refs and escaped pointers. Original policy is unchanged, and good payloads survive storage/reconstruction. F5 is a remaining dialect-location omission exposed by an additional independent probe; the broad schema-preservation gate therefore remains unsatisfied.
- **SA-G2-03/04 native-format gaps closed:** JSON string pass-through is encoded correctly; non-object `json_object` values and unsatisfied const/required/local-reference constraints fail before a success envelope, with `invalid_parameter` for no-LLM runs and `upstream_error` for provider outputs. `jsonschema==4.26.0` is now an exact production dependency through the separate bootstrap owner. Unknown dialects, malformed schemas and unresolved remote references fail explicitly and are sanitized. The local registry denies remote retrieval. No new public protocol or profile exception was approved by this review.

The required section 4.1/6.2 format-preservation contract remains open because of F5. Its Medium severity independently blocks acceptance; no severity escalation is used to obtain FAIL.

### Cross-Slice Consistency

Current runtime constructors and frozen repository/provider/bridge/admission protocols remain consistent. Runtime owns graph scheduling and delegates upstream transport and tool exposure; it never executes tools. The actual provider/bridge seam and composed API tests were included in fresh contract/full backend checks. Shared admission is used for graph and direct jobs; inference limits remain owned by the shared provider. No generic response disk cache, additional inference concurrency or effectful retry was introduced.

Concurrent UI correction and DevOps preparation owned disjoint files; no reviewer browser ports, listeners, Compose resources or production files were used or changed. Current G1 additive contracts and G3-G6 independent verdicts remain separate gates. No requested analyst evidence is missing.

### Security And Operations

Source inspection confirms dedicated single-thread SQLite ownership, WAL/foreign keys/FULL synchronization, short synchronous transactions, parameterized queries, durable unique identities, immutable accepted results, CAS checkpoints, and atomic response/claim sealing. Fresh tests inject a post-response/pre-claim failure and verify rollback, enforce caller/run identity, reject late/changed results, and retain committed event order. No DB transaction spans provider awaits. These are native Windows module checks; they do not replace corrected production-image SQLite checks.

Final-schema validation uses a registry whose retrieval callback rejects external resources. Invalid format/schema/reference errors are sanitized before a success envelope; no tool executor, secret access, external schema fetch, network inference, live infrastructure mutation or deployment was performed by this reviewer. F5 is a valid-input compatibility defect, not a demonstrated security exploit.

### Verification And Test Adequacy

Commands ran from `D:/Sources/creep`. The repository wrapper resolves the local `uv` executable and invokes `--system-certs run --project backend --locked`, preserving Python 3.11.15 and exact locked pytest/Ruff/jsonschema versions. The wrapper propagates failures and its targets were inspected against the pinned CI commands. No test or implementation file was edited or weakened.

| Command | Exit | Current result |
| --- | --- | --- |
| `python scripts/dev.py test-runtime` | 0 | 212 passed in 21.58s; all assigned runtime/storage cases |
| `python scripts/dev.py test-contract` | 0 | Generated schema drift clean; 163 Python contract/provider/tool cases in 5.18s and 9 frontend contract cases |
| First `python scripts/dev.py test` | 1 | Incomplete: progress contained one `F`, followed by Windows fatal access violation in jsonschema validation; no final pytest summary and frontend unexecuted |
| `uv --system-certs run --project backend --locked pytest backend/tests -x -q` | 0 | Bounded diagnostic after the preceding failure: all 475 passed in 34.00s; first failure/native exception not reproduced |
| One exact `python scripts/dev.py test` rerun | 0 | All 475 backend cases in 34.39s and 21 frontend cases across 3 files |
| `python scripts/dev.py lint` | 0 | Ruff check, 49-file format check, generated-contract drift check and both strict TypeScript projects |
| Independent F5 helper-level good/bad comparison via locked `python -c $cgProbe` | 0 | Both `extends` and schema-valued `type` originals valid; both transformed wrappers raise PointerToNowhere |
| Independent F5 actual runtime/SQLite reproduction below, same locked invocation | 0 | Both cases commit failed/upstream_error with no response envelope; zero external tools, caller policy unchanged. Exit 0 confirms defect assertions, not acceptance |
| `git diff --check` before report append | 0 | No whitespace errors in tracked changes |

The initial full-suite failure is preserved rather than relabeled green. The exposed stack ran through jsonschema `evolve`, `descend`, `ref`, `allOf`, `dynamicRef` and `properties`. The wrapper reported exit 1; a child native exit code was not exposed. Output truncation and absence of a final summary prevent identifying the initial `F` or exact crashing case. Both bounded subsequent executions passed without source changes to G2. Cause remains unassigned; this is a verification discrepancy/residual risk, not an invented product-defect finding or proof that the earlier failure was fixed. No further repeated full-suite runs were used to seek a preferred outcome.

The suite's Draft 3 parameter matrix tests declared dialects/IDs and ordinary properties/definitions, but does not exercise the schema-bearing keywords in F5. Thus its green result is insufficient for the required preservation contract. The standalone reproduction below is outside the existing suite and supplies that missing negative evidence.

Exact F5 reproduction (PowerShell literal code argument; no stdin, listener or network):

```powershell
$cgProbe = @'
import asyncio,copy,json,sys,tempfile
from pathlib import Path
sys.path[:0]=['backend','backend/tests/runtime']
from jsonschema.validators import validator_for
from referencing import Registry
from app.contracts.api import ChatCompletionRequest
from app.contracts.errors import CGError
from test_loops import loop_graph
from test_scheduler import Provider,create_runtime,node_request,response,submission
async def check(keyword):
    answer={keyword:[{'$ref':'#/definitions/Text'}] if keyword=='type' else {'$ref':'#/definitions/Text'}}
    schema={'$schema':'http://json-schema.org/draft-03/schema#','$ref':'#/definitions/Answer','definitions':{'Text':{'type':'string'},'Answer':answer}}
    original=copy.deepcopy(schema)
    v=validator_for(schema); v.check_schema(schema)
    assert v(schema,registry=Registry()).is_valid('ok')
    assert not v(schema,registry=Registry()).is_valid(3)
    client={'model':'cg/g','messages':[{'role':'user','content':'test'}],'response_format':{'type':'json_schema','json_schema':{'name':'answer','schema':schema}}}
    ChatCompletionRequest.model_validate(client)
    errors=[]
    async def handler(request):
        if node_request(request)=='draft':return response('draft')
        emitted=request.response_format.json_schema.schema_
        actual=validator_for(emitted);actual.check_schema(emitted)
        try: actual(emitted,registry=Registry()).validate({'payload':'ok','control':{'decision':'stop'}})
        except Exception as error:
            errors.append(type(error).__name__+': '+str(error).split(' does not exist')[0]);raise
        return response(json.dumps({'payload':'ok','control':{'decision':'stop'}}))
    with tempfile.TemporaryDirectory(prefix='cg-g2-c3-review-') as directory:
        provider=Provider(handler);runtime,repository=await create_runtime(Path(directory),provider)
        try:
            run=await runtime.submit(submission(loop_graph(),client=client))
            try: await asyncio.wait_for(runtime.await_response(run.run_id,'anonymous'),3)
            except CGError as error: assert error.code.value=='upstream_error'
            else: raise AssertionError('Expected broken emitted schema')
            checkpoint=await repository.load_checkpoint(run.run_id,'anonymous')
            assert checkpoint.run.status=='failed' and not checkpoint.responses
            assert len(provider.requests)==2 and errors
            assert json.loads(checkpoint.run.policy.client_request_json)==client and schema==original
            print(json.dumps({'case':keyword,'original_good':True,'original_bad_rejected':True,'emitted_error':errors[0],'run':checkpoint.run.status,'code':json.loads(checkpoint.run.error_json)['code'],'responses':len(checkpoint.responses),'provider_calls':len(provider.requests),'policy_unchanged':True}))
        finally:await runtime.shutdown();await repository.close()
async def main():
    for keyword in ('extends','type'):await check(keyword)
asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $cgProbe
```

Both observed records report `original_good=true`, `original_bad_rejected=true`, `_WrappedReferencingError: PointerToNowhere: '/definitions/Text'`, `run=failed`, `code=upstream_error`, `responses=0`, `provider_calls=2`, and `policy_unchanged=true`. Dedicated temporary SQLite fixtures were cleaned by their own context managers; no user data was accessed or removed.

Reviewed SHA256 values (re-read unchanged before report):

| File under backend/ | SHA256 |
| --- | --- |
| app/runtime/__init__.py | acc9a4b043216b2fb1b87e8600fa87871f9b0f6921611546e8bc5ae12296c403 |
| app/runtime/admission.py | 2f6e24c9ecd88aeb085724ff0c7d7cc5a8bc869bde3ab231a625dfd344c766ad |
| app/runtime/clock.py | 47053388204b0d7bca5737307c50dc3efd9976164d6a1a70b2bae75e4e7d51e8 |
| app/runtime/engine.py | b8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6 |
| app/storage/__init__.py | b5dd58e1c1e743acb4eb635f94c303613faab2f249ffb4e20fde9a9e7d49c7fa |
| app/storage/events.py | 009ca00b126e399d5c279be9c254f74f2e8fbca5af6cd4963ba1ea5a662b00ff |
| app/storage/repository.py | c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15 |
| tests/runtime/test_admission.py | 40ddc7092547e8c1c77b39c753bf377f05f438896116be1e3124958f478fb22f |
| tests/runtime/test_loops.py | e8f48ae83c881f95f117921f48e6f1beb063be0c772f6754ec55447da04bf536 |
| tests/runtime/test_recovery.py | e025646715f75896378015620a9dab0c08c45f06e9dab302cbf0f637a66be520 |
| tests/runtime/test_scheduler.py | 198246a3c9730bb9e70cf9d3db150ef3758157cb3fa65ecf2db9389367341891 |
| tests/storage/test_sqlite.py | 96afa27f1d8e0bfbe34c603edd4066b86ab38e1eba7e48d0298b5ef0edd0ff85 |

### Open Live Validation

No native Ollama, Hermes, Windows/WSL2 Compose, corrected production-image SQLite, container waiting-tools restart, or target performance check was executed in this review. Those remain required G5/G6 integration gates, as planned before this review; native module fixtures and the prior older-image storage proof cannot close them. The initial native test exception remains an unassigned verification discrepancy. F5 is an executed G2 acceptance failure and does not depend on any live gate being available.

### Verdict: FAIL

Reason: one empirically reproduced Medium defect (F5) leaves required final-controller schema preservation unsatisfied. Counts: Critical 0, Severe 0, High 0, Medium 1, Low/Warning/Suggestion 0. G2-runtime has exhausted its non-resetting 3/3 review budget and is **BLOCKED for user disposition**. Stop this group's automatic fixes/reviews; no fourth cycle, replacement, rename or artificial split is authorized. Other independent groups may continue, but the required blocked G2 group prevents MVP completion. No implementation edits, commits, pushes or deployment were performed.


## Task Group G4-ui - Cycle 2 - 2026-10-04
Reviewing: Waves 2 and 3, scoped correction wave - graph files/API/compiler and React editor/history, including actual-backend browser integration.
Synthesizer: review_g4_c2. Analysts: none requested; no missing analyst evidence. Stable G4 budget: 2/3, reserved before spawn in tasks/decisions at `0a1c615`. Both fix owners were terminal and all 24 assigned source/test/example files were frozen. This reviewer changed only this review artifact; test/build outputs are derived verification artifacts. Untracked product files were read directly, rather than treating an empty tracked diff as an empty change.

### Critical / Severe / High

None in the assigned G4 scope.

### Medium / Low / Warning

None remaining in the assigned G4 scope. Prior F1 and F2 are closed by current source and executable regressions below. The separate G2 terminal blocker is preserved under Open Live Validation and does not acquire a new group or reset its budget.

### Suggestion

None. Build directive/chunk-size notices and React Flow handle-update console warnings were observed during passing scenarios; these alone do not establish a material defect.

### Spec Alignment

Read the complete root specification, project AGENTS.md, installed team-spec-workflow/team-review-cycle skills, current durable requirements/spec/design/task/decision/acceptance state, prior G4 cycle 1 findings and G2 terminal history. Independently compared each preserved section 3-8 and 10 in spec.md with the authoritative root source: content matches after trimming section-boundary whitespace. No requirement, compatibility profile, cycle budget or acceptance criterion was relaxed.

- **F1 closed; empirically confirmed, high confidence.** Current `frontend/src/App.tsx:18` and `:40` identify authoritative loads with graphLoadVersion; successful saves use `loaded(value, false)` at `:42`. Current `frontend/src/editor/Editor.tsx:30` stores unapplied generation per node, `:35` derives unchanged settings from the current graph, and `:37` rebases generation/edge/scope inspectors only at an authoritative load. Browser regression `frontend/e2e/mvp.spec.ts:275` reproduces the original same-ID sequence against actual FastAPI/file storage: external revision 2 temperature 0.7, reopen, display 0.7, Apply/Save, then GET revision 3 still 0.7. It passes. The second regression at `:297` proves unapplied temperature 0.6 survives node reselection, prompt edits, added-port measurement and a successful save while stored temperature remains 0.2; conflict preserves local drafts, explicit reload rebases to 0.7/server edge/seed/scope, same-ID import rebases to 0.9/import values, and removing imported feedback/scope clears stale selections. Persisted revisions 4-6 retain exactly the deliberately applied imported/server values. No old null overwrite remains demonstrated.
- **F2 closed; empirically confirmed, high confidence.** Current `backend/app/api/graphs.py:71` parses duplicate-aware JSON, `:72` canonicalizes the complete decoded request and verifies UTF-8 before DTO construction/repository use, and `:74` maps invalid encoding/value/recursion to sanitized invalid_parameter/400. Current regression `backend/tests/graphs/test_api.py:182` exercises ten string/key locations, both high and low unpaired surrogates, and POST/PUT: all 40 combinations return exact 400, make no repository mutation or inference call, preserve original bytes/revision, and omit sentinel input from response/captured logs. Six positive cases at `:223` round-trip escaped supplementary-character pairs through create/get/save/validate/publish. All pass through composed production HTTP handlers and real storage.

Assigned R07-R09 and G4 portions of A04/A06/A12/A13/A16 are demonstrated: named ports and immutable optional-null input preparation; duplicate-provider/forward-cycle/undeclared-feedback/seed/controller/scope validation; atomic draft revision and immutable publication boundaries; graph creation/open/save/import/export/publish; prompt/generation/tools/ports/feedback editing; API-backed reload, named-input test starts, history/readiness/node results, manual tool results and cancellation. Browser tests additionally execute a seeded loop with two continues and final output at iteration 2, immutable active snapshots and native process persistence. This is a G4 verdict, not whole-product A01-A16 closure.

### Cross-Slice Consistency

The reviewed surface is the original eleven graph backend/example files and thirteen frontend files; no ownership expansion or analyst substitution occurred. Graph routes retain injected composition-root authorization. UI consumes generated contracts; the independent generated-drift gate passes. Authentication remains memory-only with fetch headers, including SSE Last-Event-ID reconnection; mutation requests are not retried. Run detail is API-backed, and real browser/process tests verify completed history and original waiting tool IDs across backend restart. The mock Ollama server replaces only the external inference service; no browser request stubs replace the production API/storage boundary.

Repository/validator invariants remain covered by the current 98-test graph suite: lexical port plans, multiple disjoint scopes, legal input members and noncontroller feedback sources, invalid topology/publication refusal, old snapshot/publication stability, cross-instance revision races, sanitized corrupt highest-publication refusal, safe paths, bounded payload/files and atomic replace/fsync fault behavior. Readiness/final runtime/API contracts are exercised by browser integration but remain independently owned by G2/G3/G6.

### Security And Operations

All six graph routes retain authorization tests. The malformed-Unicode guard runs before hashing/storage and checks nested JSON keys as well as values. Existing path tests reject traversal/device IDs and exercise an actual Windows directory junction escape; native Windows file-symlink creation privilege is unavailable, and no Linux symlink claim is derived from this Windows run. No token, user data, external connector, installed Hermes configuration, real tool executor, Ollama/model configuration, Docker resource or network infrastructure was accessed or changed.

Browser fixture used synthetic token, dedicated retained data `C:/Users/pkupr/AppData/Local/Temp/cg-ui-e2e-zSbiO9`, actual backend process trees PID 49316 -> 46288 -> 39212, and a local HTTP mock Ollama. Each owned backend tree was stopped by fixture cleanup. Independent final listener query returned no listeners on 8000/5173. No further listener use is planned; ports are released to the coordinator at this terminal handoff. Vite logged expected ECONNRESET during an intentional backend process restart; the original waiting ID subsequently completed successfully.

### Verification And Test Adequacy

All commands below were independently executed in this cycle from D:/Sources/creep and their terminal exit codes inspected. The repository wrapper uses locked uv/Python and the pinned frontend package scripts; CI workflow and test discovery were inspected. Production build completed before Playwright. Cached pinned Chromium was used; no browser or dependency installation occurred.

| Exact command | Exit | Current outcome |
| --- | ---: | --- |
| `python scripts/dev.py test-graphs` | 0 | 98 passed in 3.63s, including 46 new Unicode regressions |
| `npm --prefix frontend test` | 0 | 21 passed in three files |
| `npm --prefix frontend run typecheck` | 0 | Both TypeScript projects passed |
| `npm --prefix frontend run build` | 0 | Production bundle built; JS 509.13 kB / 154.03 kB gzip; directive/size notices only |
| `npm --prefix frontend run test:e2e` | 0 | Six actual-backend Chromium scenarios passed in 15.3s, including both F1 regressions and two actual backend process restarts |
| `python scripts/dev.py lint` | 0 | Explicit repository-config Ruff check, 49 format checks, generated-contract drift check and both TypeScript projects passed |
| `Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue` filtered to LocalPort 8000/5173 | 0 | Empty result; fixture listeners absent |

The malformed-Unicode tests assert the exact error envelope, pre-repository rejection, original bytes/revision and zero inference, rather than merely accepting any non-500 response. F1 browser tests assert displayed and persisted values against fresh GETs and preserve uncommitted drafts across unrelated edits; they are not DOM-only smoke checks. The full 522-test backend result in the coordinator handoff is attributed owner evidence, not a fresh execution by this reviewer. This review ran the affected graph suite plus full frontend and applicable CI lint/build/browser gates. Prior native Windows crash and earlier expiry-test ordering discrepancy remain in durable history; this targeted review does not claim to diagnose or erase them.

Reviewer audit accounting: an initial extra source-comparison command printed the 24-file hash inventory, then exited 1 because it incorrectly expected sections 3-8 to be one contiguous substring despite extraction inserting section-boundary blank lines. A corrected read-only per-section comparison exited 0 and proved each section 3,4,5,6,7,8,10 identical after boundary trim. This was a verifier assumption failure, not a source/spec drift finding; no implementation was edited to obtain the result.

Current SHA256 inventory aggregate is `90a624649afbb5da3c8ca6e08301eff55b1619f8716b2fe589bdfd81648b46ae`, computed from the ordered original 24 paths, each as `path + space + lowercase SHA256 + newline`. Key changed files, read on current disk:

| File | SHA256 |
| --- | --- |
| backend/app/api/graphs.py | dc5bb15dcb13771700d4a580868bc86af768b733f7ce752775038d572002dab2 |
| backend/tests/graphs/test_api.py | bc187ef4ca6149d163a8d4d3550011905e1b07df682835026da028980332e8a7 |
| frontend/src/App.tsx | c0e3c6c8f2ddde4c49212ae5afed5c70175ba828fcb4f0a1f8c957f708dc6647 |
| frontend/src/editor/Editor.tsx | fa28f5189f633b603b5d5bebba9b39ade56954897567ce724c002b1ec2f41bb1 |
| frontend/e2e/mvp.spec.ts | b9a4f6fecd46687d8e08d79b63001e8d720eb8d3cfb13c0c15292802c81b3c65 |

### Open Live Validation

No G4-specific required check remains unexecuted or failing in this handoff. Real Hermes/Ollama/public direct-mode integration, Windows/WSL2 Compose startup/upstream connectivity, production container waiting-ID restart and target-hardware timing remain required G5/G6 gates. Native browser/backend process tests with mock Ollama close only their stated G4 portion and do not close those real-service gates. G2-runtime remains **BLOCKED at its exhausted 3/3 budget** by the separate required Draft 3 schema-valued extends/type local-reference defect F5. Nothing in this G4 PASS authorizes an automatic G2 fix, fourth review, profile narrowing or whole-MVP completion.

### Verdict: PASS

G4-ui cycle 2: both prior Medium findings are closed, no current Critical/Severe/High finding remains in scope, and all assigned acceptance, required verification and requested reviewer evidence are demonstrated. Current open G4 finding counts: Critical 0, Severe 0, High 0, Medium 0, Low 0, Warning 0, Suggestion 0. Budget remains 2/3 consumed. Overall MVP completion remains blocked by G2 and the separately required open integration/live gates. Reviewer performed no implementation edits, commit, push or deployment.

## Task Group G3-proxy - Cycle 1 - 2026-10-04
Reviewing: Waves 2 and 3 - external Ollama transport, durable Hermes tool bridge, composed OpenAI/management API, and their unit/contract/HTTP integration evidence.
Synthesizer: review_g3_c1. Analysts: none requested; none missing. Stable G3 budget: 1/3, reserved before spawn in tasks/decisions at `bbcf33a`. The seventeen assigned product/test files were read directly because they are new untracked files. This reviewer owns only this append to review.md and made no implementation edits.

### Critical / Severe / High

None demonstrated in the assigned G3 scope.

### Medium / Low / Warning

- **Medium F1 - generic HTTPX line decoding changes SSE Unicode semantics.** `backend/app/providers/sse.py:165` consumes `response.aiter_lines()` before validating/re-encoding the resulting strings at `:166` and `:160`. The pinned HTTPX decoder uses replacement decoding and `str.splitlines()`, which treats U+0085/U+2028/U+2029 as line boundaries. **Evidence class: empirically reproduced, high confidence.** Through the actual composed `/v1/chat/completions` direct route and adapter, a single valid UTF-8 SSE JSON event containing `a\u2028b` or `a\u0085b` as literal Unicode content returns 502/upstream_error rather than preserving the text. A same-format ordinary `caf\u00e9` control returns 200. Separately, replacing the content bytes with `0xff` returns 200 with U+FFFD, `finish_reason=stop` and `[DONE]`, silently changing upstream content instead of enforcing the adapter's strict semantic boundary. All cases made exactly one mock upstream call and released admission/inference capacity. **Correction:** parse SSE framing on CR/LF/CRLF boundaries with an incremental UTF-8 policy that preserves valid code points, rejects malformed bytes before successful emission, and bounds buffered lines/events; do not use Unicode `splitlines()` for wire framing. Add byte-fragmented positive Unicode cases (including these separators) and malformed-byte cases in both content and tool arguments, with correct pre-header/post-header errors and cleanup. This is a required text/SSE preservation failure under R01/R02 and A02/A11, independently of its Medium severity.

- **Medium F2 - nonstream upstream strings are not checked for UTF-8 encodability at the provider boundary.** `backend/app/providers/ollama.py:71` returns a parsed completion without validating that its strings can be encoded for the public response. The conversion to public JSON happens later at `backend/app/api/chat.py:164`, outside the provider's sanitizing exception block. **Evidence class: empirically reproduced, high confidence.** A syntactically parsed upstream JSON completion with `content="\ud800"` passes the current DTO and the public direct route returns HTTP 500 with `code=storage_error`; no storage operation failed. The same escaped invalid scalar in SSE is correctly rejected as 502/upstream_error. The diagnostic below exercises actual FastAPI error handling with `raise_app_exceptions=False`, one upstream call and no leaked permits/leases. **Correction:** validate the complete normalized upstream JSON payload's UTF-8 encodability before returning it and map invalid Unicode to sanitized upstream_error/502. Cover content, names/IDs and nested raw tool strings, plus valid supplementary-character pairs; preserve valid raw argument strings and known metadata behavior. Do not let malformed provider data become an unrelated internal/storage error. This is a required JSON/error-boundary failure under section 4.1 and A02/A14.

### Suggestion

None.

### Spec Alignment

Read the full authoritative root specification, project AGENTS.md, installed team-spec-workflow/team-review-cycle instructions, preserved requirement/spec/design artifacts, task/decision/acceptance state, and relevant prior G0/G1/G2/G4 review history. R01-R11/A01-A16/G0-G6 identifiers and approved ownership remain unchanged. Current source and task reservation agree on the seventeen-file G3 surface; no empty tracked diff was treated as absence of implementation.

The current 212-test focused run demonstrates substantial assigned behavior: published/physical model namespaces and draft hiding; strict public parameters and standard errors; JSON/SSE tool indices/finish/DONE; model translation without substitution; immutable graph request context and final generation overrides; latest assistant/tool segment routing; opaque IDs and owner/internal-ID isolation; conservative one-call exposure; whole internal-round acceptance; exact first-next-response replay and changed-result conflicts; partial acceptance with a fixed deadline; namespace isolation; committed event replay; shared graph/direct admission and inference limits; cancellation, detach and reconstruction. These tests use the production handlers, adapter/bridge/runtime and SQLite with fake upstream HTTP or deterministic clocks. They do not prove real Hermes or Ollama acceptance.

The corrected expiry tests are meaningful: an accepted partial request is demonstrably waiting before the clock crosses the original fixed deadline and receives 504/tool_wait_timeout; a new request after persisted failure receives 409/run_terminal without inference, TTL extension or checkpoint changes. They do not accept either status indiscriminately. Full-batch fixtures deliberately construct valid durable multi-call batches to cover partial semantics even though production unknown-effect calls currently serialize one per response.

F1/F2 leave required proxy text/error preservation unsatisfied. They are not escalated to High merely to obtain FAIL. The separate G2 Draft 3 schema-reference defect remains owned by exhausted G2 and is neither reassigned nor fixed through G3.

### Cross-Slice Consistency

Composition creates one shared provider/semaphore and one shared admission controller for graph and direct jobs. Direct jobs do not invent durable graph sessions. Runtime owns execution independently of HTTP waiters; the bridge maps/exposes/accepts and reads durable claims without executing tools or inference. Inspection and focused tests confirm checkpoint-before-exposure, namespace/model checks, unchanged saved raw arguments, canonical request hashes, source-batch-to-first-next-response association, and terminal rejection. Contract factory normalization strips only declared validated transport/private reasoning metadata. G1's final additive-contract review remains separately open.

DevOps concurrently owned delivery files and actual 8000/8080 listeners. This reviewer ran only in-process mock/temporary fixtures, did not touch ports or Docker resources, and did not treat changing live smoke scripts as finalized evidence. There were no analysts or missing requested slice results. On notification of the reproduced defects, the coordinator explicitly authorized immediate cycle-1 synthesis with live results still pending; no PASS is inferred from that scheduling decision.

### Security And Operations

Bearer authorization covers both API surfaces, hashes the configured token namespace without storing the token, rejects duplicate authorization headers, and sanitizes public validation errors. Incoming JSON rejects duplicate keys, nonfinite values and invalid Unicode; body/tool-result limits precede inference. Synthetic-token tests cover snapshots/traces/captured logs and rotated namespace isolation. Health exposes storage readiness separately from upstream availability. No backend shell/MCP/tool executor, effectful retry, generic inference disk cache, external connector, secret access or cloud integration was introduced by the reviewed code.

Fresh adversarial probes confirm that the malformed/valid-Unicode cases release all admission leases and restore both inference permits. An additional in-process ASGI 2.3 disconnect probe used the protocol version actually advertised by pinned Uvicorn h11/httptools: an initial streamed graph disconnected while its provider was blocked becomes cancelled, with one upstream attempt, zero remaining leases and both permits returned. A hypothetical ASGI 2.4 behavior was not rated as a production defect. Existing tests independently cover ASGI send failure cleanup, continuation disconnection preserving shared work, and exposed tools surviving ambiguous delivery. No listener or live tool was used by this reviewer.

### Verification And Test Adequacy

All following commands were independently executed from `D:/Sources/creep`; reported terminal exit codes were inspected. Pinned uv/Python, Ruff and frontend package scripts were used. CI and `scripts/dev.py` were read to verify test discovery, explicit Ruff configuration, generated drift and locked tooling. Global delivery/build/browser gates are separately owned while DevOps is active; the current full-backend 522-pass owner result and G4 six-browser PASS are attributed evidence, not fresh executions by this reviewer.

| Exact command | Exit | Outcome |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked pytest backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py backend/tests/contracts -q` | 0 | 212 passed in 12.26s; no skipped or live tests substituted |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py` | 0 | 17 files already formatted |
| `uv --system-certs run --project backend --locked python scripts/export_contracts.py --check` | 0 | Generated contracts match Python DTOs; run separately to obtain its own exit code |
| `npm --prefix frontend run test:contract` | 0 | Nine frontend contract tests passed |
| PowerShell literal `$cgG3Probe` below, passed to `uv --system-certs run --project backend --locked python -c $cgG3Probe` | 0 | Diagnostic assertions reproduce both current defects and positive control; this is not a passing product regression |

The existing multibyte-stream test builds its body through `json.dumps()` with default ASCII escaping, so its Cyrillic text is not actually fragmented UTF-8 on the wire. It therefore does not falsify F1. Malformed-stream/JSON cases exercise syntax and metadata but omit the reproduced Unicode boundary cases. Add regressions that construct and fragment actual UTF-8 bytes and assert preservation/error behavior rather than only successful DTO construction.

Exact safe reproducer (literal code argument, no stdin, no listener, real inference or tool execution; only its owned temporary directories are cleaned):

```powershell
$cgG3Probe = @'
import asyncio, json, sys, tempfile
from pathlib import Path
sys.path[:0] = ['backend', 'backend/tests/api', 'backend/tests/providers']
import httpx
from test_chat import harness, chat, completion
from test_sse import chunk

def sse(value):
    return ('data: ' + json.dumps(chunk({'content': value}, finish='stop'), ensure_ascii=False) + '\n\ndata: [DONE]\n\n').encode('utf-8')

async def main():
    cases = [
        ('good_unicode', sse('caf\u00e9'), True, 200),
        ('valid_U2028', sse('a\u2028b'), True, 502),
        ('valid_U0085', sse('a\u0085b'), True, 502),
        ('bad_UTF8', sse('MARK').replace(b'MARK', b'\xff'), True, 200),
        ('bad_JSON_surrogate', json.dumps(completion('\ud800')).encode(), False, 500),
    ]
    for label, raw, stream, observed_status in cases:
        async def handle(_):
            return httpx.Response(200, content=raw, headers={'content-type': 'text/event-stream' if stream else 'application/json'})
        with tempfile.TemporaryDirectory(prefix='cg-g3-review-') as temp:
            async with harness(Path(temp), handle) as (app, _, calls):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url='http://test') as client:
                    result = await client.post('/v1/chat/completions', json=chat('ollama/fixture', stream=stream))
                    assert result.status_code == observed_status
                    assert len(calls) == 1 and not app.state.admission.leases
                    assert app.state.provider.limiter._value == 2
                    if label == 'bad_UTF8':
                        assert '\ufffd' in result.text and '"finish_reason":"stop"' in result.text
                        assert result.text.endswith('data: [DONE]\n\n')
                    if label == 'bad_JSON_surrogate':
                        assert result.json()['error']['code'] == 'storage_error'
                    if label.startswith('valid_'):
                        assert result.json()['error']['code'] == 'upstream_error'
                    print(json.dumps({'case': label, 'observed_status':result.status_code, 'body':result.text}, ensure_ascii=True))
    print('Confirmed current defects; this is diagnostic evidence, not a passing product regression.')
asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $cgG3Probe
```

Observed status sequence: `200, 502, 502, 200, 500`; expected corrected sequence: `200, 200, 200, 502, 502`, preserving the valid content and excluding success/DONE for malformed input. If a malformed event arrives after headers/body have started, the existing documented SSE error event is required instead of an HTTP status change. The first four probe events each contain the complete text and finish in one chunk; additional regression coverage must include fragmentation and late failures.

Current relevant SHA256 values, read immediately before synthesis:

| File | SHA256 |
| --- | --- |
| backend/app/providers/ollama.py | 6dd84aeb9e8c812fffc90180ba027a10c339da538467bb995948045d4b0f73c7 |
| backend/app/providers/sse.py | 073da1c5b68d593d325414a0bb4de543f596a9c4ac31f18e005a84dc55b7ba77 |
| backend/app/tools/bridge.py | c21d821ebfa1309778278d3b0aaa0d51f7a44488386f1b4d01d4d22f8206dfe1 |
| backend/app/api/chat.py | b68226b543b52fd5d2e68df634d68d64bc304c08a9d7cf63acebdae6ea68f058 |
| backend/app/main.py | dae170c7cf7055c10a10eb0ecd3d1456ab19571d0e6a3538c1a9a5547e3deb83 |
| backend/tests/providers/test_sse.py | fb9e302b790701691e81c7e9ca44f95570ae8b799e3f1d7b9c89111b9ec1c8a7 |
| backend/tests/api/test_runs.py | 82b792da5cf42bcf1384b3f683bc59f5911d5fde5ef0aaf5993a4d6036f1cc6e |

### Open Live Validation

Required complete G3 production evidence is still pending at synthesis: the pinned Hermes continuation/compression/replay assertions on the production API, streamed Hermes behavior, and integrated waiting-ID restart. Native adapter subsets and G0 research cannot substitute for these checks. Coordinator's latest DevOps handoff reports the corrected production services healthy and an executed container probe reaching external Ollama 0.33.3/pinned gemma4:12b through unchanged host.docker.internal. It additionally reports a bounded real public reproduction exited 0: seven JSON/SSE ordinary/multiturn/native-tool-request/manual-result exchanges through real Nginx, unknown physical model 404, and zero tool executions. The subsequent Windows project ending `417276aa` also executed those seven exchanges, protection/Nginx checks, history restart and down/up with retained publications/volume. This is attributed live evidence against unchanged provider SHA256 `6dd84a...` / SSE `073da1...`, not a reviewer execution or corrected-image proof.

That full Windows helper exited 1 in its Hermes observer: the native cg/synthesis run reportedly read two dedicated fixtures and compressed 28 messages to 6, but hooks on agent.client missed per-request SDK clients and recorded zero observed client calls/diagnostic IDs. Its required assertions therefore failed; waiting-tools container restart, exact replay and streamed Hermes phases were unexecuted. Do not count the reported partial activity as passing those gates. The same hardware timing phase executed: diamond wall 1.515s, queue 0.004944s, three calls, node durations 0.82994/0.599422/0.439565s; sequential wall 1.531s, queue 0.006202s, three calls, node durations 0.456379/0.45439/0.474423s. These coordinator-attributed measurements do not promise a speedup. Full Windows/WSL2 and complete production Hermes gates remain open; later corrected G3 images require appropriately fresh evidence.

G2-runtime remains separately **BLOCKED at 3/3** for its terminal F5 Draft 3 reference defect. No G2 fix, fourth review, accepted-profile narrowing, artificial split or budget reset is authorized by this G3 review. No whole-MVP completion claim is possible. The prior unassigned Windows native test exception remains historical evidence; this focused passing run does not diagnose it.

### Verdict: FAIL

Reason: empirically reproduced F1/F2 violate required Unicode text preservation and upstream error contracts; required real production G3 acceptance evidence also remains pending.

Counts: Critical 0, Severe 0, High 0, Medium 2, Low 0, Warning 0, Suggestion 0; required live acceptance gates are separately open rather than assigned invented defect severity. G3 consumed 1/3 cycles. Root may schedule one scoped G3 fix wave and affected checks before its next independent cycle; exhausted G2 is unchanged. Reviewer performed no product edits, commits, pushes, deployment, listeners or live inference/tool calls and releases sole review.md ownership at this terminal handoff.

## Task Group G1-contracts - Cycle 4 - 2026-10-04

Reviewing: final Wave 1 contract/bootstrap reconciliation after consumer integration.
Independent sole synthesizer: existing custom `review_g1_c3`; no analysts requested or missing.
This is the **one explicit user-authorized quota-recovery attempt**, reserved in
`cfa1214` before resumption. Historical cycle 3 consumed its attempt and failed
to return a verdict because of the account limit; its partial evidence is not
a PASS. The human authorization raises only G1's cap to four. No counter is
reset, and no automatic fifth attempt is authorized. G2 remains separately
BLOCKED at 3/3. The exact 25 read-only files are the original G1 scope excluding
`main.py`, whose ownership was transferred to API integration. New untracked
product files were inspected directly; an empty Git diff was not treated as
an empty implementation. Only this review record is authored by this reviewer.

### Critical / Severe / High

None. Prior **G1-C1-F1 remains closed**: `backend/app/contracts/api.py:55`
preserves optional tool-result `name`. Fresh Python and generated-schema/Ajv
tests validate all three authoritative pinned Hermes requests without deleting
fields or changing history, tool schemas, raw arguments or result strings.
Unknown client semantics remain rejected. Evidence class: empirically confirmed
DTO/schema behavior against recorded real-client requests, not fresh inference.

### Medium / Low / Warning

None in the assigned G1 scope. Prior **G1-C1-F2 remains closed**:
`backend/app/contracts/api.py:181` validates the private upstream DTO before
removing the explicitly declared metadata. All five pinned wire responses
preserve semantic fields; malformed or unknown metadata remains rejected.
The additive string/null `reasoning` field at `api.py:212` is excluded from
serialization and repr; public assistant/client DTOs still reject it. The
provider's distinct UTF-8 wire correction belongs to G3 and is not assigned a
G1 verdict here. Evidence class: empirically confirmed pure boundary and
current provider contract tests; independent G3 review remains separate.

### Suggestion

None. Post-verdict consolidation should replace the historical quota-blocked
G1 status text in `docs/api.md` and `docs/dependencies.md` with this outcome,
while retaining cycle 3's consumed/no-verdict history and all other blockers.
Those status paragraphs are not themselves an independent verdict.

### Spec Alignment

Reviewed the authoritative specification, AGENTS.md, installed spec-workflow
and review-cycle instructions, durable requirements/spec/design/tasks/decisions,
acceptance/completion records, prior G1 findings and later cross-group history.
A fresh executable text comparison confirms root sections 2, 3-8, 10, 9 and
11 are preserved in their respective durable artifacts. R01-R11, A01-A16,
G0-G6 and the accepted compatibility profile are unchanged.

The added `ActivationRecord.finish_reason` at
`backend/app/contracts/interfaces.py:215` preserves stop/tool_calls/length,
defaults to None for older/non-provider records, and rejects unknown values.
Fresh checkpoint round-trip tests cover the additive field; five targeted
actual runtime/SQLite tests confirm final length, final client settings and
formatted string preservation through the durable frontier. This does not
prove the separately failing Draft 3 controller embedding behavior.

Strict graph/API/config/error shapes, mandatory null-capable feedback seeds,
safe IDs, one-provider/all-input interfaces, loop-local activation identity,
immutable snapshot/hash/context/policy, durable response-sequence/claim
association, quiescent tool exposure and single shared admission/provider
boundaries remain consistent with frozen consumer contracts. Their full
operational semantics are owned by G2/G3/G5/G6, not proven by Protocols alone.

### Cross-Slice Consistency

Generated JSON Schema and TypeScript match current Python DTOs exactly.
The drift test generates into a temporary directory, deliberately alters an
output, and requires nonzero detection; it does not merely compare two copies
of a fixture. Both strict TypeScript projects pass with library checks enabled.
`frontend/vite.config.ts:5` restricts Vitest to source tests and excludes E2E;
the separate Playwright target remains intact. This review did not rerun UI
listeners or browser scenarios. G4's 98 graph/21 frontend/six browser evidence
and the provider owner's full 587 backend cases are attributed prior evidence.

All eight direct Python pins and eleven frontend pins match their locks and
installed isolated packages. Every external Python artifact has its pinned
PyPI source/hash; npm packages have exact resolved versions, registry URLs and
integrity entries. The 30 external Python records retain canonical SHA256
`673f02608ef1a1584b9c68a7f8502e2e578d6cb06f007c94b9309f0cd559c54e`.
`jsonschema==4.26.0` is a production dependency at
`backend/pyproject.toml:11`, with a 22-package production closure; it imports
in the locked Python 3.11.15 environment. Promotion did not update a version,
URL or artifact hash. No extra package manager, cache, executor or effectful
retry was introduced.

Current G1 source inventory, read immediately before synthesis (SHA256):

| File | SHA256 |
| --- | --- |
| backend/app/__init__.py | 6609cbe4d78dd2651b7f35c13173a05049a7019bf138b81903e6e68e083755d4 |
| backend/app/contracts/__init__.py | 786ff542c562452f866620f8e5070db2aee68732e34581d74430ad63319f8106 |
| backend/app/contracts/graph.py | 5689267856ca5fef107054066e2995356ff7d2093203849d9209f0e64e6c4e4b |
| backend/app/contracts/api.py | 19fb6fc72ef296dda1387d78ab82859982ff69029d470492721327e1c48718fc |
| backend/app/contracts/config.py | bd4cad3e08c46bdf4c80d0e58b09c0148d5e509f51dbe500ed3f5a328c797f17 |
| backend/app/contracts/errors.py | 09c56e897d4d2887a9dffb79ec7e32601cdeff423fd80b0390ccce5a105b4841 |
| backend/app/contracts/interfaces.py | 9a5d59c2a85f02e28ae72059c26cd7b39d97e9e03c0fc69aa7a304343834d902 |
| backend/pyproject.toml | 131dfaccd1d5a32136f19a3751a792f3838e57f114e04f7882b11a4175471acd |
| backend/uv.lock | 431c899b24fb68a2c5189dac324ef48ea63c690926d8934a1e54cb3bc84e1b07 |
| backend/.python-version | db82937e1f1830581a9553c7814f5c5fcacb6dfdef8310b43e9a812c887acaf5 |
| backend/tests/contracts/test_contracts.py | a3a84123d45266b44136a64f4517ec8cfe0e249c3d91ca7db00b19153241b4dd |
| frontend/package.json | 49381b49d7bfafcc1e9ff7be807d1e3267eebe1a938a3b7429b3b99b819090fd |
| frontend/package-lock.json | 229187d9a35f662a2b508510c72736286fa555fa747de20fc5d68bb83f341242 |
| frontend/tsconfig.json | 6ce4f15f5c94a4d25ac9365d6591eaabbdd41ada164641ff344f18dd69546085 |
| frontend/tsconfig.node.json | 8fc459036d3dd6cd26549ed893fd92257ec59a636bd363561b5c76cce50289f6 |
| frontend/vite.config.ts | 106ac622a9d1d64d1c7ec93107007afc1fd496b523d154f0dd83edb717e3cca1 |
| frontend/index.html | bb93b9a88ec07882fb8f2a2a0c7438a9dce95d085463783e304bfcaedca1b10c |
| frontend/src/contracts/generated.ts | 082535df6f312d20edcf449071d948d3c63d80689a6020934a9b127b9066651f |
| frontend/src/contracts/schema.json | d571712d96513938f52ec74f57d455e7315483b1f55abecaf1617d9d6b9a9763 |
| frontend/src/contracts/contracts.test.ts | 8d8252a11b577e9cbfe6485e7181e7b6190f00643a55570f47cd644ecff961c5 |
| scripts/export_contracts.py | e2f124ca6fa48ffe2a898d197c24df4818a2e6fb09a7aafb73bb9cdf3cfcb43b |
| scripts/dev.py | e8d87d001e71f30b9379088d2fc574304cb3164946a0730edb83c622d91bab1c |
| Makefile | 30d90e469dc3a0aa5fae4521727fce85d4616588921a5210822299a46d406df2 |
| docs/api.md | c783d4e78f74c9f35164ecddb4ef2d84422acaa95db4f39b90359d9648e7c165 |
| docs/dependencies.md | 785ee66e52e4187909bf515138096249c05fd2b663e59be4aa8620c58b1e03d6 |

### Security And Operations

Configuration defaults retain global inference 2, active 4, queue 20, separate
300/1800/1800-second budgets, 100 executions, 20 exposed batches and 30-day
retention. Strict positive limits, one-worker guard, credential-free /v1 URL,
secret exclusion and domain-separated caller namespace remain tested. No token
value was read; wrapper probes used only a synthetic token. Public schema
generation excludes private upstream metadata and settings secrets.

The wrapper at `scripts/dev.py:111` uses argument arrays, forward-slash Windows
paths, child-only allowlisted WSLENV forwarding and controlled path conversion.
Independent actual wslpath conversion includes a path with spaces and a
semicolon-separated COMPOSE_FILE list. A capture of final invocation proves
argv preservation and parent-environment immutability without running the smoke
helper. Actual native Python and WSL Python subprocesses exiting 7 propagate
exactly through `execute` at line 35. Missing file/test gates fail with 2.
No listeners, Docker resources, native Hermes, live inference, tools, installs,
global settings, commits, pushes or deployment were executed by this review.

### Verification And Test Adequacy

Fresh executions after the explicit cycle 4 authorization, from repository root:

| Exact command / probe | Terminal exit | Outcome |
| --- | ---: | --- |
| `python scripts/dev.py test-contract` | 0 | Generated drift; 228 Python tests in 7.87s; nine frontend cases in 330ms |
| `python scripts/dev.py lint` | 0 | Repository-config Ruff check; 49 files format-clean; generated drift; both strict TypeScript projects |
| `uv --system-certs run --project backend --locked pytest backend/tests/runtime/test_scheduler.py -q -k 'final_length_and_client_settings or ordinary_final_formatted_content'` | 0 | Five passed, 51 deselected, 0.90s; actual runtime/SQLite with deterministic fake provider |
| `uv --system-certs run --project backend --locked python -c $cgAudit` | 0 | Eight Python/eleven frontend pins and installed versions, all lock artifact records, production closure, schema meta-validation, both live backend source inventories |
| `uv --system-certs run --project backend --locked python -c $cgWrapperProbe` | 0 | Actual wslpath plus controlled final argv/env capture, native and WSL child exit7 propagation, absent-file/test exit2; native/WSL GNU Make unavailable |
| `uv --system-certs run --project backend --locked python -c $cgEvidence` | 0 | Preserved authoritative sections, external-record canonical hash, live JSON parsing, WSL daemon guard consistency, local API/dependency documentation links |
| `python -c $cgLive` and `python -c $cgHashes` | 0 | Read-only four-case live evidence inspection and 25-file current SHA256 inventory |
| `git diff --check` | 0 | Whitespace check only; untracked product files inspected separately |

The audit probes are literal PowerShell here-string variables passed by `-c`,
not stdin. `$cgAudit` parses both complete locks, compares direct requirements
to lock/installed versions, traverses production dependency names, checks every
artifact source/hash/integrity, validates the generated schema and compares
every recorded Windows/WSL backend source hash with current disk.
`$cgEvidence` compares authoritative root sections to the extracted artifacts
and recomputes the stated 30-record canonical hash using sorted compact JSON.
No network lookup or dependency resolution is substituted for local evidence.

The wrapper probe's first attempt exited 1 because the reviewer asserted that
`sh -c 'command -v make'` would return 1 when Make is absent; this shell returned
127. Earlier path/argv/env/exit7/missing-gate assertions had passed. Correcting
only that reviewer availability query to the documented Bash shell produced
the expected absent-Make exit1 and whole-probe exit0. This was a reviewer probe
assumption, not a product change or hidden failing product check. The historical
cycle3 checks remain partial prior evidence; they were rerun above. The older
unassigned Windows native full-suite exception remains undiagnosed by these
passing focused checks.

Make itself is unavailable on native Windows and this Ubuntu installation;
no GNU Make execution is claimed or installation performed. The inspected
Makefile delegates to the identical Python wrapper targets executed above.
The closest safe executable equivalent demonstrates those pinned gates and
their failure behavior. CI invokes those same Python targets directly; no
remote GitHub CI run is claimed. Separate build/E2E/full-suite evidence is
attributed to its owners/reviewers rather than rerun unnecessarily here.

### Open Live Validation

No required G1 contract/bootstrap evidence remains missing. Current versioned
`live-windows-compose.json` and `live-wsl-compose.json` contain backend source
inventories matching all nine current recorded files, including contracts,
provider and frozen G2 engine. Their production jsonschema pin matches 4.26.0.
Both corresponding Hermes reports record JSON and SSE cases, each three
original SDK calls/two native reads/two verified continuations and 3/5/2
node/attempt/tool-round counters. JSON cases record actual waiting-backend
restart before tool effects and real compression 28 to 6 with unchanged IDs
and results. WSL explicitly uses the Windows-native client via interoperability;
the guard records equal daemon identities. These are inspected, source-matched
**attributed G5/G6 live results**, not this reviewer's fresh live execution or
an independent delivery/integration verdict.

G3's corrected provider re-review and G5/G6 independent gates remain separate.
The concurrent delivery owner's backup/restore drill is not claimed complete
by this report. Remote CI is unexecuted. Most importantly, G2 F5 remains a
required failed schema-preservation gate at exhausted 3/3, with engine SHA256
`b8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6` unchanged.
This review neither fixes nor reclassifies that accepted Draft 3 defect and
does not authorize any G2 budget exception. Whole-MVP completion remains blocked.

### Verdict: PASS

G1-contracts passes this single user-authorized fourth attempt: both historical
findings remain closed, current additive contracts and required G1 checks are
demonstrated, and no requested analyst evidence is missing. Counts: Critical 0,
Severe 0, High 0, Medium 0, Low 0, Warning 0, Suggestion 0. G1 has consumed four
attempts under its explicit cap-four exception; cycle3's no-verdict history is
preserved. This is a scoped G1 verdict, not MVP acceptance. The reviewer releases
sole review.md ownership at this terminal handoff.

## Task Group G3-proxy - Cycle 2 - 2026-10-04

Reviewing: Waves 2/3 correction and integrated provider/tool/API consistency.
Independent sole synthesizer: existing custom `review_g1_c3`, now assigned to
G3; no analysts requested or missing. G3 cycle 2/3 was reserved in `3aaf318`
before this invocation. The group retains its ordinary maximum of three;
the earlier explicit G1-only exception does not apply here. All seventeen
assigned current product/test files were inspected directly despite being
untracked. Only this append is writable; no implementation was edited.

### Critical / Severe / High

None demonstrated in the assigned G3 scope.

### Medium / Low / Warning

- **Medium G3-C2-F3 — malformed Unicode model inventory crosses the provider
  boundary and becomes an internal/storage error.** At
  `backend/app/providers/ollama.py:147`, inventory validation checks type,
  whitespace and schema but not model-ID UTF-8 encodability; line 157 appends
  the invalid scalar and line 160 returns it. The actual models route at
  `backend/app/api/models.py:25` subsequently fails while serializing the
  response. **Evidence class: empirically reproduced, high confidence.** With
  a mock upstream returning an escaped unpaired high surrogate in its model
  ID, actual composed `GET /v1/models` returns HTTP500 `storage_error` rather
  than the required sanitized upstream502. The expected-502 probe exited 1.
  A bounded follow-up confirmed the same result for a low surrogate; a valid
  supplementary-character model ID round-trips with HTTP200. Each case makes
  one inventory request, zero inference/tool calls, leaves zero admission
  leases and both permits available. No storage operation failed. The
  completion fix at `ollama.py:74` correctly handles this class of malformed
  data for completions, but does not cover inventory. **Correction:** reject
  unencodable model IDs inside the inventory provider's sanitizing boundary
  before returning names, preserving valid Unicode exactly. Add focused
  adapter and composed `/v1/models` regressions for high/low unpaired scalars
  and a valid supplementary pair, with correct 502/error code, no retries or
  model substitution, cleanup, and coherent health behavior. This is an
  additional gap in the assigned inventory/error boundary under R02, section
  4.1 and A14; it is not claimed to have been introduced by the prior fix.
  The executed failing required error-contract assertion blocks PASS without
  escalating the finding beyond Medium.

### Suggestion

None.

### Spec Alignment

The full root specification, AGENTS.md, installed spec/review skills, current
durable requirements/spec/design/tasks/decisions/acceptance/completion and
G3-cycle1/G1-cycle4 history informed this review. R01-R11/A01-A16/G0-G6,
approved profiles, exact ownership and group counters remain unchanged.

**Prior G3-C1-F1 is closed.** Current `providers/sse.py:147` uses strict
incremental UTF-8 decoding and CR/LF/CRLF wire delimiters. The executed cases
at `tests/providers/test_sse.py:372` feed one-byte fragments containing
U+0085/U+2028/U+2029, multibyte and supplementary text across all three line
endings, preserving exact content. Raw tool fragments remain unchanged.
Tests at line 448 exercise malformed content/tool-argument bytes both before
and after headers: 502 or standard error event respectively, without fake
finish/DONE or replacement characters. Line/event bounds at lines 496/520
and permit/transport cleanup are asserted. Evidence: fresh executable tests
of actual adapter/HTTP routes with mock byte transport, plus current source.

**Prior G3-C1-F2 is closed for its completion scope.** Current
`providers/ollama.py:74` validates the entire normalized completion's UTF-8
encodability inside the provider error boundary. Cases at
`tests/providers/test_ollama.py:271` cover high/low invalid scalars in IDs,
model, content, names, text parts, tool IDs/names and raw argument strings;
composed routes at line 288 return 502/upstream_error rather than storage500.
Valid Unicode pairs and original raw argument strings survive. Fresh 277-case
focused execution passes these regressions. F3 concerns the adjacent inventory
method, not an unclosed copy of the already-fixed completion finding.

The current suite also demonstrates graph/direct model routing and draft
hiding; strict known metadata/public semantic rejection; JSON/SSE indexed
tools/finish/DONE; immutable publication/snapshot/client policy and final
overrides; opaque owner IDs/internal collisions; latest-segment/namespace
routing; conservative serial exposure and whole internal-round results;
partial acceptance, concurrent claims, exact first-next replay and conflicting
results; shared admission/inference bounds; durable events, cancellation,
disconnect, recovery and fixed TTL. The expiry tests use explicit barriers:
accepted waiting requests receive 504 at their original deadline, whereas new
submissions after persisted failure receive 409 without mutations or inference.
No assertion accepts either status indiscriminately.

### Cross-Slice Consistency

One shared provider/semaphore and admission controller serve graph and direct
requests. Runtime owns reducers independently of request lifetime; the bridge
owns durable classification/exposure/acceptance and does not execute tools.
Current APIs consume the G1 contracts independently passed in cycle4. Generated
drift and nine frontend contract tests pass. No schema, dependency, API profile,
lock, runtime or storage file was changed during this review. G2's accepted
Draft 3 controller-reference defect remains a distinct exhausted-group blocker.

Source SHA256 values read immediately before synthesis:

| File | SHA256 |
| --- | --- |
| backend/app/providers/__init__.py | e8a4d6f7785a5a3f54c0ab14bacb30163a33216b29ff7dfb7010aeace5b4d870 |
| backend/app/providers/ollama.py | 660797ab43282dba990d8ef69e8214009606d87d0d9861c28997a07182152dff |
| backend/app/providers/sse.py | 99b8128918baca052f969f897e9049ced87128766cc66a3afd5ec7a8c69ece75 |
| backend/app/tools/__init__.py | 0a6a8bbdf4d8709478d05086c1d44f8b8ccea91931db21776d5b766724438cf1 |
| backend/app/tools/bridge.py | c21d821ebfa1309778278d3b0aaa0d51f7a44488386f1b4d01d4d22f8206dfe1 |
| backend/tests/providers/test_ollama.py | 54a9979b7a6fe36232269d2490f9496f37bf2f3acedd385755bc6bf3480815b4 |
| backend/tests/providers/test_sse.py | 69272cff09b7adc0a8ee53bf9f3a254ec4c9eb233b8868e6e3b394e8346cfa2d |
| backend/tests/tools/test_bridge.py | f381916461ab671b7a770fe110e7103deb88a7824df777fbd03a0ac47ecaeb82 |
| backend/app/api/chat.py | b68226b543b52fd5d2e68df634d68d64bc304c08a9d7cf63acebdae6ea68f058 |
| backend/app/api/runs.py | 981b9aef1c3a5d274f80f71ee38aa5e1278cb1a473f0f901d6bb4758c4a71ec0 |
| backend/app/api/models.py | 9c5c58bd01d624b041048cf799c33461a3c1fccdd1c14badfa440dc811f2c178 |
| backend/app/api/security.py | dbfc177c776fa2cf9100418eaec087b45c295b71daa77a45d96d5f42e8b88dd2 |
| backend/app/main.py | dae170c7cf7055c10a10eb0ecd3d1456ab19571d0e6a3538c1a9a5547e3deb83 |
| backend/tests/api/test_chat.py | 11ba35738fa7a665f8cb43ca27512556ea55f7a94045c13b0d002b970f6cc974 |
| backend/tests/api/test_runs.py | 82b792da5cf42bcf1384b3f683bc59f5911d5fde5ef0aaf5993a4d6036f1cc6e |
| backend/tests/api/test_security.py | bf2a8df33a6320d2987fc7b4d0fae98d4fb054e95d2bdf2bcca1ed77bcc613a7 |
| backend/tests/integration/test_acceptance.py | 13b5f35a7f6ebef0f502dc4e504a63359c228b367b624064255b636e710fe5f7 |

### Security And Operations

Focused tests retain bearer coverage for API/SSE, duplicate-header rejection,
namespace separation, synthetic-token log/state exclusion, strict request JSON
and body/result limits before effects. No executor, cloud integration, generic
inference cache, effectful retry or model fallback was added. Adversarial
malformed upstream cases are isolated in temporary reviewer-owned SQLite/graph
directories and in-process HTTP transports; no service listener or external
request is involved. F3 currently produces a sanitized but incorrect internal
error code, not a demonstrated secret leak or data corruption.

### Verification And Test Adequacy

Fresh exact commands from `D:/Sources/creep` (terminal exits inspected):

| Command | Exit | Outcome |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked pytest backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py backend/tests/contracts -q` | 0 | 277 passed in 13.65s |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api/test_chat.py backend/tests/api/test_runs.py backend/tests/api/test_security.py backend/tests/integration/test_acceptance.py` | 0 | All assigned Python source/tests pass |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api/test_chat.py backend/tests/api/test_runs.py backend/tests/api/test_security.py backend/tests/integration/test_acceptance.py` | 0 | 17 files already formatted |
| `uv --system-certs run --project backend --locked python scripts/export_contracts.py --check` | 0 | Generated artifacts match current Python |
| `npm --prefix frontend run test:contract` | 0 | Nine passed, 223ms |
| `uv --system-certs run --project backend --locked python -c $cgG3InventoryProbe` with command-local PYTHONPATH=backend | 1 | Required expected-502 assertion fails: valid pair200, unpaired high500/storage_error |
| `uv --system-certs run --project backend --locked python -c $cgG3InventoryDiagnostic` | 0 diagnostic only | Confirms observed 200/500/500, one inventory call per case and no effects/leaks; **not passing product acceptance** |
| `python -c $cgG3LiveAudit` | 0 | Both recorded backend source inventories match disk; four native cases, pins, counters, restart/compression assertions verified from evidence |
| `python -c $cgG3Hashes` | 0 | Current seventeen-file inventory above |

The regression tests genuinely exercise literal wire bytes and one-byte
fragmentation rather than default ASCII-escaped JSON alone. Malformed cases
assert exact early/late error behavior and absence of fabricated success;
buffer cases assert bounded consumption and cleanup. The inventory test at
`backend/tests/providers/test_ollama.py:150` exercises a normal ASCII model
and health, but no invalid Unicode inventory; the completion tests cannot
cover this distinct method. F3 identifies that missing required boundary case.
The owner-reported 65 new cases and fail-first 32-failed/20-passed selector are
historical evidence; this reviewer independently ran the corrected current
suite, not a reconstructed old tree. G4 browser/build and full backend587
results remain attributed and were not needlessly repeated.

Reproducer for the bounded current-state diagnostic (literal PowerShell
here-string, no stdin, listeners, real inference or source edits):

```powershell
$cgG3InventoryDiagnostic = @'
import asyncio,json,sys,tempfile
sys.path.insert(0,'backend')
import httpx
from app.contracts.config import Settings
from app.main import create_app
from app.providers.ollama import HttpOllamaAdapter
async def main():
 observed=[]
 for label,model in [('valid_pair','model\U0001f600'),('unpaired_high','model\ud800'),('unpaired_low','model\udfff')]:
  calls=[]
  def handler(request):
   calls.append(request.url.path)
   assert request.url.path=='/v1/models'
   return httpx.Response(200,content=json.dumps({'object':'list','data':[{'id':model,'object':'model','created':0,'owned_by':'ollama'}]}).encode())
  with tempfile.TemporaryDirectory(prefix='cg-g3-review-inventory-') as directory:
   settings=Settings(data_dir=directory)
   async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as wire:
    provider=HttpOllamaAdapter(settings,client=wire); app=create_app(settings,provider=provider)
    async with app.router.lifespan_context(app):
     async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,raise_app_exceptions=False),base_url='http://test') as client:
      result=await client.get('/v1/models')
     assert calls==['/v1/models'] and provider.limiter._value==2 and not app.state.admission.leases
     observed.append(result.status_code)
     if label=='valid_pair':assert result.status_code==200 and result.json()['data'][0]['id']=='ollama/'+model
     else:assert result.status_code==500 and result.json()['error']['code']=='storage_error'
     print(json.dumps({'case':label,'status':result.status_code,'body':result.json(),'inventory_calls':len(calls),'inference_calls':0},ensure_ascii=True))
 assert observed==[200,500,500]
 print('Confirmed current defect; corrected required statuses are [200,502,502].')
asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $cgG3InventoryDiagnostic
```

### Open Live Validation

Unlike cycle1, complete corrected-source Windows and WSL live proof is now
available and inspected in the four versioned compose/Hermes reports,
`wsl-client-guard.json`, `final-residue-audit.json`, and delivery verification.
All nine recorded backend source hashes on both platforms match current disk,
including provider660797ab/SSE99b81289 and unchanged contracts/API/runtime.
Both full smoke commands have recorded terminal0. Seven actual direct
JSON/SSE/multiturn/native-tool-request/manual-result exchanges, unknown-model
404, Nginx behavior and history/volume recreation are attributed evidence.

Each platform's original Hermes JSON and SSE cases record three SDK requests,
two native fixture reads, two exact continuation replays and 3/5/2 node/
upstream/tool-round counts. The JSON case selects literal cg/synthesis,
restarts the actual owned backend before the first external effect, preserves
original run/IDs/owners/checkpoint/counters, and compresses 28 messages to six
with unchanged pending IDs/results. Nineteen exercised native files match the
pinned Hermes revision after normalization. The observer calls the original
SDK factory and keeps original clients/transport/executor; replay assertions
compare responses/state rather than merely noting successful status. The
restart verifier checks owned project/service/volume labels and changed PID/
start time. WSL explicitly uses the Windows-native Hermes client via interop,
not an unexecuted Linux-native installation. These are source-matched
**attributed live results**, not fresh reviewer live execution.

No previously missing G3 live gate is used as the reason for this FAIL; F3 is
an independently reproduced required local contract failure. A future provider
change needs appropriately scoped source reconciliation and regression proof;
do not silently relabel prior image evidence as evidence of changed bytes.
Separate G5 backup/restore/review and G6 acceptance remain outside this verdict.
G2 F5 remains BLOCKED3/3 with frozen engine
`b8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6`;
no fix, profile narrowing, budget reset or exception is authorized here.
The older unassigned Windows native test exception remains undiagnosed.

### Verdict: FAIL

Reason: G3-C2-F3 leaves required model-inventory upstream error handling
incorrect despite closure of the original completion/SSE findings and passing
current suites/live subsets.

Counts: Critical 0, Severe 0, High 0, Medium 1, Low 0, Warning 0, Suggestion 0.
G3 has consumed 2/3 cycles. One scoped correction wave and affected verification
may precede its terminal third cycle; no automatic fourth is available. G1's
exception and G2's blocker are unchanged. This reviewer made no product edits,
commits, pushes, listener/Docker actions or live inference/tool calls, and
releases sole review.md ownership at this terminal handoff.

## Task Group G3-proxy — Attempt 5 (explicit user exception) — 2026-10-05

Reviewing: terminal targeted F1/F2/F3 verification and G3 provider/bridge/API acceptance. Sole independent synthesizer: review_g3_medium, generic instance consuming installed review-agent and team-review-cycle instructions, Astra/medium as explicitly requested. No analysts were requested; no analyst evidence is missing. Only this review append is writable.

The original cycles 1 and 2 FAIL, cycle 3 quota failure, and user-exception attempt 4 quota failure remain consumed. This is the separately authorized fifth attempt reserved in tasks.md and decisions.md, not a reset or automatic extra cycle. The G2 coding peer owns engine.py and three runtime tests; this review issues no G2 verdict.

### Critical / Severe / High

None.

### Medium / Low / Warning

None in the assigned G3 slice. The initially observed image-ID transcription discrepancy in g3-fix-evidence.json was re-read immediately before synthesis: line 56 now agrees with g3-current-image-evidence.json at `sha256:e7c64ea53ed76dd3418c8ce32c3748be569a2113a4138aaa01d8133fd224f339`. The coordinator also supplied a fresh read-only image-inspect confirmation. This reviewer did not edit that artifact or treat the earlier typo as executable image evidence.

### Suggestion

None.

### Spec Alignment

Reviewed the root requirements and relevant durable specification, design, task/decision reservations, acceptance/completion ledgers and prior G3 findings. R01–R11, A01–A16, the accepted profile and exact group boundaries remain unchanged.

- **G3-C1-F1 closed, empirically confirmed.** `backend/app/providers/sse.py:147` implements strict incremental UTF-8 and only CR/LF/CRLF delimiters. Current `backend/tests/providers/test_sse.py:372` exercises literal U+0085/U+2028/U+2029, multibyte/supplementary text and one-byte fragmentation with each delimiter. Raw tool argument fragments remain exact. Malformed/truncated byte and escaped-surrogate cases exercise the actual adapter and ASGI route before and after stream start, asserting early 502 or late error event, no fabricated finish/DONE/replacement character, closed upstream and released semaphore/admission permits. Line/event bounds stop oversized input consumption.
- **G3-C1-F2 closed, empirically confirmed.** `backend/app/providers/ollama.py:74` encodes the complete normalized completion inside the sanitizing provider boundary. `backend/tests/providers/test_ollama.py:311` covers high/low invalid scalars in IDs, model, content, name, text parts, tool IDs/names and raw argument strings; composed HTTP cases at line 328 assert upstream502 rather than storage500. Valid supplementary pairs and original raw argument strings survive.
- **G3-C2-F3 closed, empirically confirmed.** `backend/app/providers/ollama.py:161` checks each inventory ID before it escapes the boundary. Provider regressions at `backend/tests/providers/test_ollama.py:168` and composed API regressions at `backend/tests/api/test_chat.py:135` demonstrate high/low rejection and supplementary-ID exact round-trip. An additional independent in-process ASGI probe below confirms route/health behavior together: valid200/healthy, high502/unhealthy, low502/unhealthy; sanitized upstream_error, exact valid namespace, two inventory calls per case, no inference, no run history or leaked admission/semaphore permits.

Fresh focused execution also covers physical/virtual namespace routing and draft hiding, unknown model404 without substitution, full client history/tools/raw arguments, JSON/SSE tool indices/finish/DONE, final-only payloads, opaque owner IDs/internal collisions, latest-segment/namespace routing, conservative one-call exposure, partial/full results, immutable policy, exact first-next replay and changed-result conflict. Deadline tests use explicit barriers: an accepted waiting request gets504 at its original deadline; a new submission after saved failure gets409 without mutation or inference. No assertion merely accepts either code.

### Cross-Slice Consistency

G3 consumes the shared G1 contracts and one runtime/admission/provider composition. The bridge checkpoints/classifies/accepts/results without executing tools. Actual HTTP/SQLite mocked-upstream tests exercise these seams, including recovery, cancellation, disconnect and shared graph/direct bounds. Generated contracts match and nine frontend contract checks pass.

A fresh AST/hash audit verified all eight provider methods other than models() and the surrounding module against g3-inventory-baseline.json. The current provider delta from the live-smoked `660797ab...` source is limited to inventory validation. All three hashes in g3-fix-evidence.json and g3-current-image-evidence.json match disk. The remaining recorded G3 transport/bridge/composition and shared-contract hashes match the prior Windows/WSL reports. The peer-owned G2 engine hash now differs from the historical `b8ff723d...` source; this is explicitly excluded from any claim that those images represent the entire current tree. Its correction and current-image/live reconciliation belong to G2/G6 consolidation.

Current assigned source/test SHA256 inventory:

| File | SHA256 |
| --- | --- |
| backend/app/providers/__init__.py | e8a4d6f7785a5a3f54c0ab14bacb30163a33216b29ff7dfb7010aeace5b4d870 |
| backend/app/providers/ollama.py | f58033ca681cdb84d53a83208c1095c1bee4c9775e5f0674aeea18c9cb3b174b |
| backend/app/providers/sse.py | 99b8128918baca052f969f897e9049ced87128766cc66a3afd5ec7a8c69ece75 |
| backend/app/tools/__init__.py | 0a6a8bbdf4d8709478d05086c1d44f8b8ccea91931db21776d5b766724438cf1 |
| backend/app/tools/bridge.py | c21d821ebfa1309778278d3b0aaa0d51f7a44488386f1b4d01d4d22f8206dfe1 |
| backend/tests/providers/test_ollama.py | 802b1a6e1ad0d37405c29eddf78929924e429165fe5e994a3dec2a4bbb43e420 |
| backend/tests/providers/test_sse.py | 69272cff09b7adc0a8ee53bf9f3a254ec4c9eb233b8868e6e3b394e8346cfa2d |
| backend/tests/tools/test_bridge.py | f381916461ab671b7a770fe110e7103deb88a7824df777fbd03a0ac47ecaeb82 |
| backend/app/api/chat.py | b68226b543b52fd5d2e68df634d68d64bc304c08a9d7cf63acebdae6ea68f058 |
| backend/app/api/runs.py | 981b9aef1c3a5d274f80f71ee38aa5e1278cb1a473f0f901d6bb4758c4a71ec0 |
| backend/app/api/models.py | 9c5c58bd01d624b041048cf799c33461a3c1fccdd1c14badfa440dc811f2c178 |
| backend/app/api/security.py | dbfc177c776fa2cf9100418eaec087b45c295b71daa77a45d96d5f42e8b88dd2 |
| backend/app/main.py | dae170c7cf7055c10a10eb0ecd3d1456ab19571d0e6a3538c1a9a5547e3deb83 |
| backend/tests/api/test_chat.py | bad432727c0cb8323d0c87a9ccd2ac6f9909ee70fd6ab8d3159c33c2c96b6cfe |
| backend/tests/api/test_runs.py | 82b792da5cf42bcf1384b3f683bc59f5911d5fde5ef0aaf5993a4d6036f1cc6e |
| backend/tests/api/test_security.py | bf2a8df33a6320d2987fc7b4d0fae98d4fb054e95d2bdf2bcca1ed77bcc613a7 |
| backend/tests/integration/test_acceptance.py | 13b5f35a7f6ebef0f502dc4e504a63359c228b367b624064255b636e710fe5f7 |

### Security And Operations

Fresh tests cover bearer protection on both API surfaces/SSE, duplicate authorization rejection, rotated caller namespaces, synthetic-token log/state exclusion and strict JSON/body/tool-result limits before effects. No secret access, product edits, listeners, containers, inference/tool effects, global installation, commits, external writes or delegation were performed by this reviewer. Temporary test state is isolated by the existing fixtures. Tools remain exclusively external to the proxy.

### Verification And Test Adequacy

All commands ran from D:/Sources/creep; terminal exits were inspected. The locked wrapper uses the existing backend environment and exact manifest/lock pins (pytest9.1.1, Ruff0.16.10). CI routes to the same wrapper targets. No live_probe helper was invoked.

| Exact command | Exit | Fresh outcome |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked pytest backend/tests/providers backend/tests/tools backend/tests/api backend/tests/integration/test_acceptance.py backend/tests/contracts -q` | 0 | 283 passed in14.32s |
| `python scripts/dev.py test-contract` | 0 | Generated drift matches;231 backend/provider/tool checks passed7.38s;9 frontend checks passed321ms |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api/test_chat.py backend/tests/api/test_runs.py backend/tests/api/test_security.py backend/tests/integration/test_acceptance.py` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check backend/app/providers backend/app/tools backend/app/api/chat.py backend/app/api/runs.py backend/app/api/models.py backend/app/api/security.py backend/app/main.py backend/tests/providers backend/tests/tools backend/tests/api/test_chat.py backend/tests/api/test_runs.py backend/tests/api/test_security.py backend/tests/integration/test_acceptance.py` | 0 |17 files already formatted |
| `uv --system-certs run --project backend --locked python -c $cgG3Probe` | 0 | Independent three-case inventory/health/error/no-effect assertions;200/502/502 |
| `python -c $cgG3Audit` | 0 | Unchanged non-inventory provider AST;current fix/image source hashes;historical live G3 source and Hermes source-pin reconciliation |
| `python -c $cgG3Evidence` | 0 | Four native case counters/versions/source/restart/compression assertions;17-file hash inventory |

The independent probe uses httpx.MockTransport containing ASCII-escaped inventory JSON, create_app's real lifespan/repository, ASGITransport(raise_app_exceptions=False), a temporary directory per case, GET /v1/models and GET /health/ready. Cases are model+U1F600, PRIVATE+UD800 and PRIVATE+UDFFF. It requires exact namespaced supplementary output, error code upstream_error and absence of PRIVATE for invalid cases, storage_ready=true, availability true/false/false, exactly two /v1/models upstream paths, semaphore value2, empty admission leases and zero /api/runs history. Thus it cannot pass merely because the same expected exception bypasses public serialization.

The AST audit hashes ast.dump nodes without location attributes using SHA256, checks every non-models method against method_ast_sha256, removes only models() and checks module_ast_without_models_sha256. The live audit asserts each native case has3 SDK calls/2 tool executions/2 verified continuations and counts3/5/2; nineteen source matches and exact Hermes0.18.2/OpenAI2.24.0/httpx0.28.1; JSON selects synthesis, changes backend PID/start time before any effect with unchanged counts, compresses28 to6 while preserving pending IDs/results. Both platform reports were parsed, not inferred from filenames.

Full backend593 and previous full UI/lint/build/live runs remain attributed historical evidence. They are not claimed as this review's fresh results. The scoped current checks satisfy this handoff; a concurrent full-suite run against G2 fail-first edits was intentionally avoided. Whole-tree CI and the G2 corrected-state evidence remain the coordinator's separate consolidation responsibility.

### Open Live Validation

No unclosed live gate remains **for the assigned G3 correction/slice**. The four live-windows/live-wsl compose/Hermes JSON reports provide attributed production proof for the unchanged completion/SSE/bridge/API paths: seven direct JSON/SSE/multiturn/native-tool/manual-result exchanges per platform, unknown404, Nginx streaming, actual waiting-ID backend restart, original native SDK/executor calls, compression and exact replay. Hermes source pin is caed552de1c8a8f9983bc555512412a1ac0e0a9e; external Ollama0.33.3/gemma4:12b. WSL explicitly invokes the Windows-native Hermes client via interop; no Linux-native Hermes execution is claimed.

The inventory-only provider delta has separate current-source image evidence in g3-current-image-evidence.json: Windows and WSL callers, strict supplementary/high/low cases and health, zero inference/tools/leaks, image e7c64ea53ed76dd3418c8ce32c3748be569a2113a4138aaa01d8133fd224f339, non-root/read-only/network-none controls. This is attributed coordinator execution, not fresh reviewer Docker/live execution. The unchanged-path AST audit plus independently executed corrected boundary tests makes that scoped reconciliation adequate without re-executing external effects.

The prior full images do not represent the concurrently corrected G2 engine. G2 independent review/current-runtime source reconciliation, G5/G6 independent reviews and whole-product acceptance remain separate open gates. No full-MVP completion, remote GitHub CI run, fresh real Ollama inference, fresh native tool execution or current entire-tree image PASS is asserted. The older unassigned Windows native exception remains historical residual risk rather than a newly reproduced G3 defect.

### Verdict: PASS

G3-proxy attempt5 PASS under the explicit user exception: F1/F2/F3 are closed, assigned required contracts/checks are demonstrated, no current blocking findings or missing requested reviewer evidence remain. Counts: Critical0, Severe0, High0, Medium0, Low0, Warning0, Suggestion0. Prior consumed attempts and FAILs remain preserved; this grants no automatic sixth review/fix budget. Changed file in this review: review.md only (append). Sole review.md ownership is released at this terminal handoff; the coordinator must still wait for the requested G2 worker before consolidating the wave.

## Task Group G2-runtime - Attempt 4 (explicit user exception) - 2026-10-05

Reviewing: bounded F5 recovery, original twelve-file runtime/storage scope and composed contracts/API seams. Sole independent synthesizer: review_g2_medium, generic instance consuming installed review-agent and team-review-cycle/team-spec-workflow instructions, same Astra model with explicitly requested medium reasoning. No analysts requested or missing. Only review.md append is writable.

The three original cycles remain consumed. The earlier quota-failed coding exception did not spawn a fourth G2 reviewer. This fourth attempt was reserved before spawn in tasks.md/decisions.md under the user's new explicit retry; no automatic fifth attempt or further fix wave is authorized.

### Critical / Severe / High

None currently demonstrated. Prior High F1/F2 remain closed.

### Medium / Low / Warning

- **Medium F6 — resource isolation breaks a valid mixed-dialect single-extends schema.** `backend/app/runtime/engine.py:570` embeds the detached payload schema; its non-rebasing branch at `:702` adds a synthetic resource ID at `:704` for a modern root. A Draft 2020-12 root referring to definitions/Answer, which declares Draft 3 and uses single-schema extends referring to definitions/Text, is accepted by the public DTO and pinned original-schema validator: `"ok"` passes, `3` fails. The actual emitted controller schema passes check_schema but validation of the good wrapped payload raises `AttributeError: 'str' object has no attribute 'get'` in pinned referencing resource crawling. A schema-validating fake provider through the actual scheduler and temporary SQLite commits failed/upstream_error, with two provider calls, zero success envelopes/output, no pending tools and unchanged client policy. **Evidence: empirically reproduced; high confidence in pinned emitted-schema preservation failure, no native Ollama claim.** Unlike owner-excluded fixtures whose ORIGINAL schemas failed, this original schema demonstrably accepts/rejects the expected values. **Correction for user disposition:** preserve accepted mixed-dialect reference behavior during embedding, accounting for pinned single-extends crawling; add original-good/original-bad versus actual emitted-request and scheduler/SQLite/recovery regressions while preserving literals, resource boundaries and policy. Do not narrow the accepted profile or change dependency ownership. This recommendation does not authorize another automatic fix/review loop.

### Suggestion

None.

### Spec Alignment

Consulted authoritative root specification, AGENTS.md, durable requirements/spec/design/tasks/decisions, prior G2 reviews, role/workflow instructions and g2-recovery-evidence.json. R01-R11/A01-A16 remain unchanged. G2 is the planned deterministic DAG/loops/state/recovery group; corrected production-image/live reconciliation remains separately owned by G5/G6.

- **Original F5 closed for the reported homogeneous Draft 3 cases.** engine.py:657-668 now traverses single/list extends and schema alternatives in type/disallow only under inherited/declared Draft 3. Fresh runtime tests include fourteen emitted-schema/scheduler/SQLite/replay cases and five non-Draft3 literal guards. Owner fail-first8failed/6passed exit1 and corrected14 exit0 are attributed evidence, not reviewer runs. Earlier tuple/list and original-invalid fixture diagnostics remain preserved.
- Independent eight-run probe covered single extends, extends list, type and disallow, each with valid/invalid final payloads. Original and emitted validators retained good/bad outcomes. Four good runs committed one completed JSON-string envelope; four invalid outputs committed failed/upstream_error with no envelope/output. Every run retained policy, made two fake provider calls and exposed no tools.
- Prior F1 remains closed: failed/cancelled/interrupted states precede saved-envelope delivery; blocked delivery-waiter regressions pass. F2/native-format cases preserve exact JSON serialization, ordinary raw JSON and length, reject malformed/non-object/constraint-breaking output before success, and retain recovery/replay behavior.
- Original F3 literal mutation and F4 empty/hash-ID cases remain covered and passing, including dual-use literals, anchors, dynamic/recursive references, escaped pointers and existing mixed resource tests. F6 is an additional interaction absent from that matrix.
- Fresh 231 runtime/storage cases also cover concurrent diamond/all-input readiness, lexical synthesis, seeded/disjoint loops and immutable external inputs, budgets/timeouts, owner-only tool history, single exposed batch, claims/CAS, partial/replayed results, fixed TTL, cancellation/detachment, uncertain recovery and retention.

Required section4.1/6.2 format preservation remains unsatisfied by F6. Its Medium severity is not escalated to obtain FAIL.

### Cross-Task Consistency

Runtime/storage protocols remain consistent with current shared contracts; full backend tests exercise composed API/provider/bridge seams. Twelve-file SHA audit matches cycle3 for all files except the two declared recovery edits, engine.py/test_loops.py. G3 attempt5 PASS remains separate and intact. No other source, dependency, API, UI or delivery file was edited.

### Security And Operations

Runtime delegates inference/tool delivery without executing tools. Storage retains dedicated single-thread SQLite ownership, WAL/foreign keys/FULL synchronization, short parameterized transactions, immutable identities and atomic response/claim sealing. Rollback, stale-frontier, identity, expiry-race and committed-event checks pass. Final validation denies remote resource retrieval and sanitizes failures. This reviewer used fake providers and temporary SQLite only; no listeners, containers, live inference/tool effects, secret access, global installs, deployments or commits. F6 is a compatibility failure, not a demonstrated security exploit.

### Verification And Test Adequacy

Commands ran from D:/Sources/creep. Inspected scripts/dev.py, backend/pyproject.toml and CI for pinned tooling, actual scope and failure propagation. No test was weakened.

| Command | Exit | Fresh result |
| --- | --- | --- |
| `python scripts/dev.py test-runtime` | 0 | 231 runtime/storage passed in22.27s |
| `python scripts/dev.py test-contract` | 0 | Generated drift clean;231 Python contract/provider/tool passed in7.00s;9 frontend contract passed |
| `uv --system-certs run --project backend --locked pytest backend/tests -q` | 0 | 612 passed in39.37s |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check --config backend/pyproject.toml backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage` | 0 | 12 files already formatted |
| Locked `python -c $cgProbe`, eight-run four-keyword probe described above | 0 | Four valid completed outputs/four invalid-output failures; emitted-schema, SQLite/policy assertions pass |
| Locked `python -c $cgDialectProbe`, exploratory dialect matrix | 1 | 03/03,03/04,04/03 passed;2020-12/03 emitted wrapper raised AttributeError; later03/2020-12 not reached or claimed passed |
| Locked `python -c $cgMixedProbe`, exact reproduction below | 0 | Defect assertions confirmed;failed/upstream_error,zero envelopes,two fake provider calls,policy unchanged. Exit0 proves negative reproduction, not acceptance |

Coordinator separately reports fresh `python scripts/dev.py lint` exit0 (Ruff,49-file format,drift,both TS projects); attributed evidence, not reviewer execution. Historical Windows native exception remains unexplained; one current full-suite PASS does not erase/diagnose it. Green suite omits F6 and cannot prove that remaining preservation criterion. No requested module baseline command or analyst result is missing. Initial report append hit a PowerShell nested-here-string parser error before execution and made no write; corrected with apply_patch.

Exact F6 reproduction (literal PowerShell argument, no stdin/network/listener):

```powershell
$cgMixedProbe = @'
import asyncio,copy,json,sys,tempfile
from pathlib import Path
sys.path[:0]=['backend','backend/tests/runtime']
from jsonschema.validators import validator_for
from referencing import Registry
from app.contracts.api import ChatCompletionRequest
from app.contracts.errors import CGError
from test_loops import loop_graph
from test_scheduler import Provider,create_runtime,node_request,response,submission
async def main():
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$ref':'#/definitions/Answer','definitions':{'Text':{'type':'string'},'Answer':{'$schema':'http://json-schema.org/draft-03/schema#','extends':{'$ref':'#/definitions/Text'}}}}
    original=copy.deepcopy(schema);v=validator_for(schema);v.check_schema(schema)
    assert v(schema,registry=Registry()).is_valid('ok') and not v(schema,registry=Registry()).is_valid(3)
    client={'model':'cg/g','messages':[{'role':'user','content':'test'}],'response_format':{'type':'json_schema','json_schema':{'name':'answer','schema':schema}}};ChatCompletionRequest.model_validate(client)
    observed=[]
    async def handler(request):
        if node_request(request)=='draft':return response('draft')
        emitted=request.response_format.json_schema.schema_;ev=validator_for(emitted);ev.check_schema(emitted)
        try:ev(emitted,registry=Registry()).validate({'payload':'ok','control':{'decision':'stop'}})
        except Exception as error:
            observed.append(type(error).__name__+': '+str(error));raise
        return response('{"payload":"ok","control":{"decision":"stop"}}')
    with tempfile.TemporaryDirectory(prefix='cg-g2-mixed-review-') as d:
        provider=Provider(handler);runtime,repository=await create_runtime(Path(d),provider)
        try:
            run=await runtime.submit(submission(loop_graph(),client=client))
            try:await asyncio.wait_for(runtime.await_response(run.run_id,'anonymous'),3)
            except CGError as error:assert error.code.value=='upstream_error'
            else:raise AssertionError('expected invalid emitted schema')
            cp=await repository.load_checkpoint(run.run_id,'anonymous')
            assert cp.run.status=='failed' and not cp.responses and cp.run.output_json is None
            assert len(provider.requests)==2 and observed and not cp.pending_tools
            assert json.loads(cp.run.policy.client_request_json)==client and original==schema
            print(json.dumps({'original_good':True,'original_bad_rejected':True,'emitted_error':observed[0],'run':cp.run.status,'code':json.loads(cp.run.error_json)['code'],'responses':len(cp.responses),'provider_calls':len(provider.requests),'policy_unchanged':True}))
        finally:await runtime.shutdown();await repository.close()
asyncio.run(main())
'@
uv --system-certs run --project backend --locked python -c $cgMixedProbe
```

Observed: original_good=true,original_bad_rejected=true,emitted_error=`AttributeError: 'str' object has no attribute 'get'`,run=failed,code=upstream_error,responses=0,provider_calls=2,policy_unchanged=true.

Reviewed SHA256 values:

| File under backend/ | SHA256 |
| --- | --- |
| app/runtime/__init__.py | acc9a4b043216b2fb1b87e8600fa87871f9b0f6921611546e8bc5ae12296c403 |
| app/runtime/engine.py | 7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f |
| app/runtime/admission.py | 2f6e24c9ecd88aeb085724ff0c7d7cc5a8bc869bde3ab231a625dfd344c766ad |
| app/runtime/clock.py | 47053388204b0d7bca5737307c50dc3efd9976164d6a1a70b2bae75e4e7d51e8 |
| app/storage/__init__.py | b5dd58e1c1e743acb4eb635f94c303613faab2f249ffb4e20fde9a9e7d49c7fa |
| app/storage/repository.py | c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15 |
| app/storage/events.py | 009ca00b126e399d5c279be9c254f74f2e8fbca5af6cd4963ba1ea5a662b00ff |
| tests/runtime/test_scheduler.py | 198246a3c9730bb9e70cf9d3db150ef3758157cb3fa65ecf2db9389367341891 |
| tests/runtime/test_loops.py | f574690ba105d27ae700ab1602a46b75433e6bc72ab20944cf3c9dc3db3f0f5f |
| tests/runtime/test_recovery.py | e025646715f75896378015620a9dab0c08c45f06e9dab302cbf0f637a66be520 |
| tests/runtime/test_admission.py | 40ddc7092547e8c1c77b39c753bf377f05f438896116be1e3124958f478fb22f |
| tests/storage/test_sqlite.py | 96afa27f1d8e0bfbe34c603edd4066b86ab38e1eba7e48d0298b5ef0edd0ff85 |

### Open Live Validation

No fresh real Ollama/Hermes, Windows/WSL2 Compose or production-container execution. Historical images used pre-fix b8ff723d engine and cannot prove current7a9ccb1e bytes. Current-engine production reconciliation and independent G5/G6 acceptance remain open with original provenance preserved. Those separate gates do not cause this G2 FAIL: F6 is an executed deterministic preservation failure. No whole-MVP or remote-CI PASS is asserted.

### Verdict: FAIL

G2-runtime attempt4 FAIL under the explicit user exception: original F5 is corrected, but empirically reproduced Medium F6 leaves required accepted-schema preservation unsatisfied. Counts: Critical0,Severe0,High0,Medium1,Low0,Warning0,Suggestion0. All requested reviewer evidence is present. Original three cycles plus this exception are consumed; G2 remains BLOCKED for user disposition. No automatic attempt5, replacement, fix wave, profile narrowing or artificial split is authorized. Changed file: review.md only (append). Sole review.md ownership is released at this terminal handoff.

## Task Group G2-runtime - Authorized Attempt 6 - 2026-10-06

Reviewing: terminal F6 dependency correction and unchanged G2 runtime/storage
module acceptance. Sole independent synthesizer: `review_g2_compact`, generic
instance consuming the installed review-agent role and team-review-cycle /
team-spec-workflow instructions. Analysts: none requested or missing.
Reservation: `tasks.md` active attempt6, coordinator reservation `fde0783`;
explicit human quota-retry exception, consumed **6/6** before spawn. Attempts
1–5, including attempt5's quota termination without a verdict, remain consumed.
No seventh automatic review or post-terminal fix wave is authorized.

Read `current-state.md` first, current requirements/spec/design, active task
reservation, retry decision, G2 F1–F6 review history and `g2-f6-evidence.json`.
All 24 exact implementation-source keys in that evidence manifest matched
SHA256 before verification and immediately before this append. The engine
remains byte-identical to attempt4; the F6 fix is the installed local wheel.
Only this review append was written; implementation, configuration, Git,
models, services and peer work were preserved.

### Critical / Severe / High

None.

### Medium / Low / Warning

- **Low D1 — pending-attempt status prose is stale.** `README.md:13–14`,
  `docs/api.md:46–48` and `docs/dependencies.md:48` still describe attempt5 as
  pending and prohibit an automatic sixth attempt. Static-verifiable: the
  current task reservation and top decision explicitly authorize this sixth
  review after attempt5 terminated without a verdict. This does not affect
  runtime behavior or invalidate its source-matched verification. Reconcile
  these status summaries, the vendor README and evidence/acceptance summaries
  after harvesting this verdict; preserve historical counters and open live
  gates. This is optional documentation reconciliation for G2 module PASS,
  not authorization for another review or a whole-product completion claim.

### Suggestion

None.

### Spec Alignment

Unchanged R04/R05/R06/R07/R09 and G2 module portions of
A03–A06/A08–A10/A13–A14/A16 are demonstrated by current source and executable
tests. The 259-case suite exercises real scheduler/admission/validator/SQLite:
concurrent diamond startup and lexical all-input fan-in; optional null and
missing-required-input rejection before inference; seeded two-continue loops,
independent scopes and immutable external inputs; strict controls and budgets;
owner-only histories, serial exposure and durable IDs; partial/duplicate replay,
atomic response/claim sealing, CAS races, fixed tool TTL, cancellation and late
results; waiting/queued recovery and interruption of uncertain attempts;
immutable snapshots/policy, retained history and bounded admission. These are
module tests with test providers/clocks, not real Hermes/Ollama evidence.

Prior finding dispositions, independently rechecked:

- **F1 closed.** Failed/cancelled/interrupted state precedes saved-envelope
  delivery. Saved-envelope and blocked-waiter regressions pass, including
  deadline/cancel transitions; completed replay and exposure-preserving detach
  retain their distinct behavior.
- **F2 closed.** Controller/native JSON string and scalar payloads serialize
  exactly; ordinary provider JSON bytes and valid length finish remain intact.
  Malformed/non-object/constraint-breaking output fails before a success
  envelope, including recovered tool continuations.
- **F3 closed.** Literal const/enum/default/examples and extension values retain
  their values; actual schema references and dual-use referenced literals are
  separately exercised. Caller policy remains immutable.
- **F4 closed.** Original root/nested empty and hash IDs pass. Current tests also
  exercise absolute/relative resource IDs, declared/nested dialects, anchors,
  dynamic and recursive scope, and escaped local pointers.
- **F5 closed.** Draft3 single/list extends and schema-valued type/disallow
  alternatives preserve original/emitted good/bad validation and replay.
  Non-Draft3 literal keyword guards remain passing.
- **F6 closed.** The 28 unchanged regression cases cover original/emitted
  good/bad schemas, invalid controls, mapping extends, inherited forms,
  annotation targets, root/legacy/relative/absolute IDs, recursive scope,
  escaped and percent-encoded pointers and resolver-context boundaries.
  Actual scheduler/SQLite commits completed envelopes only for valid output;
  invalid output commits failed/upstream_error with no success envelope.
  Reconstruction preserves outcome and policy without extra provider calls.
  An additional independent 12-run probe used default installed validators
  without Registry overrides or monkeypatches across Draft3/4/6/7/2019-09/
  2020-12 roots and Draft3 single-extends children, each with good/bad output.
  All original/emitted/control, persisted outcome, two-call and immutable-policy
  assertions passed. No accepted-profile narrowing or engine workaround exists.

### Cross-Slice Consistency

The exact local wheel is `referencing==0.37.0+cg.1`; jsonschema remains 4.26.0.
Manifest/uv source/lock/wheel hash and installed distribution agree. The
bootstrap owner's 31-package/29-unrelated-block preservation audit is retained
as attributed evidence at the matching current lock hash. Fresh integrity tests
verify the local pin and source directly; this reviewer did not regenerate the
lock or install another dependency.

Independent fetch of ONLY the immutable provenance wheel URL into an OS
temporary directory verified the upstream SHA. All 19 archive members were
compared after dist-info name normalization: only `jsonschema.py`, METADATA's
version and regenerated RECORD contents differ. The sole source change yields
mapping-valued Draft3 extends once; list traversal and Draft4 combinators remain
unchanged. License, dependency metadata, tests, type markers and WHEEL bytes
are preserved. The stdlib rebuild script's `--check` reproduced the shipped
wheel and provenance byte-for-byte. Its fresh wrong-hash regression rejects
input without writing output. The temporary upstream archive was removed by
its own context manager.

Runtime continues to consume shared contracts/provider/bridge interfaces and
delegates tool execution to the client. Full/contract/lint evidence below is
accepted only for its recorded source and scope. No requested analyst or G2
verification result is missing; G5/G6 are separate groups.

### Security And Operations

Dedicated-thread SQLite uses WAL, foreign keys, FULL synchronization, short
parameterized transactions, durable unique identities and optimistic versions.
Fresh rollback, race, immutable-result, namespace and committed-event tests
pass. No transaction spans provider awaits. Final schema validation retains
the deny-remote registry and sanitized failure before success. No tool executor,
inference cache, effectful retry or inference-concurrency change was introduced.

The fresh disposable image probe ran with network none, read-only filesystem,
all capabilities dropped, no-new-privileges and UID10001. It checked installed
source/engine hashes, original/emitted good/bad payloads, bad controls, immutable
schema and Draft3/Draft4 traversal; intentional remote retrieval was denied.
No inference, tools, service, volume or listener was started. `--rm` removed the
probe container; a subsequent ancestor-filtered container listing was empty.
No secrets or production data were accessed. Existing project/session policy
mismatch was not changed or treated as extra authorization.

### Verification And Test Adequacy

All commands ran from `D:/Sources/creep`; native locked environment is Python
3.11.15 with referencing loaded from `backend/.venv/Lib/site-packages`, not the
discarded `.f6-probe`. No PYTHONPATH or validator monkeypatch was introduced.

| Fresh reviewer command | Exit | Result |
| --- | ---: | --- |
| PowerShell Get-FileHash SHA256 comparison for every manifest source key, before and after checks | 0 | All 24 match |
| `uv --system-certs run --project backend --locked pytest backend/tests/runtime/test_loops.py -q -k mixed_draft3_single_extends --tb=short` | 0 | 28 passed,138 deselected,4.01s |
| `uv --system-certs run --project backend --locked pytest backend/tests/contracts/test_referencing_patch.py -q` | 0 | 10 passed,0.29s |
| `python scripts/dev.py test-runtime` | 0 | Wrapper dispatched locked pytest runtime/storage;259 passed,26.05s |
| `uv --system-certs run --project backend --locked python -c $cgDefaultProbe` | 0 | Independent 12 default-validator/scheduler/SQLite cases described above |
| `uv --system-certs run --project backend --locked python -c $cgProbe` | 0 | Immutable upstream hash/19-member audit and rebuild script --check; byte-identical wheel/provenance |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage backend/tests/contracts/test_referencing_patch.py scripts/rebuild_referencing.py` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check --config backend/pyproject.toml backend/app/runtime backend/app/storage backend/tests/runtime backend/tests/storage backend/tests/contracts/test_referencing_patch.py scripts/rebuild_referencing.py` | 0 | 14 files already formatted |
| `docker --context desktop-linux image inspect cg-f6-backend-proof:20261006-local1 --format '{{.Id}} {{.Config.User}}'` | 0 | Exact recorded image ID;10001:10001 |
| `docker --context desktop-linux run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --mount 'type=bind,source=D:\Sources\creep\.codex\specs\cognitive-graph-mvp\g2-f6-container-probe.py,target=/proof.py,readonly' --entrypoint python cg-f6-backend-proof:20261006-local1 -c "exec(compile(open('/proof.py').read(), '/proof.py', 'exec'))"` | 0 | All installed-image assertions pass; remote denied with _WrappedReferencingError |
| `docker --context desktop-linux ps -a --filter ancestor=cg-f6-backend-proof:20261006-local1 --format '{{.ID}} {{.Status}}'` | 0 | Empty; no remaining probe container |

Accepted current-source owner evidence from `g2-f6-evidence.json`, not claimed
as new reviewer executions: `uv --system-certs run --project backend --locked
pytest backend/tests -q` exit0,650 passed74.08s; `python scripts/dev.py
test-contract` exit0,241 Python plus9 frontend and generated drift clean;
`python scripts/dev.py lint` exit0,Ruff/51-file format/drift/both TypeScript
projects. Attempt5 independently completed runtime259/contracts249 and lint
before quota termination; that evidence is not an attempt5 verdict. Full and
contract suites were not rerun merely to repeat already matched evidence.
Owner Compose config/build exit0 is corroborated by the fresh actual image
execution, which proves this dependency install but not the live deployment.

Key SHA256 values (complete24-file map remains in the evidence manifest):

- Engine: `7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f`.
- F6 runtime tests: `95c7a6ad4e4931cf2b3d92252cd3723ee82d2f55aaf2ed110a0a23f50cc01562`.
- Lock: `f5240c215933c6b12858f1edb3afbdd122f45b7aa2b2429ca8d09d6fe2e94902`.
- Upstream wheel: `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231`.
- Local wheel: `a84fbf0a7365b1a0592392a2859914de38f37258f1bca97d78fce582a102804c`.
- Native/image installed source: `d71d7e00650fa3411b1957b1517d95a515461d7d428753eaf7a2719c10482c86`.
- Image: `sha256:ffc31653bf7e2ea11ed9cf22497bb67c739ae918c412232f76ebd91cd5c5e07d`.

### Open Live Validation

Fresh source-matched production Hermes/Ollama Windows/WSL2 reconciliation,
including native client continuation/process restart and integrated delivery,
remains OPEN, as do independent G5/G6 reviews. They are planned separate gates,
not waived requirements or missing G2-module proof. Historical images and this
offline probe do not satisfy them. Remote CI and operator backup/restore remain
outside this review's executed evidence. The earlier unexplained Windows native
test exception remains a historical residual risk; later passing tests do not
diagnose or erase it. No whole-MVP completion or universal-schema proof is made.

### Verdict: PASS

G2-runtime authorized attempt6 **PASS** for its assigned module acceptance.
F1–F6 are closed by current-source executable evidence; no required G2 evidence
is missing. Counts: Critical0,Severe0,High0,Medium0,Low1,Warning0,Suggestion0.
D1 is non-blocking post-verdict status reconciliation. Budget remains consumed
6/6, with no seventh automatic attempt or fix wave. Changed file: this review
append only. Sole review.md ownership is released at this terminal handoff.

## Task Group G5-delivery - Cycle 1 - 2026-10-06
Reviewing: current delivery wave, reservation consumed1/3 in tasks.md/decisions.md.
Synthesizer: review_g5_compact; generic instance consuming installed review-agent
role and team-review-cycle/team-spec-workflow instructions. No analysts requested.
Read-only slice: Compose/env/build contexts/Dockerfiles/Nginx/CI/Makefile/dev and
smoke helpers, README, runbook/verification/Hermes/dependency docs, source-matched
current evidence and relevant historical backup/review records. Only this append
is written. No source/config/Git edits or live inference/tool effects occurred.

### Critical / Severe / High
None.

### Medium / Low / Warning
- **F1 Medium, blocking required verifier contract** — `scripts/smoke_compose.py:1075`
  returns from the direct-only branch inside the protected try. If its scoped
  teardown or residue check fails, `scripts/smoke_compose.py:1383` merely saves
  cleanup_error in primary_error; the pending return skips the raise at1390.
  The CLI consequently reports success while its containers/network may remain.
  Evidence class: **empirically reproduced**, high confidence, with no Docker,
  socket, HTTP, model or tool effects: locked-Python in-process test replaces
  external calls, lets direct smoke succeed, makes own `down` raise
  CommandFailure(exit73), and observes normal return. This violates the delivery
  requirement that smoke/check/cleanup failures preserve nonzero exit. It does
  not invalidate the recorded successful full runs, which do reach the raise.
  Correction: arrange all successful execution branches to reach shared error
  propagation after finally, or raise a cleanup-only failure from finally while
  preserving an earlier primary failure. Add no-effect regression cases for
  direct-only success, down failure, residue failure, and primary+cleanup failure;
  verify the failing command's status is preserved, not merely a printed warning.
- **D1 Low, non-blocking documentation drift** — `docs/runbook.md:46` still says
  G2 BLOCKED4/4 and49 says current-engine reconciliation is open, despite its own
  current summary and source-matched success. `docs/hermes-compatibility.md:24`
  still calls F6 blocking, and135 introduces a current F5 blocker; the latter
  subsection is described as historical above but remains misleadingly titled.
  `docs/dependencies.md:41` and249–250 still leave current live reconciliation
  open. `docs/verification.md:13` and Hermes20 also retain pre-reservation0/3.
  Evidence class: **static-verifiable**, high confidence. Mark old snapshots
  explicitly historical or replace status prose with the current-state pointer,
  retaining exact earlier failures and genuine G5/G6 gates. No product criteria
  or historical exits should be changed. This Low alone would not require FAIL.

### Suggestion
None.

### Spec Alignment
R10 and delivery subsets A01/A07/A10/A15/A16 are otherwise supported. Immutable
image digests, exact dependency locks, local referencing wheel and one Uvicorn
worker match the frozen configuration. Both actual platforms use only backend
and frontend, loopback8000/8080, named cg_data:/data and external Ollama/Hermes.
A01 literal cg/synthesis is the JSON case; SSE uses a separate dedicated graph.
The two Hermes owners perform two native guarded fixture reads per case, resume
their own activations, and final synthesis contains both fixture tokens.
Current full smokes demonstrate waiting-ID backend restart before the first
native effect, preserved counters/owners/checkpoint, and completed-history
restart plus volume-preserving down/up. F1 is a helper failure-path defect,
not a new product/runtime or protocol finding.

### Cross-Task Consistency
Accepted G0PASS2/G1PASS4/G2PASS6/G3PASS5/G4PASS2 remain their independent results;
no budget is reset. Source audit here independently matched both live manifests
against current disk:29 application files and9 input files per platform,
22-package inventories and installed referencing member hashes against the
committed wheel. Both manifests contain exit0 and provenance-probe0. Four live
JSONs and summary agree on current images, IDs, original pinned Hermes files,
two continuations per case and executed restart/compression. Backup audit uses
its historically named image; unchanged storage source supports its narrowly
claimed file/SQLite-copy semantics, not current inference/schema acceptance.

### Security And Operations
Static controls and live metadata agree on UID10001/101, read-only roots, tmpfs,
cap-dropALL/no-new-privileges, one worker, no GPU/socket/host-tool mounts, and
external execution boundaries. Nginx forwards auth/cursors, disables buffering,
cache/gzip and configures1860second timeouts above1800second budgets. Auth/log/
queue/limits acceptance retains separate current API/runtime/browser evidence.
Backup instructions stop the chosen backend, preserve all files/WAL together,
use immutable image/fresh empty volumes, validate archive paths/UIDs, and retain
original data. Historical e4f18bc2 audit.json confirms logical SQL equality,
pre-start file equality and post-restart IDs/checkpoints; failed physical-byte
assumption remains exit1, corrected read-only audit remains0. No user backup or
new restore was performed here. F1 must prevent false cleanup success.

### Verification And Test Adequacy
All fresh commands ran from D:/Sources/creep; exact pinned tooling is inherited
through uv locked backend. In-process probes run only reviewed script logic.

| Fresh reviewer command | Exit | Outcome |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/dev.py scripts/smoke_compose.py scripts/smoke_hermes.py` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check --config backend/pyproject.toml scripts/dev.py scripts/smoke_compose.py scripts/smoke_hermes.py` | 0 | Three files formatted |
| `wsl --exec bash -n /mnt/d/Sources/creep/scripts/smoke_compose.sh` | 0 | Shell syntax |
| `python scripts/smoke_compose.py --context desktop-linux --validate-only` | 0 | Actual Windows config/target parsing; no runtime claim |
| `python scripts/dev.py smoke-compose --validate-only` | 0 | Actual Windows-to-WSL path/argument/config dispatch; Linux caller, no runtime claim |
| `uv --system-certs run --project backend --locked python -c $cgProbe` | 0 | Reproduced F1: normal main return after injected down exit73; this exit0 confirms the bug, not acceptance |
| `uv --system-certs run --project backend --locked python -c $cgAudit` | 0 | Both29-source/9-input/wheel-member audits;22 package records;19 pinned Hermes files and two verified continuations per case; six fresh residue queries |

The first reviewer probe draft exited1 with an unclosed literal before importing
or invoking application logic; corrected probe above reproduced F1. First hash
audit exited1 on a reviewer-assumed key `referencing_member_hashes`; corrected
actual key `referencing_sources` passed. Neither failed probe changed files.
Each fresh residue command is the exact argv from the corresponding manifest's
current_source_provenance containers/networks/volume fields, using
`docker --context desktop-linux`; all6 exit0 match empty container/network arrays
and the two retained exact-project volumes.

Reproduction core for the lead (PowerShell here-string $cgProbe, then command
above; no test file or implementation was written by this reviewer):
```python
import importlib.util, json, sys
from unittest.mock import patch
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('smoke','scripts/smoke_compose.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
b={'ports':[{'host_ip':'127.0.0.1','published':8000}], 'volumes':[{'type':'volume','target':'/data','source':'cg_data'}], 'environment':{'CG_DATA_DIR':'/data','WEB_CONCURRENCY':'1'}}
f={'ports':[{'host_ip':'127.0.0.1','published':8080}]}
c={'services':{'backend':b,'frontend':f},'volumes':{'cg_data':{'name':'cg-review-cleanup_cg_data'}}}
seen=[]
def run(cmd,**kwargs):
    seen.append(cmd)
    if 'down' in cmd: raise m.CommandFailure(cmd,73)
    if 'context' in cmd and 'show' in cmd: return 'desktop-linux'
    if 'version' in cmd: return 'linux/amd64'
    if 'config' in cmd and 'json' in cmd: return json.dumps(c)
    return ''
class Socket:
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def bind(self,*args): pass
with patch.object(sys,'argv',['smoke_compose.py','--project','cg-review-cleanup','--model','fixture','--direct-only']), patch.object(m,'run',run), patch.object(m.socket,'socket',Socket), patch.object(m.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps({'sources':{}}),returncode=0)), patch.object(m,'direct_smoke',return_value={}), patch.dict(m.os.environ,{'CG_DATA_DIR':'/data','COMPOSE_PROFILES':''}):
    m.main()
assert any('down' in cmd for cmd in seen)
print('BUG: main returned normally despite cleanup exit73')
```

Accepted owner commands, not rerun here: exact two full argv arrays in
live-current-summary.json phases both exit0, respectively native
scripts/smoke_compose.py and Windows scripts/dev.py smoke-compose through WSL.
Each built actual images and exercised seven direct exchanges plus authentic
Hermes JSON/SSE/replay/compression, with successful scoped down and independent
residue proof. Source-matched g2-f6-evidence.json records full backend650,
runtime259, contracts241Python+9frontend and lint51/drift/bothTS, all0;
current-ui-evidence.json records frontend21, six real-backend Playwright cases
and build0. CI pins actions/toolchains and executes these wrappers plus Compose
config; it does not purport to supply external Hermes/Ollama. Static checks
alone would not satisfy the live gates, but matching executed local evidence is
present. F1 lacks an adequate cleanup-failure regression in the current gates.

### Open Live Validation
No additional required G5 successful-path live run is missing. Remote GitHub CI,
arbitrary-user restore/cutover and WSL host-copy variant were not executed and
are not required substitutes for the accepted isolated local drill. WSL uses
Windows-native pinned Hermes via explicit interop, not a Linux Hermes install.
One WSL UTC node duration is unusable after clock adjustment; no speed claim is
accepted from one target sample. Fix F1 with no-effect lifecycle regressions;
repeat live inference/tool effects is unnecessary for this control-flow fix.
Independent G6 remains separate OPEN0/3, contingent on corrected G5 acceptance.

### Verdict: FAIL
Reason: reproduced F1 violates required nonzero smoke/cleanup failure reporting.
Counts: Critical0,Severe0,High0,Medium1,Low1,Warning0,Suggestion0. G5 cycle1/3
is consumed; one scoped fix wave and cycle2 are available under the existing
budget. Full live successes are preserved, not relabeled as failures. Changed
file: this review append only. Sole review.md ownership released at terminal
handoff; no child workers were spawned or remain active under this reviewer.

## Task Group G5-delivery - Cycle 2 - 2026-10-07
Reviewing: cycle1 scoped fix wave1, consumed2/3 before spawn in tasks.md and
 decisions.md. Synthesizer: review_g5_cycle2, generic instance consuming the
installed review-agent role, team-review-cycle and team-spec-workflow.
Analysts: none requested. Scope: the reserved delivery slice plus its new
lifecycle regression file and g5-fix-evidence.json. Only this append is written;
no implementation, Git, resource, inference or external tool effects performed.

### Critical / Severe / High
None.

### Medium / Low / Warning
None remaining in the reviewed implementation. Prior F1 and D1 are closed:
- F1: scripts/smoke_compose.py:1381 now raises a cleanup-only exception directly
  inside finally. This overrides the pending direct-only return, preserving
  CommandFailure.exit_code. An existing primary error still reaches the shared
  raise at1391, and cleanup failure cannot replace it. The successful path,
  exact-project down without -v, and independent residue queries are unchanged.
  Evidence: static control-flow inspection and fresh executable regressions.
- D1: docs/runbook.md:46 and docs/hermes-compatibility.md:18 now identify accepted
  G2/current-source live evidence. The old F5 section at Hermes136 is explicitly
  historical; docs/dependencies.md:41 and249 and docs/verification.md:25 retain
  historical evidence with current-state pointers. No historic failure was
  relabeled success. Fix-wave status prose predates this cycle's verdict;
  normal coordinator post-verdict status reconciliation remains, not a product
  or required verification defect.

### Suggestion
None.

### Spec Alignment
R10 and assigned delivery subsets A01/A07/A10/A15/A16 remain demonstrated.
The helper fix changes failure reporting only. Reviewed root specification,
requirements/spec/design, frozen environment defaults and delivery interfaces
remain aligned: backend/frontend only, loopback8000/8080, cg_data:/data, one
backend worker, external Ollama and Hermes execution, pinned images/toolchains.
No application/authentication/concurrency/tool policy or dependency changed.

### Cross-Task Consistency
Fresh byte audit matched all six g5-fix-evidence.json hashes. Reversing exactly
the finally correction yields prior helper SHA256
3bf4204d8d0626c524cdc807703f83db07d96bba4e383829a6ff54f2e7feeedb,
matching BOTH accepted current Windows/WSL manifests. Per platform, all29
application hashes and9 input hashes reconcile (helper by exact reversal),
22 installed package records remain present, and all15 referencing wheel
members equal recorded installed members. The wheel archive itself matches
its recorded SHA256. Both provenance probes and full helper exits remain0.
Thus successful-path live evidence remains applicable without repeating effects.
G0–G4 independent verdicts and budgets are preserved; G6 is separate OPEN0/3.

### Security And Operations
The correction preserves scoped teardown and volume retention. Tests verify
project selection, absence of -v/--volumes, label-filtered residue checks,
primary-error precedence and actual CLI status73/1/29. Existing non-root,
read-only roots/tmpfs, cap-drop, no-new-privileges, auth forwarding, SSE buffering
controls, fixed limits and external execution boundaries remain unchanged.
Cycle1's accepted isolated backup audit and source-matched native Hermes JSON/
SSE/restart/replay/compression proof retain their explicit source/platform scope.
This review does not claim a user-data restore or newly executed live smoke.

### Verification And Test Adequacy
All fresh commands ran from D:/Sources/creep with locked repository tooling:

| Exact command | Exit | Result |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked pytest backend/tests/delivery/test_compose_smoke.py -q` | 0 | 11 passed in0.08s |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py backend/tests/delivery/test_compose_smoke.py` | 0 | All checks passed |
| `uv --system-certs run --project backend --locked ruff format --check --config backend/pyproject.toml scripts/smoke_compose.py backend/tests/delivery/test_compose_smoke.py` | 0 | Two files formatted |
| `uv --system-certs run --project backend --locked python -c $cgAudit` | 0 | Six hashes, exact helper reversal, both29-source/9-input/wheel-member audits |
| `uv --system-certs run --project backend --locked python -c $cgMore` | 0 | Both22-package inventories and installed/wheel member equality |

The first reviewer byte-reversal draft exited1 because it assumed LF in a CRLF
file; the corrected byte-preserving audit above passed. This was a reviewer
probe error, not an implementation or evidence mismatch; no file was changed.
The small inspection commands also exited0. No new validate-only/live invocation
was necessary for this isolated error-handler change and unchanged delivery
configuration; cycle1's executed Windows/WSL static dispatch checks are retained.

Regression adequacy: tests at delivery/test_compose_smoke.py:175–265 exercise
real main control flow with effects forbidden/intercepted, direct success,
down failure, both residue failures, combined primary/cleanup failures, the
actual parsed CLI guard and full-path success/cleanup failure. They assert
numeric exits, not only log messages. Recorded pre-fix3failed/4passed proves the
original missing-raise cases. CI's test wrapper collects backend/tests, including
this file; its lint wrapper includes tests/scripts. The mocks intentionally
prove error control flow, not Docker runtime semantics.

Accepted source-matched owner evidence in g5-fix-evidence.json: full locked
backend661passed45.11s exit0; python scripts/dev.py lint exit0 (Ruff52 formats,
schema drift, both TypeScript projects); four-doc UTF8/local-link audit39 exit0.
Those broader unchanged-source checks were assessed rather than repeated.
Actual Windows/WSL successful build/health/Ollama/Hermes/restart/teardown proof
remains in live-current-summary.json and its four manifests, independently
reviewed in cycle1 and freshly byte-reconciled here. Static tests alone are not
being substituted for that executed evidence.

### Open Live Validation
No required G5 live-validation gate remains open. Remote GitHub CI execution,
arbitrary user-data restore/cutover and the WSL host-copy variant remain unrun
and explicitly outside the accepted isolated local drill's claims. Existing
single-sample/WSL wall-clock timing limitations remain; no speed guarantee.
G6 independent whole-product integration acceptance remains OPEN0/3.

### Verdict: PASS
G5-delivery cycle2 PASS; F1/D1 closed, required delivery acceptance and
verification evidence present, no new blocking regression. Counts:
Critical0,Severe0,High0,Medium0,Low0,Warning0,Suggestion0. Budget remains2/3.
Changed file: review.md append only. Sole review.md ownership is released at
this terminal handoff; no child agents were spawned or remain active.
