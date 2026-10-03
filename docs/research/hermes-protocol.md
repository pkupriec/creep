# RD1: pinned Hermes continuation research

RD1 demonstrates transparent function-tool continuation with the installed real
Hermes client and external local Ollama. This is a research bridge, not the MVP
runtime. G0's coordinator and independent reviewer own its final gate decision.
Requirements: R01/R03, scenarios A07–A10, root specification sections 7 and RD1.

## Versions and evidence

- Hermes distribution `0.18.2`, Git revision
  `caed552de1c8a8f9983bc555512412a1ac0e0a9e`.
- Installed source:
  `C:/Users/pkupr/AppData/Local/hermes/hermes-agent`; Python `3.11.15`.
- Actual client dependencies: OpenAI SDK `2.24.0`, httpx `0.28.1`.
- Ollama `0.33.3`, external `http://127.0.0.1:11434/v1`.
- Tested physical model `gemma4:12b`, immutable installed digest
  `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
  Metadata advertises completion/tools/thinking/vision; this experiment tests
  text and native function tools only.
- Isolated research tools and their transitive packages are exactly pinned in
  [hermes-requirements.txt](../../experiments/hermes-requirements.txt).
- [hermes-traces.json](../../experiments/hermes-traces.json) contains actual
  Hermes HTTP bodies, native Ollama calls/results, SQLite ownership mappings,
  checkpoints, exact replay checks, and compression evidence. It excludes HTTP
  authorization headers and uses only dedicated synthetic fixture content.
  Model reasoning is not needed to inspect continuation correctness.

The installation is **not a clean checkout**: Git reported 3,175 modified
entries. Research rejects a changed HEAD or different normalized content for
the 18 inspected production source files, including the transport, conversation
loop, compressor, auxiliary client, tool executor, and file implementation.
Their raw and LF-normalized SHA256 hashes are recorded in each trace. All 18
match the pinned Git objects after CRLF normalization. This is evidence for
those source files; it does not attest that every installed file or dependency
matches an upstream clean installation. No installed file was edited.

## Reproduce safely on Windows

Run from the repository root. Use a new dedicated work directory for each
experiment; fixtures and SQLite state remain for inspection and are never
deleted. The commands use the installed Hermes venv solely as a read-only
dependency/source supplier; pytest and ruff run from project isolation.

```powershell
python -m venv .venv/hermes-research
uv pip install --system-certs --python .venv/hermes-research/Scripts/python.exe -r experiments/hermes-requirements.txt
.venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q
$env:CG_RD1_HERMES='1'
.venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q
.venv/hermes-research/Scripts/python.exe -m ruff check experiments/hermes_bridge.py experiments/test_hermes_bridge.py
.venv/hermes-research/Scripts/python.exe -m ruff format --check experiments/hermes_bridge.py experiments/test_hermes_bridge.py
```

Without `CG_RD1_HERMES=1`, the four real-client tests are explicitly skipped.
With it, the actual installed client performs fixture reads for nonstream,
fragmented SSE, simultaneous two-owner calls, and serialized two-owner calls.
The deterministic provider in these tests proves client/tool behavior and does
not stand in for a real model test.

Real external Ollama, both owners, SSE, serialized external calls, checkpoint
reload, actual compression, and exact replay:

```powershell
.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/hermes-rd1/live-gemma5-final --owners 2 --stream --restart --compress --serial-tools --upstream http://127.0.0.1:11434/v1 --model gemma4:12b --trace .venv/hermes-rd1/live-gemma5-final.json
```

Other tested commands:

```powershell
.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/hermes-rd1/nonstream2 --owners 1 --restart --trace experiments/hermes-traces.json
.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/hermes-rd1/live-gemma2 --owners 1 --stream --restart --upstream http://127.0.0.1:11434/v1 --model gemma4:12b --trace .venv/hermes-rd1/live-gemma2.json
.venv/hermes-research/Scripts/python.exe experiments/hermes_bridge.py --work-dir .venv/hermes-rd1/live-gemma3 --owners 2 --restart --upstream http://127.0.0.1:11434/v1 --model gemma4:12b --trace .venv/hermes-rd1/live-gemma3.json
```

These CLI runs exit 0 only after actual Hermes reaches completion, every owner
receives the real fixture result, and final synthesis completes. The proxy only
emits `read_file` calls whose exact argument path is that owner's fixture.
Hermes runs the original file tool/executor on Windows outside Compose.

The initial `pip install pytest==8.4.2 ruff==0.13.3` failed with local CA trust
validation. `uv pip install --native-tls ...` succeeded using system trust;
the newer synonym `--system-certs` is verified as the reproducible command.
TLS verification was never disabled. No global package installation occurred.

## Actual protocol and continuation decisions

`AIAgent(base_url=..., provider="custom", api_mode="chat_completions",
model="cg/research")` uses its original OpenAI-compatible transport,
conversation loop, assistant-message construction, tool dispatch, and file
executor. It keeps calling the model after `finish_reason=tool_calls` and
finishes only after the proxy returns final synthesis.

Actual client request keys observed in the final streaming experiment:
`messages`, `model`, `max_tokens`, `parallel_tool_calls`, `stream`,
`stream_options`, `tools`. Nonstream requests omit streaming options. Hermes
does not echo a diagnostic run header or use completion IDs as sessions.

Use `cg_` plus an opaque random UUID (35 alphanumeric/underscore characters).
Actual Hermes preserves these IDs in assistant history and role=tool results.
Its API sanitizer strips whitespace, canonicalizes tool argument JSON with
sorted keys, repairs malformed arguments and tool pairs, and removes duplicate
ID references. Mapping must use the external ID; store a canonical JSON
arguments hash rather than comparing raw JSON strings. Preserve the original
assistant/function envelope privately in the owning activation.

The research mapping persists external ID, run ID, owner, internal ID, canonical
arguments hash, delivered flag, and accepted result. Both synthetic owners use
the same internal ID `collision`, while opaque external IDs remain distinct.
Only the owner receives its own result; synthesis receives owner payloads in
stable `a`, then `b` order. Native model-generated call IDs are preserved in
the real-model traces; collision injection belongs to the deterministic real
Hermes/client experiment, not a claim that Ollama produced identical IDs.

Each new initial request receives a random run ID, even for identical questions.
Routing inspects only the latest assistant/tool segment, not all old history.
Unknown IDs, mismatched model/caller namespace, mixed new user turn, cross-run
ambiguity, and changed accepted results fail explicitly. Exact continuation
hash plus run mapping replays the identical cached completion without another
node inference or tool delivery. Historical closed IDs followed by a completed
assistant answer and new user message create a fresh run.

Both tool owners complete their initial inference before external delivery.
Thus a `waiting_tools` checkpoint has no uncertain sibling upstream work. The
prototype uses sequential initial computation for this research; production
G2 must add the specification's globally bounded concurrent scheduler while
retaining this quiescent external-delivery boundary. `parallel_tool_calls=false`
delivers one owner at a time; actual Hermes executes two tool rounds and three
API requests. Partial-result tests wait for the remaining delivered IDs and
never deliver an accepted call again. Hermes submitted full batches in actual
runs; partial batches are contract tests only.

`--restart` closes and reconstructs the SQLite-backed bridge object **before**
Hermes submits tool results. Old external IDs complete the same persisted run.
This proves bridge-state reconstruction, not a Docker/backend process restart.
An additional regression marks an uncertain active checkpoint `interrupted`
on reconstruction and confirms it performs no automatic inference restart.
Production process recovery and TTL/cancellation remain G2/G6 responsibilities.

## Compression, time, and streaming limits

The pinned `ContextCompressor` protects a recent tail, aligns boundaries around
assistant-tool groups, then sanitizes orphaned pairs. Its preprocessing may
prune old results and truncate old tool arguments. The unconditional pre-call
sanitizer can insert a stub for an orphaned result. A proxy must route the latest
pending IDs and reject ambiguity; it cannot rely on a complete old transcript.

`--compress` adds inert closed historical turns, explicitly forces one research
boundary at the actual Hermes pre-call sanitizer, and invokes the real
`ContextCompressor.compress`, `_generate_summary`, and original auxiliary
`call_llm` against external Ollama. Only boundary timing/history size and a
512-token tail budget are forced. The summarizer is a real model, not a fake
summary. The latest external ID and result remain byte-identical; the next
actual Hermes request carries the compacted history and resumes its owner.
The trace records before/after counts and IDs. This is a transparent ID/path
proof on a forced boundary, not an assertion that every possible context size,
configuration, or future Hermes version is compatible.

Research writes only an isolated `HERMES_HOME` under its work directory and
suppresses installed/project dotenv discovery to avoid credential access.
Context-file loading and memory are disabled; only the original `read_file`
schema is offered. MCP refresh is disabled for the research client; no external
server is enabled. The isolated compression config names the local physical
model/endpoint with a dummy OpenAI SDK key. Global CLI/profile startup and
production authentication are not exercised or reconfigured.

Hermes defaults to 90 iterations; the harness uses 8. One owner consumes two
API calls; two serialized owners consume three. Its ordinary per-call timeout
defaults to 1,800 seconds, with per-model/provider configuration taking
precedence over `HERMES_API_TIMEOUT`. The harness sets 300 seconds. Local
nonstream calls disable the implicit stale timer; an explicit configured timer
still applies. Streaming cloud read/stale defaults are 120/180 seconds and
local endpoint handling differs. The compressor has a 300-second effective
timeout floor. Product run/tool TTLs must be documented separately; comment
heartbeats do not relax the client's total request deadline.

Actual Hermes accepted an SSE comment heartbeat, role delta, indexed fragmented
function arguments, `finish_reason=tool_calls`, final content, final finish
reason, and `[DONE]`. Nonstream has equivalent completion behavior. No internal
node payload is delivered as final text until synthesis finishes.

The first real Gemma attempt used a 256-token research generation cap with
default thinking; it exhausted the cap three times and exited 1 with
`model_length_before_completion`. No tool was delivered or executed. The
successful model-specific research settings are `max_tokens=512`,
`temperature=0`, `reasoning_effort="none"` for node inference and an isolated
compression override. This changes the research model's thinking behavior;
it is **not** an added accepted client parameter or a proposed universal
product default. The frozen client profile must retain the authoritative
parameter list and reject unsupported semantic fields.
[Ollama documents the `none` thinking control](https://docs.ollama.com/api/openai-compatibility).
Gemma sometimes summarizes a fixture without quoting its token despite a prompt;
ownership correctness is established by the exact persisted result/messages,
not by assuming model prose always reproduces every byte.

## Verification and remaining gates

Focused failing test was observed before implementation: pytest exited 1 during
collection because `hermes_bridge` did not exist. Final verification:

| Exact command | Exit | Evidence |
| --- | --- | --- |
| `$env:CG_RD1_HERMES='1'; .venv/hermes-research/Scripts/python.exe -m pytest experiments/test_hermes_bridge.py -q` | 0 | 16 passed in 16.75s: 12 contracts/recovery cases, 4 actual Hermes executions |
| `.venv/hermes-research/Scripts/python.exe -m ruff check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | All checks passed |
| `.venv/hermes-research/Scripts/python.exe -m ruff format --check experiments/hermes_bridge.py experiments/test_hermes_bridge.py` | 0 | Both files formatted |
| `uv pip install --system-certs --python .venv/hermes-research/Scripts/python.exe -r experiments/hermes-requirements.txt` | 0 | Seven exactly pinned packages checked; uv 0.11.28 |

The final live CLI command above exited 0. Its measured wall time was 20.0207s,
including source verification, actual Hermes setup/tools, real compression,
and graph completion. It made three Hermes HTTP completions, executed two real
Hermes reads, and made five node/final Ollama requests (one shared model), plus
the separate real-model compression request. Measured node request durations
were 2.4373s, 1.1241s, 1.8591s, 1.2153s, and 1.4771s. Compression reduced 28
messages to six, retained `cg_e91ca6c7979e40b89aa5c788d4328f1a` and its exact
result, then returned a final graph answer. Both continuation replay checks
returned the cached original response. This sequential research fixture is not
a GPU throughput benchmark or evidence of production parallel speedup.

These results close RD1's tested continuation and model-context research risk;
they do not claim A01–A16 product acceptance. Remaining required work includes
the production graph scheduler/loops, immutable revisions and run snapshots,
atomic checkpoint/event/replay transactions, cancellation and TTL handling,
direct-mode/error/SSE integration, broader tool schemas, and clean
Windows/WSL2 Compose smoke. The prototype deliberately handles one tool request
per owner and is unsuitable as a production continuation implementation.
Its partial-batch envelope includes a `research_status` marker for direct tests;
the MVP must wait/return the agreed API behavior rather than copy this envelope.

The coordinator records authoritative decisions under
`.codex/specs/cognitive-graph-mvp/decisions.md`; this task does not edit shared
specification or review files.
