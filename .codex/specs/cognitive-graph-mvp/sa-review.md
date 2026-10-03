# Cognitive Graph MVP — provisional architecture advisory

Owner: `sa_g0` (sa-agent). Date: 2026-10-03, Europe/Kiev. Scope: G0 advice for G1.

This report proposes implementation contracts; it does not freeze them, amend
requirements, close G0, or supply an independent review verdict. The lead owns
accepted decisions in [decisions.md](decisions.md). RD1 and RD2 remain the
authorities for their experiments. No production files were changed.

Sources: entire [root specification](../../../Cognitive_Graph_MVP_Codex_Team.md),
[AGENTS.md](../../../AGENTS.md), [requirements.md](requirements.md),
[spec.md](spec.md), [design.md](design.md), [tasks.md](tasks.md),
[decisions.md](decisions.md), and
[environment research](../../../docs/research/environment.md). Proposed names
below are a handoff to the single G1 contract owner, not existing modules.

## Findings in implementation priority order

| Priority | Finding / consequence | Recommendation / owner | Acceptance evidence required |
| --- | --- | --- | --- |
| P0 | A returned tool checkpoint can coexist with an uncertain sibling inference. Restart then cannot safely promise continuation of that run. | Before exposing a batch, pause new dispatch and let already-started calls settle under their deadlines. Persist the resulting quiescent frontier. G1 contract; G2 runtime; G3 bridge. | A08/A10: crash after batch commit and before/after HTTP delivery; old IDs finish without rerunning siblings. |
| P0 | In-memory session matching, NULL-containing unique keys, or result insertion separate from replay claims permits duplicated activation/continuation. | Durable activation identities, a single pending external batch, transactional request claims and immutable accepted results. G1/G2/G3. | A09/A10: simultaneous duplicate requests, identical independent questions, conflicting results, process restart. |
| P0 | A global iteration counter or early scope exit breaks disjoint loops and fan-in. | Per-loop iteration, per-activation ports, immutable external inputs, next-iteration feedback, controller-stop-only exit. G1/G2. | A03–A06: diamond plus two independently iterating loops feeding synthesis. |
| P0 | Releasing the inference permit at response headers or giving each run its own semaphore violates the global limit. | One provider-owned permit spans the complete upstream exchange, including direct mode. G1/G3. | A16: overlapping direct and graph requests, stream cancellation, failures and permit accounting. |
| P1 | Atomic file replacement and a SQLite transaction are not one cross-store transaction. | Keep graph/publication authority in files; copy immutable bytes/hash into the run transaction. Avoid a competing SQLite published pointer. G1/graph repository owner. | A13: fault injection around draft replacement, publication and run insertion. |
| P1 | Tool-wait time counted as active, TTL reset by replay, or uncapped waiting runs defeats budgets. | Separate accounting and fixed batch deadlines; count admitted waiting runs toward active capacity. G1/G2. | A14/A16: fake-clock boundaries, partial results, restarts, full queue. |
| P1 | Host reachability does not prove container reachability. | Preserve the specified default provisionally; probe from the actual owned backend container in G5/G6. DevOps. | A15: Windows and WSL2 launch with actual application-container Ollama access. |

P0/P1 are implementation priorities, not fabricated defect severities in code
that does not yet exist. Each recommendation below is reversible before G1
freeze; afterward changes require shared-contract review and data migration
where persistent keys or state meanings change.

## Scheduler and loop contract

Proposed compiled plan types owned by G1:

```text
ActivationKey(run_id, scope_key, iteration, node_id)
PortValue(target_activation, target_port, source_node_id, source_iteration, value)
LoopPlan(loop_id, members, controller, inbound_edges, feedback_edges, exit_edges)
CompiledGraph(nodes, forward_order, loops, expected_ports_by_node, output_node_id)
```

`scope_key=""` and `iteration=0` identify nodes outside a loop. Real loop IDs
must be nonempty. These fields are NOT NULL in SQLite. A nullable `loop_id`
in a composite unique constraint is an avoidable duplicate-root risk.

1. Compile each node's ordered ports once, using a documented lexical port
   order independent of completion order. A port is ready by presence, even
   when its value is explicit null. Reject duplicate providers. Validate
   required run inputs before admission or upstream calls; materialize omitted
   optional inputs as null. Claim a ready activation atomically once.
2. Validate the forward DAG separately from SCCs of the full graph, including
   self-loops. Each cyclic SCC must be wholly contained in exactly one declared
   scope; a scope may include forward-only members, so do not assume scope
   membership equals one SCC. Reject nested/overlapping scopes and feedback
   edges with missing scope, endpoints outside that scope, or absent seed keys.
3. Validate every member reaches the controller along forward edges and is
   reachable from the scope's entries. The controller must be terminal within
   the scope's forward graph. Contract scopes into supernodes and require the
   resulting inter-scope graph to remain acyclic. Any scope-to-outside edge
   must originate at its controller. This catches cross-scope deadlocks and
   bypasses without forbidding multiple disjoint loops.
4. Materialize iteration zero feedback tokens from `initial_value`, including
   null. Latch each external edge value once into the loop instance; make it
   available to the corresponding port in every iteration. Ports whose
   external sources have not completed remain absent, not null. External
   values cannot be overwritten by later loop iterations.
5. Within an iteration use ordinary all-port readiness; a controller cannot
   run before its required ancestors. Store each feedback source's payload
   for the next iteration, but do not activate that iteration until the
   controller produces valid control JSON. Feedback need not originate only
   at the controller; restricting that would narrow the stated graph format.
6. On `continue`, atomically complete the controller, increment only its
   loop's iteration, initialize new activations with feedback and latched
   external inputs, and persist events. Emit no scope-external token. On
   `stop`, complete the scope and emit only the controller payload to its
   outside successors. Keep prior activations immutable for history.
7. Validate decision against distinct configured `continue_value` and
   `exit_value`; the example values are `continue`/`stop`. Missing/invalid
   control fails the run. Controller tool calls complete before this check.
   Never parse prose or execute expressions. The terminal output node is a
   one-input pass-through, not an extra synthesis request.

Count a node execution when a new LLM activation is claimed, not when a tool
result resumes that activation; count upstream attempts separately. Tool rounds
need a distinct, frozen meaning (see unresolved choices). Test that budget
checks occur before starting work and never convert exhaustion into success.
Failure of any required activation terminalizes the run and cancels peers.

Required adversarial tests: the A03 delayed diamond; absent versus null ports;
two loops stopping at different iterations then joining; multiple feedback
ports from different members; a seed missing versus explicit null; scope output
bypass; a cross-scope cycle; stale iteration tokens; a controller returning
`length` with incomplete JSON. These are refinements of A03–A06, not new features.

## Durable continuation and exposure boundary

Generate one opaque random external ID per tool call; never encode/rely on the
question, completion ID, node name or provider's internal ID. Use a stable
namespace derived from the configured token without storing the token (for
example domain-separated SHA-256), otherwise the single literal anonymous
namespace. Token rotation intentionally changes namespace and may prevent
resuming prior token-bound runs; document this rather than bypassing it.

Keep original run context separate from activation-owned tool history. Only
that activation receives its provider assistant call and tool result pairs.
The incoming compressed continuation does not replace the original snapshot or
silently remove client system constraints. Other nodes receive final payloads,
never another activation's live calls as their own.

Proposed ToolBridge routing result:

```text
classify(request, namespace) -> NewRun | Continuation(run_id, batch_id, results) | Conflict
accept(continuation, canonical_request_hash) -> Replay | JoinedClaim | AcceptedPartial | Ready
prepare_batch(run_id) -> PersistedResponseEnvelope
await_response(claim_id) -> PersistedResponseEnvelope | TerminalError
```

RD1 must determine the exact latest assistant/tool segment parser and permitted
ID normalization before G1 freezes `classify`. Do not scan every historical
tool message. Validate relevant IDs against one namespace, run, graph model and
pending batch. Unknown latest IDs, mixed runs/batches, changed accepted results,
or new user content mixed with a pending continuation produce explicit errors.
Closed historical segments before a new turn do not resume old work. Exact
terminal-continuation replay remains recognizable after the batch is closed;
otherwise a retry of the final response accidentally starts a new run.

The run-level bridge lock serializes delivery claims, not all node computation.
Stop new dispatch when preparing a tool handoff; drain already-started provider
calls under their existing deadlines. If any required call fails, fail the run
instead of exposing tools. When no inference remains active, persist the entire
frontier, external mappings, pending batch, response envelope and event in one
transaction. Only then send response bytes. A crash before commit exposes no
calls; a crash after commit reuses the same envelope and IDs. HTTP cannot prove
whether Hermes received bytes, so record `exposed` as potentially delivered.

Serialize unknown/side-effecting tools by default, even with
`parallel_tool_calls=true`. Tools schemas alone do not establish safe
independence. Do not add heuristics such as “name starts with read”. G1 may keep
a pure internal batching-policy seam; enabling a trusted read-only policy needs
separate evidence. `parallel_tool_calls=false` always caps exposure at one call.
An activation that originally emitted several calls resumes its provider only
after all calls from that provider response have results, even if several
external batches were needed. Use call ordinal plus activation/provider round
to isolate repeated internal IDs across owners and rounds.

Partial results are committed once; unchanged repeats are harmless, changed
contents conflict. Close a batch only after every exposed ID has a result.
Never expose already-delivered calls to solicit missing results. Management
tool-result submission may acknowledge accepted/missing IDs. The Chat
Completions request may remain pending until missing results or TTL; it must
not manufacture a successful completion or resend the outstanding calls. Hold
no database transaction or inference permit during that wait. RD1/G1 must
document the actual wire behavior and separate submission needed for remaining
results. A request retry joins an existing durable claim instead of launching
another scheduler. Cancellation and late results are checked before mutation.

Canonical request hashing must include model, normalized message representation,
tools and semantic generation/tool policy, plus stream mode if response wire
replay differs. Sort object keys, preserve array order and string contents;
never normalize tool argument/result strings by parsing and rewriting them.
The cache key includes namespace, run, batch and hash; it is continuation
idempotency, not an inference-response cache. Persist the response's completion
ID and semantic contents; deterministic SSE rendering may reuse this envelope.

This prevents the proxy from initiating duplicate tool calls. It cannot make a
Hermes executor transactional or guarantee that Hermes itself never repeats a
tool after uncertain delivery. That residual boundary belongs in compatibility
documentation, with RD1 traces proving the supported behavior.

## Minimal storage invariants and module boundaries

G1 owns DTOs, protocols and JSON Schema/TypeScript generation. Suggested protocol
placement: `contracts/runtime.py`, `contracts/storage.py`, `contracts/tools.py`
under `backend/app/`, alongside the graph/API models. Names are proposals for
the lead's exact-file handoffs; no implementation is authorized by this report.

| Owner / interface | Responsibilities and narrow return types |
| --- | --- |
| GraphRepository / `load_snapshot(graph_id, revision, published_only)` | Validated immutable graph plus canonical bytes/hash. `save(expected_revision)` and `publish(expected_revision)` share one per-graph lock. |
| Validator / `compile(graph) -> CompiledGraph` | Structural errors carry node/edge identity; no I/O or execution. |
| GraphRuntime / `submit`, `resume`, `cancel`, `recover` | Own background tasks, readiness, loop transitions and admission. HTTP handlers await outcomes but do not own scheduler lifetime. |
| RunRepository / `create_run`, `claim_activation`, `complete_activation`, `checkpoint_batch`, `accept_results`, `terminalize` | Each method is one explicit state transition with event persistence and optimistic state/version predicates. No provider calls inside methods. |
| OllamaAdapter / `complete`, `stream`, `models`, `health` | One shared inference permit, call timeout, validated error mapping; no graph/SQLite logic or tool execution. |
| ToolBridge / methods above | Route, map, batch, hash, restore tool histories and expose envelopes; no Hermes executor. |
| EventBus / `read_after(run_id, event_id)`, `subscribe` | Database is authority. Commit before notification; notify only wakes a catch-up reader. No DB cursor/transaction held across SSE waits. |

Suggested minimum tables (all state-changing access stays behind RunRepository):

- `runs`: random primary key; namespace; graph ID/revision; immutable snapshot
  JSON/hash, original context and policy; status; state version; budgets;
  active elapsed time; timestamps; terminal error; next event sequence.
- `activations`: primary key; run FK; NOT NULL scope key, iteration and node ID;
  `UNIQUE(run_id, scope_key, iteration, node_id)`; status; provider round;
  checkpoint messages; payload/control; current attempt marker.
- `activation_inputs`: activation FK plus target port as primary key;
  source identity/iteration and JSON value. Insert once, reject a differing
  duplicate. `loop_instances` stores iteration/status and latched external
  inputs; equivalent structured checkpoint storage is acceptable if updates
  retain the same transactional invariants.
- `tool_batches`: primary key, run FK, sequence, status, fixed expiry and
  response envelope; unique `(run_id, sequence)` and a partial unique index
  allowing at most one open batch per run.
- `pending_tools`: globally unique external ID; activation/run FK; batch FK
  when exposed; provider round/call ordinal; original internal ID, exact
  arguments/hash, result/hash and state. Unique
  `(activation_id, provider_round, call_ordinal)`. Do not key by internal ID alone.
- `response_cache`: unique `(namespace, run_id, batch_id, request_hash)`;
  claim state and saved response/checkpoint. A durable claim without a response
  after crash is reconciled with activation attempt markers, never blindly
  re-executed.
- `events`: primary key `(run_id, event_id)`; event type/payload/timestamp.
  Allocate sequence and insert in the same state-change transaction. SSE can
  replay committed events after reconnect using `Last-Event-ID`.

Use one serialized SQLite connection on a dedicated worker thread, including
checkpoint operations; do not share a transaction between unrelated coroutines.
Enable and verify WAL, foreign keys and an explicit busy timeout. Prefer FULL
synchronization for checkpoints exposed to Hermes. SQLite has one writer in
WAL mode; WAL requires local filesystem shared-memory behavior. Current SQLite
documentation also describes a multi-connection WAL race fixed in 3.51.3 and
specified backports. Record the actual linked SQLite version in each pinned
runtime, not merely Python's version. [SQLite WAL](https://www.sqlite.org/wal.html)

Use short `BEGIN IMMEDIATE` write transitions, rollback on failure, and verify
affected-row counts. It can return SQLITE_BUSY rather than upgrading a stale
read transaction later. [SQLite transactions](https://www.sqlite.org/lang_transaction.html)
Foreign-key enforcement must be explicitly enabled per connection and checked.
[SQLite foreign keys](https://www.sqlite.org/foreignkeys.html)

Atomic transition examples:

1. Ready-to-running: check nonterminal run + remaining budget, claim activation,
   increment budget and persist attempt-start/event; commit; then call Ollama.
2. Completion: verify attempt/run version, save output or tools and status,
   route tokens/update ready frontier, append events; commit; then notify.
3. Continuation: validate namespace/run/batch/deadline and all results, insert
   request claim and new accepted results, close a completed batch, append
   checkpoint/events; commit; only the winning claim schedules work.
4. Terminalization: compare nonterminal status, preserve first terminal reason,
   prohibit new claims/exposure, mark open batches terminal and append events;
   commit; then cancel and await owned tasks. Late task completion cannot
   overwrite terminal state because its predicate fails.

No DB transaction spans inference, network delivery, filesystem fsync or an SSE
await. Retention deletes terminal run records under FK-safe transactions, never
graphs, published revisions or live pending mappings. Replay evidence lives at
least as long as its run's configured history retention.

## Recovery, cancellation and resource accounting

At startup, recover storage before readiness. Waiting checkpoints with no
uncertain attempts retain original IDs, responses and unexpired deadlines.
Expired waits become failed with a timeout reason. A persisted running attempt
whose completion was not committed makes the run `interrupted`; do not retry
it automatically. Node status can be `failed` with interruption detail because
the specified node-status enum lacks `interrupted`. Queued never-started runs
may resume admission; terminal history is unchanged. Pending durable requests
join a recovered checkpoint or receive the explicit interrupted status.

Keep strong references to runtime tasks and propagate CancelledError after
cleanup. TaskGroup cancels siblings on failure; bare gather does not provide
that failure behavior. Cancellation remains cooperative, so terminal-state
predicates are still required. [Python asyncio tasks](https://docs.python.org/3.11/library/asyncio-task.html)

Proposed accounting to freeze in G1:

- `CG_MAX_ACTIVE_RUNS` counts admitted nonterminal graph runs, including
  `waiting_tools`; `CG_MAX_QUEUED_RUNS` bounds additional not-admitted runs.
  Waiting runs retain an admission slot but no inference permit. This is the
  simplest bound on suspended state; four waits can delay new runs until
  completion/cancellation/TTL. A different policy needs an explicit bound for
  waiting runs rather than silently releasing unlimited capacity.
- Active elapsed time is run wall-clock execution time while admitted and
  computing/draining, including semaphore waits; concurrent nodes do not
  multiply it. Queued time and quiescent external tool wait are separate.
  Use monotonic deltas in-process and persist accumulated elapsed time at
  state transitions. Restart during uncertain active work interrupts it.
- Start the tool deadline when the durable external batch is prepared; preserve
  its UTC expiry across process restart. Partial results, retries, client
  disconnects and UI refresh do not extend it. Expiry includes process downtime.
  Wall-clock rollback remains a host-clock assumption to document/test.
- Each provider exchange gets its own timeout after acquiring the permit;
  queueing remains bounded by the active budget/admission policy. Hold the
  permit through complete JSON/SSE consumption and release in `finally`.
  Direct passthrough uses the same limiter. A semaphore limits concurrent
  holders; it does not bound the number of queued HTTP requests, so the API
  also needs a bounded admission path for direct exchanges. [Python semaphore](https://docs.python.org/3.11/library/asyncio-sync.html#semaphore)
- At most two explicitly safe upstream retries; no retry of delivered external
  effects. Every retry rechecks cancellation and budgets. No disk inference
  cache, minimum parallelism or speculative provider calls.

Finishing a tool response is normal detachment, not initial-request cancellation.
An initial request disconnect cancels active work best-effort, except committed
tool exposure is treated as ambiguous delivery and retained for replay. A
continuation waiter disconnect must not cancel shared replay work implicitly.
Freeze these adapter callbacks before API and runtime implementations diverge.

## Graph files, snapshots and publication

Use JSON files as graph authority and SQLite as run/history authority. Under
one per-graph repository lock: validate safe ID and expected revision, write a
same-directory temporary file, flush/fsync, then replace the draft; fsync the
directory where supported. Publication creates an immutable revision file with
the same durability pattern. Treat the highest valid published revision as
the current publication (no unpublish API is specified). An orphan temporary
file is never listed; a complete published file after a crash is authoritative.
Do not maintain an independently committed DB pointer that can advertise a
missing publication. Corrupt immutable files cause explicit storage errors.

Starting a run reads exact bytes/revision under the repository lock, canonicalizes
and hashes the complete graph, then inserts that snapshot into SQLite before
scheduling. The lock may span this short insertion but no inference. Subsequent
edits cannot alter the run. Published revision files never mutate. A caller
requesting an overwritten draft revision gets a revision conflict unless that
revision is retained as an immutable publication; do not substitute current
draft silently. This policy needs documenting in G1's management API.

Atomic replacement behavior and fsync durability must be tested on the actual
Linux named volume. Do not infer power-loss guarantees from NTFS-host unit
tests. Use a stopped/quiescent complete-volume backup for the simplest consistent
graph-plus-history backup; never copy only a live `.db` and omit its WAL. If
online SQLite backup is later used, the backup API provides a database snapshot,
but graph consistency still needs coordination. [SQLite backup API](https://www.sqlite.org/backup.html)
Restore to a separate owned volume and verify hashes, revisions, waiting IDs
and history before replacing any data. No backup, deletion or restore is
performed in this advisory.

## External runtime and local security boundaries

The browser addresses the frontend origin at `127.0.0.1:8080`; its `/api` and
`/v1` requests proxy to Compose `backend:8000`. Hermes on Windows/WSL2 uses the
host-published API at `127.0.0.1:8000/v1`. Inside the backend container,
`127.0.0.1` refers to that container. Docker Desktop documents
`host.docker.internal` for reaching the host; a native WSL Docker engine needs
its own tested route. [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/)

The environment report proves Windows/Ubuntu loopback Ollama access, but host
probes to `host.docker.internal` failed. That is neither proof nor disproof of
the eventual backend-container route. Keep Ollama external even though this
machine's existing service happens to be a user-owned container. Do not attach,
restart, reconfigure or assume ownership of it. Keep data in `cg_data`, not a
shared Windows source bind mount; no Docker socket, Hermes home or Windows tool
directory belongs inside Compose.

Optional token validation must cover management, OpenAI, event and tool-result
routes consistently. Browser use needs a deliberate token-entry/header strategy;
native EventSource cannot be assumed to carry an Authorization header. Prefer
fetch-based SSE with an in-memory token; never place tokens in URLs, graph JSON,
bundles, screenshots or persisted traces. Same-origin and loopback remain the
default; no account system or new cloud dependency is required.

Use allowlisted graph IDs and repository-created paths, strict size limits on
requests/graphs/tool results, terminal-state guards and sanitized structured
logs (run/activation/event IDs, status, durations, counts). Full prompts/results
belong only in authorized local run history; do not log request headers or
provider exceptions containing URLs with credentials. Enforce positive configured
limits at startup and reject multiple backend workers. Record queue time,
activation time and call counts without promising GPU speedup.

Ollama documents Chat Completions streaming, tools, tool_choice and
response_format, but that list is not proof of the selected model's controller
JSON or tool behavior. RD1 and G6 own live compatibility evidence. Do not infer
`parallel_tool_calls` fidelity from absent documentation or conflate it with
the proxy's external batching policy. [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility)

## Decisions still needed before G1 freeze

1. RD1 outcome: exact latest-segment parsing, ID normalization, streaming and
   request profile, client iteration/time limits and native tool/control model
   proof. A failure is a G0 blocker; architecture proposals do not bypass it.
2. Count `CG_MAX_TOOL_ROUNDS` per exposed external batch (recommended to align
   with Hermes turns) or per model-produced tool round. Freeze the meaning and
   tests; serial delivery can require several batches for one provider round.
3. Confirm partial Chat Completions waiting/error wire semantics and duplicate
   in-flight request joining. Do not respond with fake `stop` or duplicated tools.
4. Confirm active-slot treatment of waits and bounded direct-request admission.
   The recommendations above avoid inventing another configuration variable.
5. Confirm retained-revision lookup for UI test runs and file-authoritative
   publication recovery. This is an implementation choice, not a new feature.

These choices can normally be resolved by the lead from RD1 and the existing
specification. Only a demonstrated material compatibility conflict needs user
disposition. No currently discovered missing environment fact blocks this report.

## Evidence, verification and handoff

Read commands used PowerShell `Get-Content -Raw` for the full root specification,
AGENTS.md, the five assigned artifacts, environment report and the installed
`team-spec-workflow`/`team-documentation` SKILL.md files; successful reads exited
0. A combined initial tool response was truncated; the specification, skills
and artifacts were then reread with sufficient output budgets. Ancestor and
descendant guidance discovery found no additional AGENTS.md; `rg --files -g
AGENTS.md -g '!node_modules' -g '!.venv' .codex docs` returned 1 (no matches),
not a validation pass. The environment report independently records absent
`D:/AGENTS.md` and `D:/Sources/AGENTS.md`.

Executed read-only runtime probe:

```powershell
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Exit 0; Windows interpreter links SQLite `3.53.1`. This is local evidence, not
a pin for the future backend image. Official SQLite/Python/Ollama/Docker pages
linked above were read on 2026-10-03. No inference, external mutation, credentials,
dependency installation, product test or smoke test was performed.

Verification classification: `[skip-verify]` for runtime acceptance, because this
assignment is architecture analysis only. Evidence is the traceable A03–A10,
A13/A14/A16 contract analysis above. Proposed checks remain unexecuted and do
not close those scenarios, G0, or A15. Implementation owners must add executable
fault-injection, fake-clock, provider-contract and live checks in their assigned
groups. Independent review-agent remains mandatory.

Rollout: lead accepts/revises recommendations into decisions/design, then G1's
single writer freezes DTOs/schema/state transitions before parallel modules.
Rollback: change these proposals freely before freeze; after persistent data
exists, back up first and use a versioned migration rather than dropping state.
Residual risks: uncertain external tool delivery cannot be made transactional;
runtime/model and host/container behavior remain live gates; optional-token
rotation affects continuation namespace; host clock adjustments affect durable
TTL; conservative serialization and quiescent handoff may add latency.

## G1 concrete contract advisory — 2026-10-03

Owner: `sa_g1` (sa-agent), exact handoff in [tasks.md](tasks.md#g1-contract-architecture-advisory).
This appended section preserves the historical G0 advice. Accepted policy remains
in [decisions.md](decisions.md#2026-10-03--g0-pass-g1-contract-decisions).
G0 independently passed cycle 2; this advisory consumes no review cycle and
does not declare G1 or any runtime scenario passed.

### Reviewed draft and scope

Read the complete root specification and project AGENTS.md, installed
team-spec-workflow/team-documentation skills, accepted decisions, G0 review
outcome, design, prior advisory, and current `backend/app/contracts/` models and
contract tests. No ancestor or descendant AGENTS.md was found in the inspected
paths. `coding_bootstrap` remains the only contracts/manifests/bootstrap writer.

Initial inspected `interfaces.py` SHA256:
`df6249b3deb1930e2a99b2fcc20beb1dcf4074f917f7ca979561bea38352dbdd`.
At this inspection `docs/api.md` did not yet exist. Findings below describe
concrete draft seams, not defects in a runtime implementation that has not yet
been written. The owner received the questions through team messages before
this report; any reconciled updates will be recorded below.

The draft already represents the important static boundaries: a serialized,
hash-checked `GraphSnapshot`; mandatory `FeedbackEdge.initial_value` accepting
explicit null; non-null root scope/iteration identity; per-loop external and
feedback token state; activation/provider-round/call-ordinal tool ownership;
fixed batch expiry; durable replay claims; and a shared admission interface.
Generated schemas and tests are the contract owner's verification responsibility.

### Actionable interface gaps, ordered by impact

P0/P1 below denote implementation priority, not formal security severity.
Every row is owned by G1 `coding_bootstrap` for the contract resolution and by
the named downstream group for executable proof.

| ID / priority | Concrete draft reference and failure case | Resolution before freeze | Required downstream evidence |
| --- | --- | --- | --- |
| SA-G1-01 / P0 | `RunRepository.save_checkpoint(checkpoint, expected_version)`, `claim_activation`, `accept_results`, `terminalize`: a scheduler reads version N, results or cancellation commit N+1, then an old full checkpoint writes stale pending tools/status. The signature alone does not define version advancement, ownership or merge. | All mutations advance the run version in one short transaction. Full checkpoint CAS rejects stale versions; reload and merge only the intended activation/frontier delta. Never restore old accepted results, decrease counters, replace immutable context/snapshot, or reopen terminal runs. Activation completion also checks its durable attempt identity. Persist events in the same transition. | G2 A09/A14: controlled races between two node completions, partial result insertion and cancellation; stale saves rejected without losing accepted data or first terminal reason. |
| SA-G1-02 / P0 | `checkpoint_batch`/final run completion are separate from `complete_claim(claim_id, envelope)`. Crash after the next batch commits but before claim completion can leave a pending request with no defined durable association to its correct next response. Multiple partial submitters and management completion make a single current claim insufficient. | Persist the relationship between source batch and its next response/error transactionally with the next exposure or final completion. Complete all applicable claims in that transaction, or define a durable source-batch outcome from which claims are deterministically reconstructed. No HTTP bytes precede that commit. Replaying an old claim must never substitute the newest batch. | G2/G3 A09/A10: crash at every boundary with two partial claims plus management submission; all exact retries recover the same completion ID/content and tool IDs with unchanged call counts. |
| SA-G1-03 / P0 | `GraphRuntime.await_response(run_id, namespace)` has no response cursor. A continuation could immediately receive an earlier batch envelope still present for the run. `ToolBridge.await_response(claim_id)` has the necessary identity but ownership is unstated. | Either explicitly restrict runtime await to the initial request and require every continuation to use claim-bound bridge await, or add a durable batch/response cursor. A partial claim waits for the remaining results and next response, never receives the outstanding batch again. | G3 A08/A09: two sequential batches and simultaneous partial/replayed requests receive exactly their assigned response. |
| SA-G1-04 / P0 | `GraphRuntime.cancel` is unconditional, while initial-request disconnect must preserve committed ambiguous tool delivery. A handler's read-then-cancel check races with `checkpoint_batch`. | Add an initial-disconnect operation or a conditional cancellation predicate sharing the same atomic exposure boundary. If exposure wins, retain IDs/checkpoint; if cancellation wins, reject new exposure. Explicit user cancellation remains unconditional and terminal. Continuation disconnect does not cancel shared work. | G2/G3 A10/A14: force disconnect on both sides of exposure commit; no regenerated tool IDs or cancelled committed continuation from the disconnect race. |
| SA-G1-05 / P1 | `AdmissionController.acquire`/lease `wait` and `OllamaAdapter.stream -> AsyncIterator[bytes]` do not specify queue reservation timing or stream close ownership. An unbounded acquire wait or early permit release defeats A16. | Acquire atomically reserves active or queued capacity and immediately returns 429 when both are full. Waiting tools retain their admission lease. One adapter instance owns the global inference semaphore through full JSON/SSE consumption; callers explicitly close streams on cancellation/error, with idempotent permit release. No admission lease is held merely for replay lookup. | G2/G3 A14/A16: mixed direct/graph streaming and tool waits fill exact capacities; overflow, cancellation and malformed upstream SSE do not leak permits or exceed the global limit. |
| SA-G1-06 / P1 | `RunRepository.recover`, `GraphRuntime.shutdown`, and `terminalize(status: RunStatus)` lack explicit checkpoint/terminal ordering. A blanket shutdown cancellation can erase valid waiting IDs; a blanket terminal guard can reject successful final-response replay. | Shutdown preserves durable waiting checkpoints and fixed UTC expiry. Recover expires waits and marks uncertain active attempts interrupted before readiness; restore waiting/queued admission. Restrict terminalization to terminal states and preserve the first terminal outcome. Completed exact claims may replay after successful completion; changed/new/late results on cancelled, failed, interrupted or expired runs conflict before mutation. | G2/G3 A09/A10/A14: graceful shutdown and abrupt restart, expired partial waits, final-response replay after completion, and cancellation versus late results. |
| SA-G1-07 / P1 | `CompiledGraph.final_llm_node_id: SafeID` requires an LLM even though the approved format does not prohibit an input-to-output graph. | Make the field optional for a validated passthrough graph. Apply final-node generation overrides only when an LLM supplies the final output. Do not add an undocumented topology restriction. | Graph/runtime owner A04: input-to-output graph compiles and returns its input with no inference; normal final LLM/controller behavior remains unchanged. |

### Loop, continuation and persistence constraints to carry into implementation

`Validator.compile` must populate lexical `PortPlan.ordered_ports`, validate the
forward DAG and cyclic SCC declarations separately, and reject cycles in the
graph of collapsed loop scopes. `LoopPlan` plus the snapshot supplies feedback
seeds and configured continue/exit values; `LoopState.external_inputs` are
latched once and rebound to each new iteration without modifying values.
Feedback may originate at any scope member. Start the next iteration only after
the controller's validated continue decision; only its exit payload crosses the
scope boundary. All-port presence includes explicit null. These are semantic
compiler/runtime obligations, not claims that Pydantic syntax tests prove them.

`checkpoint_batch` must reject exposure while any activation has an uncertain
running provider attempt. Runtime stops new dispatch and drains already-started
siblings first. One open batch, a single durable winning resume transition, and
immutable accepted result strings must be enforced by storage constraints and
transaction predicates. `ToolBridge.classify` validates the latest relevant
segment's namespace/model/batch/owner/arguments against persisted mappings;
historical closed IDs before a new turn do not resume an old run. Compressed
continuation history never replaces the immutable original run context.

The raw argument hash and canonical echo-comparison hash serve different
purposes: preserve the exact delivered argument string and canonicalize only
for the explicitly permitted Hermes echo comparison. Do not use semantic JSON
normalization to excuse changed tool result strings or changed replay requests.
Canonical request hashes include the full accepted semantic request profile.

Partial acceptance and exact replay never extend `ToolBatch.expires_at` or
increment exposed-batch tool-round counts. Active elapsed time excludes
quiescent tool wait and queued time; it includes scheduling/provider-permit wait
while computing. `waiting_tools` keeps active admission capacity and releases
inference capacity. No SQLite transaction spans inference, SSE, HTTP delivery,
or any wait for another request.

`GraphRepository.load_snapshot` must honor current draft or retained published
revision lookup, with 409 for overwritten unpublished drafts. File authority
and immutable snapshot insertion remain as accepted in decisions.md. No
database publication pointer, tool executor, inference cache, extra Ollama
container, global configuration change or new external service is proposed.

### Verification, ownership, rollout and residual risk

Evidence commands: `Get-Content -Raw` for the sources and contracts named above
exited 0; `Get-FileHash -Algorithm SHA256 backend/app/contracts/interfaces.py,
backend/app/contracts/graph.py, backend/app/contracts/api.py,
backend/app/contracts/config.py` exited 0. `rg --files -g AGENTS.md -g
'!node_modules' -g '!.venv' backend .codex docs` exited 1 because it found no
additional guidance, not because an acceptance test failed. One initial combined
read was truncated; the specification, skills and artifacts were reread with
sufficient output limits. No runtime test, model call, environment mutation,
secret access or deployment was executed by this advisory.

Verification classification: `[skip-verify]` for executable behavior. The
interleavings above are analysis and proposed tests, not executed fault
injection. This report relies on current local contracts and approved product
semantics; it introduces no new framework/runtime capability claim requiring
external documentation. The G0 official-source qualifications remain historical.

Rollout: contract owner resolves these seams in signatures and normative API
documentation; lead accepts decisions, then independent G1 review evaluates the
coherent freeze before downstream writers begin. G2 owns durable transitions,
loops and admission; G3 owns provider stream lifetime, routing and HTTP
disconnect/continuation integration. Rollback before persistence exists is a
scoped contract/schema update; afterward any identity/claim/storage change needs
a versioned migration and preserved backups, never dropped pending state.

Residual risks remain external ambiguous tool delivery, unavailable actual
Compose/Ollama routing proof, host clock changes affecting UTC deadlines, and
future implementation drifting from the shared contract. This advisory does
not resolve live gates or replace the independent review-agent verdict.

### G1 owner reconciliation and advisory disposition

The contract owner responded and updated only its assigned files. A fresh
read of `interfaces.py` and `docs/api.md` confirms the following resolutions;
the initial finding table above is preserved as review history, not a list of
currently unresolved contract defects.

| Finding | Current resolution inspected on disk |
| --- | --- |
| SA-G1-01 | API documentation specifies one runtime frontier reducer, version advancement for every mutation, stale-CAS rejection/reload/rebase, immutable accepted results/context/responses, and attempt-identity guards. No stale full-checkpoint retry is allowed. |
| SA-G1-02 | Separate `complete_claim` was removed. `checkpoint_batch` and new `complete_run(checkpoint,envelope,expected_version)` atomically persist the outcome and seal all applicable source-batch claims. `RunCheckpoint.responses`, `ResponseEnvelope.response_sequence`, and `ReplayClaim.after_response_sequence` preserve the association across restart. |
| SA-G1-03 | `GraphRuntime.await_response(..., after_response_sequence=0)` returns the first stored response strictly beyond the cursor. Bridge await uses the durable claim. All partial/full/management claims resolve to their source batch's first subsequent response; a non-exact new request for a closed older batch returns 409 without scheduling. |
| SA-G1-04 | `GraphRuntime.detach_initial` uses `RunRepository.cancel_if_unexposed` at the same transactional boundary as batch exposure. Explicit cancel remains distinct. Documentation prohibits the read-then-cancel race. |
| SA-G1-05 | Acquire reserves active/queued capacity before return; wait adds no reservation. Waiting tools retain active leases. Provider stream returns closeable `AsyncGenerator[bytes,None]`; callers await `aclose()` on error/disconnect, and the shared permit lasts through full consumption. |
| SA-G1-06 | `TerminalFailureStatus` limits failure terminalization; success requires atomic `complete_run`. Documentation orders completed exact replay, conflicting/late results, fixed deadline checks and pending claims. Graceful shutdown preserves safe waits/queued runs; recovery expires waits and interrupts uncertain attempts before readiness. |
| SA-G1-07 | `CompiledGraph.final_llm_node_id` is nullable, and docs explicitly allow input-to-output without an LLM. Final generation overrides have no provider call to affect in that case. |

One final construction seam was also resolved: `AsyncGraphRuntime`'s documented
constructor now receives `validator: Validator`. Recovery compiles each
preserved `RunRecord.snapshot`; it never loads a newer draft/publication.
The injectable `Clock` seam supports the required deterministic timeout tests.
`ToolCheckpoint` now rejects a running sibling and validates exposed batch,
mapping and response membership syntactically; storage must still verify the
authoritative database state transactionally. No syntax validator proves the
absence of an actual in-flight task.

Inspected reconciliation hashes:

- `backend/app/contracts/interfaces.py`:
  `1199677d3ce6d923688ef8197b0db9545506ab2dcec1b57e5f1948302771e1b6`.
- `docs/api.md`:
  `2cc59eba0f3276b7f27f988da8ee9dabbaf2c5503f78cb05dd4440717101d8d8`.

No unresolved architecture-contract blocker remains from this advisory at
those hashes. This is not an independent PASS: the lead must harvest the
bootstrap verification and obtain G1's review-agent verdict. All proposed
race/fault/restart/concurrency tests in the finding table remain required
downstream executable evidence; no production scenario is closed here.

Documentation-only validation: `git diff --check --
.codex/specs/cognitive-graph-mvp/sa-review.md` exited 0; Git warned about its
normal LF-to-CRLF conversion. Read/hash commands for the reconciliation exited
0. The G0 section remains intact. This agent authored only `sa-review.md` and
made no commit, deployment, configuration or product-code change.
