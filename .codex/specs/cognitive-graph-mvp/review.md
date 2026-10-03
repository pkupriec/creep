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
