# Cognitive Graph API and frozen component contracts

G1 defines these interfaces; production endpoint, scheduler, storage, provider
and UI implementations are delivered in G2–G6. A DTO or protocol test is not
evidence that an endpoint or live acceptance scenario works. Approved behavior
is in [the specification](../.codex/specs/cognitive-graph-mvp/spec.md);
[accepted decisions](../.codex/specs/cognitive-graph-mvp/decisions.md) resolve
the research and architecture policies.

Graph, runtime/storage, provider/bridge, composed API and UI implementations
have executable tests. Six browser scenarios have exercised the native
backend/SQLite with a mock upstream, including process restart and durable
tool IDs and same-ID graph reload. G4 passed independent cycle 2 (2/3), with
both prior findings closed. G3's medium-reasoning attempt5 independently
PASSed with zero findings. G1 independently PASSed its user-authorized
attempt4. Original quota failures remain recorded. Current-source Windows/WSL2
production Hermes/Ollama/Compose smokes passed, with application/dependency
identity verified. G5 PASS2/3 and G6 PASS1/3 close all mandatory MVP acceptance.
Exact live-source evidence
and gate status are maintained in
[delivery verification](verification.md), rather than inferred from unit tests.

## F6 correction and independent acceptance

G2 attempt4 historically found Medium F6: a valid Draft2020-12 root referencing
a Draft3 child with single-valued
`extends`. Original-good/original-bad validation and the public DTO accept it;
controller embedding causes pinned referencing crawling to raise AttributeError.
The actual scheduler/SQLite reproduction commits failed/upstream_error (502),
with two fake provider calls, zero success envelopes, and unchanged policy.
Original F5 is fixed: traversal now covers Draft3 `extends` single/list and
schema alternatives in `type`/`disallow`, with19 added regressions.

This is a compatibility defect in the accepted profile, not an unsupported
schema or invalid caller input. Prior findings F1–F5 are closed. Native final
validation without the affected controller rewrite is unaffected by this
particular defect. The authorized dependency correction pins repository-local
`referencing==0.37.0+cg.1`, derived from the prior locked0.37.0 wheel, changing
only mapping-valued Draft3 `extends` crawling to yield one schema. Array
traversal, the baseline engine, jsonschema4.26.0 and the accepted profile are
preserved. Isolated evidence passes all28 F6 regressions and259 runtime/storage
tests. The pinned Linux backend image builds with that exact wheel; a
network-disabled container under UID10001 verifies installed source parity,
original/emitted valid and invalid payloads, and invalid-control rejection.
This image proof does not establish live Hermes/Ollama or Windows/WSL2 behavior.
Independent G2 attempt6 PASS closes F1–F6 and this preservation gate.
Attempt5's quota termination remains consumed; budget6/6 permits no automatic
seventh review or fix wave. Separate source-matched production reconciliation
and G5/G6 independent reviews subsequently PASSed; mandatory gates are closed.
See the [authoritative review](../.codex/specs/cognitive-graph-mvp/review.md).

Python DTOs in `backend/app/contracts` are the source of truth.
`python scripts/dev.py generate-contracts` writes the versioned
`frontend/src/contracts/schema.json` and `generated.ts` from those DTOs.
`python scripts/dev.py check-contracts` regenerates in memory and fails on
either missing or changed output. TypeScript enforces shape/discriminators;
JSON Schema enforces patterns/ranges/required keys. Backend validators also
enforce cross-field and topology semantics; neither TS nor schema alone
proves a valid executable graph.

Smoke targets forward their helper's CLI options, for example
`python scripts/dev.py smoke-compose --validate-only` (also accepted as
`--validate` by the helper) or `make smoke-compose SMOKE_ARGS="--validate-only"`.
Validation checks Compose configuration without building or starting resources.
Hermes accepts `--model`, `--hermes-root` and its other documented helper flags:
`python scripts/dev.py smoke-hermes --model <installed-model> --hermes-root <path>`.
On Windows, Compose dispatches through WSL with forward-slash path conversion;
repeat `--file` accepts Windows absolute paths or WSL/relative paths.
`COMPOSE_FILE` uses the Windows semicolon-separated path list and is converted
for the WSL helper. Required Compose/smoke configuration and an optional
`CG_API_TOKEN` are forwarded through child-only WSLENV entries; values are not
printed, and the parent/global environment is unchanged. Path-conversion and
helper failures return nonzero, preserving a failing helper's exit code.

`npm --prefix frontend test` collects source unit tests only. Browser scenarios
remain under `frontend/e2e` and run separately with
`npm --prefix frontend run test:e2e`; listing those scenarios does not prove
backend-backed browser acceptance.

## Authorization, transport and errors

The default host API is `http://127.0.0.1:8000`, with same-origin UI forwarding
on `http://127.0.0.1:8080`. All `/api` and `/v1` routes, including SSE and tool
results, require `Authorization: Bearer <token>` when `CG_API_TOKEN` is set.
Health endpoints reveal only boolean readiness and need no token. The UI holds
its supplied token in memory and uses fetch-based SSE; tokens never belong in
URLs, graph files, run snapshots, event payloads or logs. Caller namespace is
domain-separated SHA256 of the configured token or `anonymous`. Rotating the
token changes namespace and prevents access to earlier token-bound runs.
`frontend/src/api/client.ts` implements authenticated fetch SSE with the bearer
header and persisted Last-Event-ID cursor, reconnecting only read subscriptions.
It never retries mutations or sends authentication in the event URL.

Maximum HTTP body: 2 MiB; canonical graph: 512 KiB; one UTF-8 tool result: 1 MiB.
These fixed boundaries are `MAX_REQUEST_BYTES`, `MAX_GRAPH_BYTES` and
`MAX_TOOL_RESULT_BYTES` in `contracts/config.py`. Oversize input fails before
admission/inference. IDs use `[A-Za-z0-9][A-Za-z0-9_-]{0,63}`; paths are formed
only by the repository. Unsupported semantic parameters fail with HTTP 400;
Pydantic validation is translated into the standard envelope, not FastAPI's
default 422 body. No implicit retries apply to management mutation/conflicts.

```json
{"error":{"message":"Invalid graph","type":"invalid_request_error","code":"graph_validation_failed"}}
```

The authoritative exhaustive code/status mapping is `errors.ERROR_STATUS`.
Error messages must be sanitized descriptions, never raw upstream exception
text or authorization headers.

| HTTP | Codes |
| --- | --- |
| 400 | `graph_validation_failed`, `invalid_parameter`, `unsupported_parameter`, `unsupported_tool_choice`, `budget_exceeded`, `context_overflow` |
| 401 | `unauthorized` |
| 404 | `unknown_model`, `graph_not_found`, `run_not_found` |
| 409 | `revision_conflict`, `continuation_conflict`, `unknown_tool_call`, `ambiguous_continuation`, `run_terminal`, `interrupted`, `cancelled` |
| 413 | `request_too_large` |
| 429 | `queue_full` |
| 500 | `storage_error` |
| 502 | `upstream_error` |
| 503 | `ollama_unavailable` |
| 504 | `llm_timeout`, `run_timeout`, `tool_wait_timeout` |

Statuses below 500 use `invalid_request_error` except 401
`authentication_error` and 429 `rate_limit_error`; all 500+ use `server_error`.
After an SSE response starts, send `event: error` with this same JSON envelope
as data and close. Do not manufacture `finish_reason=stop` or `[DONE]` for an
error. Only known-safe upstream failures before delivery allow at most two
retries; retries never repeat an exposed external tool effect.

## OpenAI-compatible surface

`GET /v1/models` returns `ModelsResponse`: `{"object":"list","data":[...]}`.
Each model contains `id`, `object="model"`, `created`, and `owned_by`.
Published graphs use `cg/<safe-id>` and physical models `ollama/<model-name>`;
drafts are hidden and unknown physical names are never substituted.

`POST /v1/chat/completions` takes `ChatCompletionRequest`. Accepted top-level
keys: `model`, `messages`, `tools`, `tool_choice`, `parallel_tool_calls`,
`stream`, `temperature`, `top_p`, `max_tokens`, `stop`, `response_format`,
`stream_options`, `n`. Only `n=1` is accepted. `messages` preserves the full
supplied list, text strings or text-part arrays, system/developer/user/
assistant/tool roles, optional names (including Hermes tool-result `name`),
assistant function calls and corresponding tool results. Images/audio, legacy function messages,
Responses parameters, `seed`, and public `reasoning_effort` are unsupported.

Functions preserve `name`, `description`, arbitrary JSON `parameters`, and
optional `strict`; arguments and results remain exact strings. Tool choice is
`none|auto|required` or `{"type":"function","function":{"name":"read_file"}}`.
Temperature is 0–2, top_p 0–1, max_tokens a positive integer, stop a string or
one to four strings. Response formats are `text`, `json_object`, and
`json_schema` with name/description/schema/strict. Stream options supports
only `include_usage` and requires stream=true. All DTO objects reject extras.

```json
{"model":"cg/synthesis","messages":[{"role":"system","content":"Use only the supplied information."},{"role":"user","content":"Compare both proposals."}],"stream":false,"n":1}
```

The response is `ChatCompletionResponse`, one choice with assistant content
or tool_calls, and `finish_reason=stop|tool_calls|length`. Completion IDs are
response IDs. `X-CG-Run-ID` is diagnostic and need not be echoed by Hermes.

`ChatCompletionResponse.from_upstream(payload: object) -> ChatCompletionResponse`
is the pure, strict JSON response boundary consumed by OllamaAdapter.complete.
The adapter parses the upstream body and invokes this factory, retaining the
physical model in the returned DTO. The HTTP response owner explicitly maps
that model to the requested direct/virtual namespace when rendering externally.
It maps factory ValidationError/ValueError to a sanitized HTTP502 upstream_error;
the factory does not perform I/O, retries, inference, or tool execution.

Before constructing the public/internal DTO, the factory validates and removes
only these explicitly known nonsemantic Ollama metadata fields:

- Root `system_fingerprint`: optional string or null.
- `usage.prompt_tokens_details`: optional null or strict object containing only
  optional `cached_tokens` (nonnegative integer or null).
- Nonstream `message.tool_calls[].index`: optional nonnegative integer or null;
  a provided integer must equal the call's array ordinal before removal.
- Nonstream assistant `message.reasoning`: optional strict string or null;
  validated private metadata excluded from DTO serialization and representation.
  Hidden reasoning is not returned, persisted or logged.

All other keys remain strict, including fields inside these metadata objects.
Malformed metadata, unknown semantic extras, invalid roles/call types, missing
required fields, or inconsistent tool_calls/finish_reason fail validation.
The factory preserves ID, physical model, created timestamp, object, ordered
choices/calls, content, call IDs/names/raw argument strings, finish_reason,
and aggregate prompt/completion/total usage exactly, without mutating its input.
Client request validation and public response model_validate remain strict;
normalization cannot be used to accept unsupported client parameters. This
factory covers nonstream completion JSON only. The separate
`providers.sse.validated_stream` boundary validates/excludes optional string/null
delta.reasoning metadata; stream call indices remain for fragmented SSE calls.
HTTP/SSE cleanup and composed route behavior have their own verification gates.
The provider checks the normalized nonstream completion's UTF-8 encodability
before returning it. Invalid escaped Unicode in content, names, IDs or raw tool
strings returns sanitized `upstream_error` (502), not `storage_error` (500).
SSE uses strict incremental UTF-8 decoding and only CR/LF/CRLF wire delimiters;
literal U+0085/U+2028/U+2029, fragmented multibyte characters and valid raw tool
arguments are preserved. Line/event buffers remain bounded. Malformed bytes
fail before headers with 502, or after headers with the standard error event
and no fabricated finish/DONE; permits are released on failure or closure.
These delivered G3 fixes have regression coverage and attributed Windows/
WSL2 proof. Independent G3 attempt5 PASSed; prior quota failures are retained.
No public profile or pin changed; older images do not prove current G2 bytes.

```json
{"id":"chatcmpl_opaque","object":"chat.completion","created":1791050000,"model":"cg/synthesis","choices":[{"index":0,"message":{"role":"assistant","content":"Final synthesis"},"finish_reason":"stop"}]}
```

Direct mode strips only the `ollama/` prefix, uses the same bounded admission
and provider pool as graphs, and preserves JSON/SSE/tools/error semantics.
Direct requests are ephemeral admission jobs, not persisted graph sessions.
Graph requests map latest user text to `chat` while separately retaining full
immutable history. Required additional named inputs fail before inference;
omitted optional inputs materialize explicit null. Original client instructions
are retained; predecessor outputs are data and activation tool histories are
private to their owner. Client temperature/top_p/max_tokens override only the
final LLM node. tool_choice=none disables every node's tools. A forced tool
requires exactly one tool-capable node, otherwise `unsupported_tool_choice`.
For each activation, `required` or a specific tool choice applies to its first
provider round; after all durable results for that owner round arrive, its
resumed provider request uses `auto`. This does not alter other activations'
first-round policy. Global `none` keeps tools disabled throughout the run.
parallel_tool_calls=false delivers at most one external call per response.
response_format constrains only the final external response; controllers have
their own strict schema generated by `graph.controller_schema(loop)`.
Before a graph success envelope is committed, `json_object` requires an object
and `json_schema` validates the native final value against the caller's schema,
including graphs with no LLM. Controller payloads and input→output values are
native JSON values; constrained native output is serialized as canonical JSON
after validation. Ordinary LLM serialized content is parsed for validation
without rewriting the delivered string. Incompatible no-LLM output fails with
sanitized `invalid_parameter` (400); invalid model/controller output fails
with `upstream_error` (502), never a success envelope.

The production validator uses the original supported declared schema dialect
(the installed default when absent), checks its local meta-schema, and resolves
only inline/local resources through `referencing.Registry(retrieve=deny_remote)`.
Unknown dialects, malformed schemas, failed constraints and unresolvable
external references fail at that same sanitized boundary. No schema fetch,
extra format checker or silent dialect substitution occurs. Independent
acceptance of the mixed-dialect F6 dependency correction above is G2 PASS6/6.
G1's cycle3 quota failure remains historical; attempt4 independently PASSed.

Internal stored `Generation.reasoning_effort` is an optional explicit
model-specific setting (`none|low|medium|high`), default absent. It is forwarded
only through `ProviderRequest`, after physical model translation. It does not
extend the public client profile or disable thinking universally. G0's actual
Gemma tool experiment used an explicit `none`; live production model validation
was subsequently accepted by G6. Each graph keeps one base_model; nodes cannot switch it.

Streaming uses standard `ChatCompletionChunk` JSON in SSE data, assistant role
delta, final content or indexed tool-call deltas, finish_reason, optional usage,
then `data: [DONE]`. Usage-only final chunks have empty choices. Comment
heartbeats are permitted; only final externally valid payload is emitted.
Intermediate/control text is buffered. A controller-final response is fully
validated before its payload is rendered through SSE. Initial-request
disconnection cancels best-effort unless a tool exposure has committed;
uncertain exposure preserves its envelope/IDs for replay. Disconnection of a
continuation waiter does not cancel work shared by durable duplicate claims.

## Graph management

| Method/path | Request | Response / behavior |
| --- | --- | --- |
| GET `/health/live` | none | `HealthResponse`; 200 while process is live |
| GET `/health/ready` | none | `HealthResponse`; 200 after storage/recovery readiness, otherwise 503; Ollama availability is reported separately |
| GET `/api/graphs` | none | `GraphListResponse` with IDs/names/draft and published revisions |
| POST `/api/graphs` | raw `Graph`, revision=1 | raw created Graph, 201; collision 409 |
| GET `/api/graphs/{id}` | safe ID | raw current draft Graph (also export representation) |
| PUT `/api/graphs/{id}` | `SaveGraphRequest={graph,expected_revision}` | raw saved Graph; graph.id equals path and graph.revision equals expected_revision; repository increments revision by one; lost update 409 |
| POST `/api/graphs/{id}/validate` | no body | `ValidationReport={valid,errors,warnings}` against current draft; issues include node_id/edge_id when relevant |
| POST `/api/graphs/{id}/publish` | `PublishGraphRequest={expected_revision}` | `PublishGraphResponse={graph_id,published_revision,graph_hash}`; topology validation and atomic immutable publication; mismatch 409 |

Import is create with an explicit new safe ID, or save with expected revision
when replacing an existing draft. Export is graph-only JSON; no environment
token or history. Forward edges form a DAG. Feedback requires loop_id and the
initial_value key, including explicit null. Loops are disjoint, have distinct
configured continue/exit values, one terminal controller and controller-only
outgoing scope edges. Full topology validation/compilation is G2/G4 work.
Coordinates are purely visual. One terminal output passes through one input.
Graph request parsing checks the entire decoded JSON representation for valid
UTF-8 before DTO construction, hashing or storage. Escaped unpaired surrogates
return sanitized `invalid_parameter` (400); POST creates no file and rejected
PUT preserves existing file bytes. Valid surrogate pairs and Unicode roundtrip.
The UI tracks an authoritative load boundary, so reloading the same graph ID
refreshes inspector generation/edge/scope state while preserving local edits
until an explicit load. Six backend-backed browser scenarios and 98 graph
cases pass; G4's independent cycle 2 is PASS at 2/3, with no current findings.

Files under `CG_DATA_DIR/graphs/<id>.json` are authoritative drafts;
`published/<id>/<revision>.json` are immutable publications. Highest valid
published revision is current publication; no competing database pointer.
Writes use same-directory temporary file, flush/fsync and atomic replacement,
plus directory fsync where supported. save/publish/load_snapshot use the same
per-graph lock. Corrupt publications fail explicitly, never silently roll back
to an older published revision. A new run captures canonical full graph JSON
and SHA256 before scheduling. Future edits/publications cannot change it.

## Runs, history and continuation

| Method/path | Request | Response / behavior |
| --- | --- | --- |
| POST `/api/runs` | `StartRunRequest={graph_id,revision,inputs,messages?,tools?}` | `StartRunResponse={run_id,status}`, 202; validate named inputs before admission |
| GET `/api/runs` | optional graph_id/status, limit=20 (1–100), offset=0 (>=0) | `RunListResponse={runs,total,limit,offset}` in created_at descending/run_id tie order |
| GET `/api/runs/{id}` | run ID | `RunDetailResponse={run,snapshot,activations,pending_tools,output,error}`; authorized namespace only |
| GET `/api/runs/{id}/events` | `Last-Event-ID` nonnegative integer, default 0 | committed `RunEvent` SSE with `id: <event_id>`, `event: <type>`, JSON data; event sequence is per-run monotonic |
| POST `/api/runs/{id}/cancel` | no body | `StartRunResponse={run_id,status}`; idempotent terminal-state preservation |
| POST `/api/runs/{id}/tool-results` | `ToolResultsRequest={results:[{tool_call_id,content}]}` | `ToolResultsResponse={run_id,status,accepted_ids,missing_ids}`; partial acknowledgment; repeated identical content harmless, changed/unknown/late IDs conflict |

UI test runs load current draft or requested retained immutable publication.
An overwritten unpublished revision returns 409; no silent revision
substitution. History reflects snapshot revision/hash, queue/active duration,
executions/attempts/tool batches and activation/node/loop iteration states.
Statuses are queued/running/waiting_tools/completed/failed/cancelled/interrupted;
node states are pending/ready/running/waiting_tools/completed/failed/cancelled.

```json
{"graph_id":"synthesis","revision":1,"inputs":{"chat":"Compare both proposals."},"messages":[],"tools":[]}
```

Hermes continuation is classified from the latest relevant assistant/tool
segment using opaque `cg_` UUID IDs proven in G0. Closed IDs preceding a
completed answer/new user turn do not resume history. Physical model requests
whose latest IDs have no graph mappings return `NewRunRoute` and use the
ephemeral direct path with their full original tool history. IDs that do map
to graph state require the matching `cg/<graph-id>` model; a mismatch is 409.
Classification uses the latest segment only. Latest unknown graph IDs,
mixed run/batch/namespace/model, or a new user turn combined with pending
results return explicit 409. Original history remains immutable even if the
incoming Hermes continuation was compressed.
`tools.bridge.canonical_request_hash(request: ChatCompletionRequest) -> str`
normalizes semantic defaults, sorts object keys, preserves array order and
raw arguments/results, and includes model, all semantic policy and stream mode.
A separate canonical JSON argument
hash validates Hermes-normalized echoed arguments without rewriting originals.

One external batch is open at a time. Unknown/side-effecting calls serialize
conservatively even when parallel_tool_calls permits more; no name heuristics
declare tools safe. At handoff, stop new dispatch and drain started sibling
inference. Atomically commit the quiescent frontier, batch, all mappings,
response envelope and event before any response bytes. Each mapping identifies
activation/provider round/call ordinal; internal IDs alone are not unique.
Only the owner receives its result; its next provider round waits for every
call in the previous provider response, even if serialized across batches.

Partial management results return accepted/missing IDs. Partial Chat
Completions results persist once and wait for outstanding batch results to
arrive via another request or management call until the fixed original tool
TTL. They never fake stop or reissue delivered tools. Exact repeated
continuation joins a durable pending claim or replays its saved envelope with
the same completion ID/tool IDs and no new node/tool/inference. Conflicting
results fail 409. Replay is continuation idempotency, not an inference cache.
After cancellation/timeout/interruption, late results fail explicitly.
Focused HTTP/SQLite tests distinguish a pending partial continuation reaching
its original fixed TTL (`tool_wait_timeout`, 504) from a new submission after
failed state is already persisted (`run_terminal`, 409). Neither path extends
the TTL or adds provider/tool effects. The timing-test seam was corrected with
deterministic before/after-terminal barriers, preserving both exact assertions
and leaving production chat unchanged. Terminal API/integration evidence is
49 passing cases; the latest provider-owner full backend run passes 587 cases.
These checks close the earlier timing-test discrepancy, not the separate G2
schema blocker or required live gates.

## Frozen component signatures and transaction ownership

`contracts/interfaces.py` contains exact async Protocols and frozen records.
It does not implement production scheduling/storage/network behavior.

| Boundary | Signatures consumed by later owners |
| --- | --- |
| GraphRepository | `list_graphs()->tuple[GraphSummary,...]`, `list_published()->tuple[GraphSnapshot,...]`, `create(Graph)->Graph`, `get(graph_id)->Graph`, `save(Graph,expected_revision)->Graph`, `publish(graph_id,expected_revision)->GraphSnapshot`, `load_snapshot(graph_id,revision=None,published_only=False)->GraphSnapshot` |
| Validator | synchronous `validate(Graph)->ValidationReport`, `compile(GraphSnapshot)->CompiledGraph`, `prepare_inputs(Graph,inputs_json)->str` |
| RunRepository | `initialize/close`, `create_run(RunSubmission,run_id,now)->RunRecord`, `get_run(run_id,namespace)`, `list_runs(namespace,graph_id,status,limit,offset)->RunPage`, `load_checkpoint(run_id,namespace)->RunCheckpoint`, `save_checkpoint(checkpoint,expected_version)->RunRecord`, `claim_activation(key,attempt_id,now)->ActivationRecord|None`, `checkpoint_batch(ToolCheckpoint,expected_version)->RunRecord`, `complete_run(checkpoint,envelope,expected_version)->RunRecord`, `lookup_tools(external_ids)->tuple[PendingTool,...]`, `accept_results(ContinuationRoute,request_hash,now)->ContinuationAcceptance`, `get_claim(claim_id)->ReplayClaim`, `terminalize(run_id,TerminalFailureStatus,error,now)->RunRecord`, `cancel_if_unexposed(run_id,namespace,now)->RunRecord`, `recover(now)->tuple[RunRecord,...]`, `read_events(run_id,namespace,after_event_id,limit=1000)`, `cleanup_history(before)->int` |
| GraphRuntime | `submit(RunSubmission)->RunRecord`, `resume(ContinuationAcceptance)`, `await_response(run_id,namespace,after_response_sequence=0)->ResponseEnvelope`, `cancel(run_id,namespace)->RunRecord`, `detach_initial(run_id,namespace)->RunRecord`, `recover()`, `shutdown()` |
| OllamaAdapter | `complete(ProviderRequest)->ChatCompletionResponse`, `stream(ProviderRequest)->AsyncGenerator[bytes,None]`, `models()->tuple[str,...]`, `health()->bool`, `close()` |
| ToolBridge | synchronous `map_calls(activation,response)->tuple[PendingTool,...]`, `classify(ChatCompletionRequest,namespace)->NewRunRoute|ContinuationRoute`, `accept(route,request_hash)->ContinuationAcceptance`, `prepare_batch(run_id,namespace)->ResponseEnvelope`, `await_response(claim_id)->ResponseEnvelope` |
| EventBus | `notify(run_id)`, `read_after(run_id,namespace,after_event_id)->tuple[RunEvent,...]`, `subscribe(...)->AsyncIterator[RunEvent]` |
| AdmissionController | `acquire(job_id)->AdmissionLease`, `restore(active_job_ids,queued_job_ids)`; lease `wait/release` |
| Clock | synchronous `now()->timezone-aware datetime`, `monotonic()->float`, async `sleep(seconds)`; fake clocks are injected in tests |

All listed methods are async except Validator, Clock.now/monotonic,
ToolBridge.map_calls, provider stream and event subscribe. Stream/subscribe
return asynchronous iterators directly. Protocol calls raise CGError
for contract failures. Immutable persistence records hold nested JSON as
strings, not mutable live dictionaries. `GraphSnapshot.graph()` returns a
detached validated graph; hash/identity validation runs on construction.

`CompiledGraph` holds snapshot, forward order, lexical ordered ports, loop
plans, output node and optional final LLM identity. An input→output graph is
valid without any LLM; final_llm_node_id is None, and generation overrides have
no provider call to affect. `ActivationKey` is
`(run_id,scope_key,iteration,node_id)`; root scope is empty string, iteration=0,
and SQLite columns are NOT NULL. `PortValue` includes target activation/port,
source identity/iteration and exact serialized value; absence differs from
present null. `LoopState` holds separate iteration, latched immutable external
inputs and next-feedback tokens. Controllers are strict JSON; only configured
exit releases scope data. Seeded iteration zero and subsequent transitions
retain all-port barriers; disjoint loops advance independently.

`RunRecord` holds immutable snapshot/context/inputs/policy, state_version,
timestamps, elapsed budgets, attempts/executions/tool_rounds and output/error.
`RunCheckpoint` contains every activation, loop, mapping, batch, response
envelope and event JSON.
`ActivationRecord.finish_reason` preserves the actual provider response's
`stop`, `tool_calls` or `length` independently of payload, history and usage,
including across checkpoint reload. It defaults to None for input/output nodes,
pending activations and records written before this field existed. Runtime
stores it when a provider response arrives; recovery must retain `length` when
constructing the final response rather than replacing it with `stop`.
`ToolCheckpoint` wraps that quiescent checkpoint and its new ToolBatch.
`PendingTool` preserves raw arguments, raw SHA256 and separate canonical JSON
hash, provider round/call ordinal, result and result hash. `ToolBatch` has fixed
UTC prepared/expires times and a frozen ResponseEnvelope. All persistence
datetimes must be timezone-aware. ResponseEnvelope validates its stored
completion JSON and returns detached DTOs. `ReplayClaim` stores durable
namespace/run/batch/request_hash, pending/completed/terminal state, envelope
or error, plus after_response_sequence identifying its source batch boundary.
`ContinuationAcceptance` distinguishes replay/joined/partial/ready
and contains accepted/missing IDs and the owning claim.

Every RunRepository mutation uses one short serialized SQLite transaction;
no transaction spans inference, network/SSE wait or filesystem sync. Enable
WAL, foreign keys, busy timeout and FULL synchronization. Verify row counts
and optimistic version predicates. Required durable uniqueness: activation
key; external tool ID; activation/provider_round/call_ordinal; batch sequence;
one open batch per run; namespace/run/batch/request_hash claim; run/event_id.
save_checkpoint atomically validates the nonterminal run/version, saves the
frontier and events, and increments version. Every mutating transition,
including claims/results/attempts, advances state_version. The runtime is the
single in-process frontier reducer per run; parallel provider tasks return
their outcomes to it, not independent full-checkpoint writers. On CAS conflict,
reload the authoritative checkpoint and recompute the still-applicable
activation/attempt transition. Never blindly retry a stale checkpoint or
overwrite accepted tools, immutable snapshot/context/policy, sealed responses,
events or terminal state. A stale attempt must not route output. Bridge result
acceptance remains a short DB transaction and may race this reducer; CAS/rebase
must preserve both transitions. claim_activation checks ready
state/run/budget atomically, increments new LLM-execution and upstream-attempt
counts, sets the attempt marker and emits activation.running; a tool resume
increments attempts without another activation execution. checkpoint_batch
additionally verifies no uncertain running attempts, commits mappings/envelope
and increments exposed-batch budget once. The same transaction appends the
response and seals all pending continuation claims waiting for that new
response boundary. complete_run likewise saves completed frontier/final
envelope/events and seals all such claims in one transaction. There is no
separate post-commit complete_claim mutation or unreconstructable cache window.
ResponseEnvelope.response_sequence starts at one; every newly exposed tool
batch uses that sequence, and final completion uses the next sequence.
Batch.sequence equals its envelope sequence. Claims point to their source
batch's sequence; all partial/full/management claims for that source resolve
to the first subsequent committed response, never an earlier batch or a
later skipped response. Runtime await_response returns the first stored
sequence strictly greater than its cursor (initial cursor zero); ToolBridge
await_response reads the durable claim association. Every returned response
was committed before notification, so restart can recover association exactly.

accept_results checks namespace/model/run/batch, existing result conflicts and
the exact durable claim first. A completed matching claim replays even after
successful graph completion. New/changed submissions to completed runs, and
submissions after cancellation/failure/interruption/expiry, fail explicitly;
they never create a new run. A matching pending claim joins before scheduling.
Otherwise check terminal/deadline guards, create the unique claim, commit
immutable results, close a fully accepted batch and append events atomically.
No partial/replay path extends expires_at or increments tools budget.
A new non-exact request hash for an already-closed older batch returns
continuation_conflict; it never binds to the latest response or schedules old
work. Existing exact claims retain their first subsequent saved response.
terminalize preserves the first terminal reason and prohibits later mutation;
it accepts only failed/cancelled/interrupted states, seals pending claims with
that terminal error and closes open batches atomically. Completed success
requires complete_run's envelope transaction. Terminal history cannot be
overwritten by late task completion. Explicit cancel always terminalizes;
detach_initial instead uses cancel_if_unexposed, sharing the transactional
boundary with checkpoint_batch. If exposure won, preserve it; if detachment
won, batch exposure fails its nonterminal/version guard. No read-then-cancel
race may erase committed potentially delivered tools.

Recovery before readiness returns queued and safe unexpired waiting runs; uncertain persisted
active attempts become interrupted without automatic inference. Expired waits
fail with tool_wait_timeout, including process downtime. Events commit before
notification; notification only wakes database catch-up. No cursor/transaction
is held during SSE waits. Retention deletes only terminal run history older
than the configured window, preserving graphs/publications/live mappings.
Graceful runtime shutdown stops dispatch, preserves safe waiting checkpoints,
original IDs and fixed deadlines, marks uncertain active attempts interrupted,
and retains never-started queued runs for recovery. It does not cancel all
waiting runs as though the user had pressed Cancel. admission.restore includes
safe waiting runs as active leases, and queued runs as reserved queue leases.

AdmissionController bounds shared graph/direct jobs by CG_MAX_ACTIVE_RUNS and
CG_MAX_QUEUED_RUNS. acquire atomically reserves an active or queue position
before returning and fails queue_full when both capacities are full;
an available lease admits immediately, otherwise wait blocks until admitted.
Lease.wait creates no extra reservation or unbounded waiter job; job IDs are
unique, and duplicate acquire joins/rejects its existing reservation.
Release is idempotent and removes queued cancellation too. waiting_tools retains
its active lease while releasing inference capacity; direct jobs release on
full exchange/disconnect. Provider semaphore capacity CG_MAX_PARALLEL_LLM is
shared across all graph/direct calls and held through full JSON/SSE consumption.
The closeable stream generator releases it in finally; downstream consumers
must await generator.aclose() on disconnect/error. Receiving upstream headers
alone does not release a permit. No DB transaction or provider permit is held
while waiting for external tool results.
Active wall time includes computing/draining/permit wait, excludes queued and
quiescent external wait; concurrent nodes do not multiply it. Every newly
exposed external batch counts one tool round; replay/partial results never
increment or extend the fixed UTC tool TTL. These policies are contracts to
verify in G2/G3/G6, not runtime PASS claims from G1.

## Concrete implementation handoff and injection

The implementations below consume G1 types. `app.main.create_app` composes
shared services and injects them into routes. Its optional Settings and
keyword-only provider/repository/graphs/validator/clock/admission/runtime/bridge/
events arguments support actual HTTP integration tests; omitted components use
the implementations below. Construction defers SQLite opening to lifespan.
Startup initializes storage, recovers runtime/admission, then sets readiness
and starts retention cleanup. Shutdown stops cleanup, joins runtime, then closes
provider and repository. Injected components participate in this lifecycle;
the provider still closes only an HTTP client it owns. `/health/ready` checks
storage independently from upstream availability. Independent integration
review and full live acceptance remain open.

| Concrete class / module | Construction and ownership |
| --- | --- |
| `graphs.validator.GraphValidator` | No I/O; supplies Validator; lexical ports, graph topology and prepared input JSON |
| `graphs.repository.FileGraphRepository` | `(data_dir: Path, validator: Validator)`; sole graph/publication file owner |
| `api.graphs.create_graph_router` | `(repository: GraphRepository, validator: Validator, authorize: Callable[..., object]) -> APIRouter`; mounts `/api/graphs` with mandatory injected authorization dependency on every route; composition owns token policy |
| `api.models.create_models_router` | `(graphs: GraphRepository, provider: OllamaAdapter, authorize: Callable) -> APIRouter`; mounts published virtual and physical `/v1/models` |
| `api.runs.create_runs_router` | `(settings, graphs, validator, repository, runtime, bridge, events, clock, authorize) -> APIRouter`; mounts authenticated management/history/events `/api/runs` |
| `api.chat.create_chat_router` | `(settings, graphs, validator, provider, runtime, bridge, admission, authorize) -> APIRouter`; mounts authenticated graph/direct `/v1/chat/completions` |
| `storage.repository.SQLiteRunRepository` | `(database_path: Path)`; sole serialized SQLite connection/transaction owner |
| `storage.events.DurableEventBus` | `(repository: RunRepository)`; database catch-up authority plus lightweight wakeups |
| `runtime.admission.BoundedAdmissionController` | `(max_active: int, max_queued: int)`; one instance shared by graph and direct jobs |
| `runtime.clock.SystemClock` | Supplies Clock; injectable fake clock for deterministic timeout/accounting tests |
| `providers.ollama.HttpOllamaAdapter` | `(settings: Settings, client: httpx.AsyncClient|None=None, limiter: asyncio.Semaphore|None=None)`; one shared instance/permit pool, close only an owned HTTP client; complete consumes `ChatCompletionResponse.from_upstream` before namespace translation |
| `tools.bridge.DurableToolBridge` | `(settings: Settings, repository: RunRepository, events: EventBus, clock: Clock)`; no runtime/provider/executor dependency |
| `tools.bridge.canonical_request_hash` | `(request: ChatCompletionRequest) -> str`; semantic defaults/stream included, raw argument/result strings preserved |
| `runtime.engine.AsyncGraphRuntime` | `(settings: Settings, repository: RunRepository, validator: Validator, provider: OllamaAdapter, bridge: ToolBridge, events: EventBus, admission: AdmissionController, clock: Clock)`; owns per-run reducers and strongly referenced background tasks |

The composition root constructs single shared instances, initializes storage,
recovers runtime/admission before readiness and injects these objects into
route handlers. Runtime receives frozen RunSubmission from the API; it owns
all scheduling, prompt construction, loop transitions and background lifetime.
Recovery recompiles each preserved RunRecord.snapshot using the injected
Validator; it never reloads current draft/publication or changes saved context.
Provider outcomes are buffered; ToolBridge.map_calls creates opaque external
IDs/raw+normalized hashes without I/O. Runtime preserves the original provider
assistant envelope in only the owning activation's messages and commits all
unexposed mappings/frontier. After quiescing sibling inference, it calls
ToolBridge.prepare_batch; bridge selects an allowed external batch, constructs
the envelope and invokes repository.checkpoint_batch atomically. The bridge
does not execute tools or run a scheduler.

Chat/API result routing calls bridge.classify/accept, then runtime.resume only
for a ready acceptance. Partial requests await the claim; management submits
through the same validated accept path, acknowledges accepted/missing IDs and
triggers resume only when ready. Runtime claims prevent a duplicate ready
notification from executing the activation twice. On the next response,
repository.checkpoint_batch or complete_run owns atomic claim finalization;
bridge await_response merely reads/waits for that saved result. Runtime may
then continue surviving other HTTP request lifetimes. Explicit cancellation
and initial detachment invoke their distinct guarded runtime methods.
