# Hermes compatibility profile

The tested research client is Hermes0.18.2, revision
`caed552de1c8a8f9983bc555512412a1ac0e0a9e`, OpenAI SDK2.24.0/httpx0.28.1.
[G0 evidence](research/hermes-protocol.md) demonstrates original Hermes
Chat Completions transport, native file execution, opaque tool IDs, compression
and continuation against a research bridge. G1 validates its three actual
request histories and five Ollama responses. Complete corrected-image Windows
and WSL2 production smokes passed: original Hermes JSON/SSE, two native guarded
reads per case, owner routing, exact replay, original waiting IDs across backend
restart and real compression. WSL Compose used the existing Windows-native
client through explicit interoperability with equal daemon IDs and pinned
versions. The earlier observer failure remains historical evidence; the
original per-request SDK factory is now observed without replacing transport.
[Verification](verification.md) records exact source/image/run evidence and
accepted independent reviews and residual limitations.

G0–G4 independently PASS; G2 attempt6 closed F1–F6 with the accepted schema
profile unchanged. Earlier F5/F6 failures and quota terminations remain
historical evidence. Current-source full Windows/WSL2 live validation passed
with the exact application and installed wheel bytes matched; earlier native
proofs retain their original source attribution. G5 PASS2/3 and G6 PASS1/3
close the mandatory integration and delivery gates. See
[current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md) for review
status and [current live verification](verification.md#current-source-full-live-validation-2026-10-06)
for source-matched evidence and the independent acceptance record.

Configure the Hermes custom OpenAI-compatible provider with API mode
`chat_completions`, base URL `http://127.0.0.1:8080/v1` (or native backend port
8000), and the exact model `cg/<published_graph_id>`. Direct mode uses
`ollama/<installed_name>`. Use the local bearer token as the custom API key when
`CG_API_TOKEN` is configured; anonymous local mode accepts a nonsecret dummy
SDK key. Never store a token in graph JSON, URLs, traces or source control.
This MVP does not implement Responses or native Ollama `/api/chat`.

Accepted top-level keys are `model`, `messages`, `tools`, `tool_choice`,
`parallel_tool_calls`, `stream`, `temperature`, `top_p`, `max_tokens`, `stop`,
`response_format`, `stream_options`, and `n=1`. Text messages preserve system,
developer, user, assistant and tool histories, including optional tool-result
`name`. Function schemas and raw argument/result strings are retained.
Multimodal content and other semantic fields fail400; `reasoning_effort` is
not a public request parameter. See [API contracts](api.md) for exact shapes
and the explicitly validated upstream metadata normalization policy.

Both JSON and SSE return only final external output or tool calls. The finish
reason is `stop`, `tool_calls`, or `length`. `X-CG-Run-ID` is diagnostic;
completion IDs are not session IDs. During a tool boundary, Hermes executes
the returned native calls and sends role=tool results with opaque `cg_` IDs.
Only the owning activation receives its results. One external batch is open
at a time; unknown or effectful calls serialize conservatively, and
`parallel_tool_calls=false` delivers at most one call. The separate fixed
tool-wait TTL includes downtime. Cancellation cannot undo Hermes side effects.

The latest relevant assistant/tool segment identifies a continuation. Old
closed history does not resume completed work; a new user turn creates a new
run, even for an identical question. Mixed pending IDs and a new user turn,
unknown IDs, changed accepted content, model/namespace mismatch and late
results fail409. Exact continuation replay returns its durable response
without another node or tool execution. Partial results wait for the remaining
batch; UI manual submission is supported but does not prove Hermes execution.

G0 used external Ollama0.33.3 and installed `gemma4:12b`, digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
That model supports native function tools; no universal model compatibility
claim is made. Stored node `generation.reasoning_effort=none` was an explicit
model-specific test choice to avoid exhausting the output budget on thinking.
It is not a universal default. Select your installed physical model explicitly;
no fallback weights or model download occurs.

`scripts/smoke_hermes.py` tests the production endpoint using the unchanged
Hermes AIAgent/OpenAI client and native read_file executor. Each invocation
creates dedicated JSON/SSE two-owner graphs and isolated HERMES_HOME fixture
directories. The JSON graph is literally synthesis, so the unchanged native
client selects cg/synthesis; POST refuses to overwrite an existing graph.
Use a dedicated new project. Startup suppresses installed dotenv discovery and verifies 19 exercised
source files against the pinned revision (18 G0 files plus plugins.py).
It registers one in-memory `PluginContext.register_hook(pre_tool_call)` guard
on the isolated native manager; the original executor's
`resolve_pre_tool_block` rejects any tool/path outside the dedicated fixtures.
It removes only its own guard afterward. No installed hook/configuration,
tool implementation, client transport, product executor or approval policy is
replaced. Native dispatch creates/closes original SDK clients per request.
An instance-local `_create_openai_client` delegate calls the unchanged original
factory with identical arguments and returns the same SDK object; it only adds
public HTTPX event hooks on those objects and the existing primary client.
Native transport/auth/cancellation/final close remain intact, and the delegate
is restored afterward. Original SDK event hooks observe only request bodies and diagnostic
headers; authorization headers are never captured. JSON replay compares the
original response, SSE replay compares cached chunks, and both require unchanged
durable counters/activation/mappings and exactly two real fixture reads.

```powershell
$env:CG_SMOKE_BASE_URL = 'http://127.0.0.1:8080'
$env:CG_SMOKE_MODEL = 'gemma4:12b' # Explicit installed model; select yours.
$env:CG_SMOKE_REASONING_EFFORT = 'none' # Only if appropriate for your model.
$env:CG_SMOKE_HERMES_ROOT = 'C:/Users/pkupr/AppData/Local/hermes/hermes-agent'
python scripts/dev.py smoke-hermes
```

This production command fails nonzero on missing prerequisites or assertions
and retains safe fixture/evidence files. Without extra flags its process restart
and compression gates remain OPEN. Use the existing pinned native Python directly
or the integrated runbook invocation; no dependency installation is implicit.
With `--restart-project <fresh-smoke-project> --docker-context desktop-linux
--compose-file D:/Sources/creep/compose.yaml`, the JSON SDK response hook restarts
the exact owned backend at a durable waiting-tools boundary before the first
native read. It verifies service/project/volume identity, changed process PID/
start time, unchanged run/opaque IDs/owners/results/counters, and completion on
those original IDs. It never restarts Ollama or an unrelated container.

`--compress --compression-url http://127.0.0.1:11434/v1` exercises the original
native ContextCompressor with the same physical model after a native result and
before sending its continuation. Inert closed fixture turns force one real
compression; latest opaque IDs/raw results must remain identical and the next
production continuation must succeed. The 512-token tail budget and optional
reasoning none are isolated test settings, not product defaults. Auxiliary
configuration is created only in the new HERMES_HOME; no installed config or
secret file is read or changed. Compression uses real external Ollama via the
original native client, not a fake summarizer or proxy tool executor. Original
agent sanitation runs afterward. Reported native compression/restart fields
are evidence only when their requested assertions actually execute and pass.
See verification.md for the executed results and open gates.
Hermes's iteration/time budget must accommodate exposed batches plus final
completion; the smoke uses24iterations and300second API timeout. Production
graphs must fit the independently configured server budgets and client limits.

For an explicitly authorized native fallback after a demonstrated container
route failure, `--native-backend-python backend/.venv/Scripts/python.exe
--native-ollama-url http://127.0.0.1:11434/v1 --base-url http://127.0.0.1:8000`
starts a dedicated production backend and replaces that exact owned process at
the first durable tool boundary. It is exclusive with `--restart-project`.
The new data/log/evidence directory is retained; cleanup stops only the process
handle created by the helper. Full runnable flags are in runbook.md. This native
mode does not prove Docker routing, Nginx or Windows/WSL2 Compose behavior.

## Historical G2 cycle3 F5 blocker

At that stage, independent G2-runtime review cycle3/3 found valid Draft3
schema-valued `extends`/`type` local references omitted by controller embedding
(F5). The public schema profile remained unchanged, and that automatic fix/review
budget was exhausted. The unformatted native tool fixtures above did not exercise
or resolve that defect; successful Hermes evidence could not establish full MVP
acceptance while it remained blocked. Subsequent user-authorized G2 attempt6
closed F1–F6; consult the current-state link above for current gates.
