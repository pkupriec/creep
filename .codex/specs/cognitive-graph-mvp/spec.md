# Cognitive Graph MVP — spec

Authority: Cognitive_Graph_MVP_Codex_Team.md v1.1, 2026-10-03.
Sections below are preserved verbatim. No research gate is closed by extraction.

## 3. MVP Scope and Constraints

### Included

- OpenAI Chat Completions interface for Hermes: `/v1/models`, `/v1/chat/completions`.
- `input`, `llm`, and `output` nodes, conditional LLM outputs, explicit feedback edges.
- Concurrent execution of independent ready nodes through a shared, bounded Ollama request pool.
- One backend process, JSON graph files, SQLite for state and history.
- Tool calls returned to Hermes, followed by resumption of the waiting node.
- Editor, graph publication, UI test execution, traces, cancellation.
- Reproducible Docker Compose deployment and Hermes setup instructions.

### Deferred

Distributed execution, multi-tenancy, cloud deployment, custom shell/MCP executor, separate long-term memory/RAG, product-owned tools, arbitrary Python in nodes, automatic model-generated graph changes, multimodal inputs, nested graphs, visual Graph Pipelines, native Ollama `/api/chat` and `/api/generate`, and a complete Responses API implementation. Text and function tools are mandatory. Do not advertise unsupported APIs.

MCP and tools already connected to Hermes are used through its exposed function schemas and executor. Maintain a modular `ToolBridge` boundary for future direct MCP support. The proxy cannot automatically access capabilities that Hermes does not expose through context or tools.

Configure the base model at graph level. MVP nodes do not switch model weights. Direct mode may use other client-selected models as separate requests. The proxy does not copy weights or start an inference server per node and cannot guarantee Ollama's internal VRAM residency behavior.


## 4. APIs and Configuration

### 4.1 Client Contract

`GET /v1/models` returns a standard `list` object containing published `cg/<graph_id>` and physical `ollama/<model_name>` models. Namespaces prevent collisions. Draft graphs are hidden.

`POST /v1/chat/completions` accepts `model`, `messages`, `tools`, `tool_choice`, `parallel_tool_calls`, `stream`, `temperature`, `top_p`, `max_tokens`, `stop`, `response_format`, and `stream_options` within the agreed compatibility profile. Unsupported parameters that could affect semantics return 400 instead of being silently ignored. Record the supported subset in `docs/hermes-compatibility.md` after R&D. Only `n=1` is supported. Preserve tool schemas and JSON arguments.

Direct mode translates the model name and forwards the request to Ollama's external `/v1/chat/completions`. Verify JSON, SSE, tools, and errors, not just text. Never substitute another model for an unknown model.

In graph mode, client `temperature/top_p/max_tokens` apply to the final node; other nodes use stored settings. `tool_choice=none` disables tools throughout the run. Forcing a specific tool is supported only for graphs with one tool-capable node; otherwise return 400 `unsupported_tool_choice`. Do not apply a forced call independently to every node. `parallel_tool_calls=false` limits external delivery to one call per response. `response_format` applies to the final external response; internal control JSON has a separate contract.

Return a standard `chat.completion` with one choice, a message containing `content` or `tool_calls`, and `finish_reason=stop|tool_calls|length`. Completion `id` is not a session identifier. `X-CG-Run-ID` is a diagnostic response header; Hermes need not echo it.

Errors: `{"error":{"message":"...","type":"invalid_request_error","code":"graph_validation_failed"}}`. HTTP codes: 400 invalid graph/parameter, 404 unknown model/graph, 409 publication/resumption conflict, 429 full queue, 502 upstream error, 503 Ollama unavailable, 504 timeout. After SSE starts, emit the documented error event and close the stream. Do not imitate successful `stop`.

### 4.2 Management API

| Method / route | Contract |
| --- | --- |
| `GET /health/live`, `GET /health/ready` | Process liveness and storage readiness; report Ollama availability separately |
| `GET /api/graphs` | IDs, names, revision, published_revision |
| `POST /api/graphs` | Create; ID collision returns 409 |
| `GET /api/graphs/{id}` | Graph JSON and revision |
| `PUT /api/graphs/{id}` | Save with expected_revision; lost update returns 409 |
| `POST /api/graphs/{id}/validate` | Errors with node_id/edge_id and warnings |
| `POST /api/graphs/{id}/publish` | Validate and atomically publish the revision |
| `POST /api/runs` | `{graph_id,revision,inputs,messages?,tools?}`; return run_id |
| `GET /api/runs` | Pagination and graph_id/status filters |
| `GET /api/runs/{id}` | Snapshot, states, results, pending tools, error |
| `GET /api/runs/{id}/events` | SSE with monotonic event_id; support Last-Event-ID |
| `POST /api/runs/{id}/cancel` | Idempotent cancellation |
| `POST /api/runs/{id}/tool-results` | Test UI: tool_call_id/content array; validate pending IDs |

The UI does not independently access the Hermes environment. Tool-enabled graphs display `waiting_tools` and allow manual result submission. Real tools are tested through Hermes. Manual results do not prove complete Hermes integration.

### 4.3 Environment Variables

| Variable | Default / meaning |
| --- | --- |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434/v1` |
| `CG_DATA_DIR` | `/data` |
| `CG_API_TOKEN` | Optional local access token; when configured, required for both API surfaces |
| `CG_MAX_PARALLEL_LLM` | 2; global semaphore, not per run |
| `CG_MAX_ACTIVE_RUNS` / `CG_MAX_QUEUED_RUNS` | 4 / 20 |
| `CG_LLM_TIMEOUT_SECONDS` | 300 per upstream call |
| `CG_RUN_ACTIVE_TIMEOUT_SECONDS` | 1800 total active execution time |
| `CG_TOOL_WAIT_TIMEOUT_SECONDS` | 1800, separate from active execution |
| `CG_MAX_NODE_EXECUTIONS` | 100; emergency execution budget |
| `CG_MAX_TOOL_ROUNDS` | 20 per run |
| `CG_HISTORY_RETENTION_DAYS` | 30; configurable |

These names and values are proposed MVP defaults, not measured characteristics. Explain the separate tool-wait TTL in the UI. Users select an installed physical model when creating a graph; do not hardcode an unavailable model.


## 5. Graph File Format

Canonical format: UTF-8 JSON, `schema_version=1`. Export Pydantic as JSON Schema and use matching TypeScript types. UI coordinates do not define execution order.

```json
{
  "schema_version": 1,
  "id": "synthesis",
  "name": "Two experts and synthesis",
  "revision": 1,
  "base_model": "USER_INSTALLED_MODEL",
  "inputs": [{"id": "chat", "required": true}],
  "nodes": [
    {"id": "input", "type": "input", "input_id": "chat", "position": {"x": 0, "y": 100}},
    {"id": "a", "type": "llm", "system_prompt": "Analyze correctness.", "tools_enabled": true, "generation": {"temperature": 0.2}, "position": {"x": 250, "y": 0}},
    {"id": "b", "type": "llm", "system_prompt": "Analyze alternatives.", "tools_enabled": true, "generation": {"temperature": 0.2}, "position": {"x": 250, "y": 200}},
    {"id": "s", "type": "llm", "system_prompt": "Synthesize all inputs into the final answer.", "tools_enabled": false, "generation": {"temperature": 0.2}, "position": {"x": 500, "y": 100}},
    {"id": "output", "type": "output", "position": {"x": 750, "y": 100}}
  ],
  "edges": [
    {"id": "ia", "source": "input", "target": "a", "target_port": "question", "kind": "forward"},
    {"id": "ib", "source": "input", "target": "b", "target_port": "question", "kind": "forward"},
    {"id": "as", "source": "a", "target": "s", "target_port": "correctness", "kind": "forward"},
    {"id": "bs", "source": "b", "target": "s", "target_port": "alternatives", "kind": "forward"},
    {"id": "so", "source": "s", "target": "output", "target_port": "answer", "kind": "forward"}
  ],
  "loops": [],
  "output_node_id": "output"
}
```

Each input port has exactly one provider. Multiple inputs use separate named ports. One output may feed any number of nodes. Required values must be present; an omitted optional input produces explicit null, keeping all-port readiness defined. Serialize predecessor results with node_id/port and stable port order, independently of task completion order.

Files: `/data/graphs/<safe-id>.json`; published revisions: `/data/published/<safe-id>/<revision>.json`. Use temporary-file writes, fsync, and atomic rename. Validate IDs against an allowlist pattern; reject arbitrary paths. The backend increments draft revisions; publication requires expected_revision. Every run stores a complete immutable snapshot and hash. Editing or publishing does not change an existing run. Import validates the schema; ID collisions require an explicit new ID or saving against an expected revision. Export excludes secrets and history.


## 6. Execution, Fan-In, and Loops

### 6.1 Nodes and Context

A node starts only after all input ports for the same activation have arrived. Output has one input; exactly one terminal output is allowed. Store Hermes history as separate run context. Preserve client system constraints and add the node role prompt without removing original instructions. Predecessor outputs are data, not new system instructions.

An LLM node receives original chat context, its prompt, current inputs, and its own tool history. Other nodes' calls must not appear as its calls. Store results and compact control data; do not require hidden chains of thought. Context overflow produces an explicit error or a documented reduction strategy. Never silently discard instructions or tool-call/result pairing. Validate message construction with the target model during R&D.

Execute independent ready nodes concurrently with a global semaphore. Fan-in waits for all results. Failure of a required node fails the run and cancels remaining tasks; hidden partial synthesis is prohibited. Automatic retries apply only to safe upstream failures before tools/responses are delivered, with at most two retries. Never repeat external side effects through retries of tool arguments/results.

### 6.2 Explicit Loop Model

Ordinary `forward` edges form a DAG. A `feedback` edge transfers data to the next iteration and does not block the first iteration. Every cyclic strongly connected component (SCC) belongs to one declared loop scope. Reject nested/overlapping scopes in the MVP. Multiple disjoint loops are supported. After drawing feedback, the UI requires a scope, controller, seed, and exit condition.

Loop definition: `id`, `node_ids`, `controller_node_id`, `continue_value`, `exit_value`. Feedback edge: `loop_id`, `target_port`, `initial_value`. Every feedback seed is mandatory, including explicit null if appropriate. External loop inputs are immutable and available every iteration. Scope nodes are reachable through forward paths. The controller is the final scope node; every node has a path to it. Outgoing scope edges are permitted only from the controller and receive final payload on `stop`.

Example: `draft → critique`, with `critique → draft` as feedback. Seed: `"No previous critique"`. The question remains available every iteration. The controller returns `{ "payload": "...", "control": { "decision": "continue" } }` or `stop`. Use strict JSON Schema with enum decision and payload. Missing/invalid decisions are errors; the dispatcher does not interpret prose. Controller tools finish through the ordinary tool loop before control JSON is produced.

Tag tokens with `(run_id, loop_id, iteration, node_id, port)`. Never mix iterations. On continue, start the next iteration with new feedback and constant external inputs. On stop, emit payload. Continue emits no external data. Required branching uses this control-port contract; arbitrary expressions/eval are unnecessary.

Conditional termination is normal semantics. Exceeding execution, tool-round, or time budgets returns `budget_exceeded`/`run_timeout`, not a successful answer. Emergency budgets prevent hangs without replacing exit conditions.

Validation checks unique IDs/ports, valid sources, all required ports, one output, reachability, forward-DAG structure, declarations for all cycles, seeds, controller validity, and absence of loop output bypasses. Reject graphs that cannot reach output before publication.


## 7. Hermes Tools and Run Continuation

### 7.1 Responsibility Boundary

Hermes executes tools in its own environment: terminal, files, browser, MCP when available. The proxy receives schemas and returns standard assistant tool_calls. Do not move shell execution into the backend, mount a Docker socket, or grant direct Windows access to simplify the MVP.

Compatibility preserves model-visible schemas, arguments, results, and client constraints. Tool support in the selected model is an external prerequisite. Do not replace native calls with heuristic extraction of commands from prose.

### 7.2 Pause and Resume

1. An LLM node requests tools. Persist a checkpoint before replying.
2. Generate unique external tool_call_id values and persist `(external_id → run_id, activation_id, node_id, internal_id, arguments_hash)`.
3. Return assistant.tool_calls with `finish_reason=tool_calls`; hide internal outputs/control.
4. Hermes executes tools and submits another request with role=tool results and corresponding IDs.
5. Recognize pending IDs, validate model/graph and caller namespace, persist results, restore the owning node's history, resume that exact activation.
6. When the graph completes, return its final output. A new user turn starts a new graph run with history, rather than resuming a completed run.

Derive caller namespace from the API token without storing its value, or use one local anonymous namespace. The MVP is local and single-user. Never use a hash of the last question as session ID: independent conversations may ask identical questions. Generate opaque random globally unique tool IDs and durable mappings. Pending results without new user messages resume a run; mixing a new turn and pending continuation returns 409. Every initial request creates its own run; concurrent turns without tools need no client session ID.

Detect continuation from IDs in the latest relevant assistant/tool segment, not every old tool message. Unknown new IDs are errors. Closed historical IDs do not trigger resumption. Exact repeated continuation uses a canonical request hash plus pending batch to replay cached response/checkpoint without rerunning nodes/tools. Changed content for an accepted ID returns 409. Reject ambiguous routing rather than guessing.

Hermes may compress history or normalize IDs. Prove mapping and latest-segment detection on a pinned real version. If transparent continuation cannot be proven, record a blocker and propose a minimal client adapter. Do not claim compatibility with unmodified Hermes before this experiment passes.

### 7.3 Multiple Waiting Nodes

Deliver one external batch at a time. Combine simultaneously ready independent calls when parallel_tool_calls permits it; conservatively serialize unknown/side-effecting actions. LLM computation remains concurrent. Do not assume transactional tools or isolated directories: nodes share the Hermes environment and may observe one another's changes.

Support full-batch and partial results, waiting for remaining results. Never issue already-delivered calls again. Incomplete batches may wait until TTL; verify actual client behavior in R&D. Cover partial batches contractually even if Hermes always submits full batches. Only the owning node receives a tool result; downstream receives its final payload.

Cancellation/timeout prevents new calls and cancels LLM tasks. The proxy cannot forcibly stop a tool already executing in Hermes. Reject late results with explicit terminal status. External side effects are not rolled back.

After restart, restore waiting_tools from SQLite; original IDs remain valid until TTL. Mark active upstream executions with unprovable completion as interrupted and do not automatically rerun them. Preserve completed history.


## 8. Streaming and UI

Buffer internal LLM responses for fan-in/control validation. Externally stream only final output that requires no control-JSON validation. If the final node produces control JSON, buffer it and then emit payload through standard SSE. Tool responses support SSE role delta, tool_calls with index/id/function/arguments, finish_reason, and DONE. stream=false is semantically equivalent. SSE comment heartbeats before final output are allowed after verifying Hermes support. Never present intermediate text as the final response.

Disconnection during an active initial request cancels the run best-effort. Finishing a response to wait for tools is normal and preserves checkpoint. Disconnected batch delivery is ambiguous: replay uses the same IDs and creates no new calls.

UI: graph list, create/open/save/import/export, publish revision, left-to-right canvas with zoom/pan, multiple ports, connections/deletion, side panel for prompt/generation/tools_enabled/cycle/seed, one output and one or more inputs. Distinguish feedback arrows. Auto-layout is convenience, not semantics.

History: graph/status filters, start/end times, duration, revision/hash, run_id. Details: nodes/iterations, readiness, timestamps, payloads, errors, tools, upstream usage if available. Run statuses: queued, running, waiting_tools, completed, failed, cancelled, interrupted. Node statuses: pending, ready, running, waiting_tools, completed, failed, cancelled. Reopening restores state from API rather than lost browser state.

Use minimal React UI without an account system, separate chat client, or observability platform. History may contain sensitive Hermes data and is visible only to the local user. Never write keys to traces. History cleanup does not delete graphs.


## 10. Acceptance and Verifiable Scenarios

| ID | Scenario / required evidence |
| --- | --- |
| A01 | Hermes selects cg/synthesis using proxy base_url and receives final answer; record SHA/version and setup commands |
| A02 | ollama/<model>: ordinary chat, multi-turn, stream/nonstream, tool request/result through the same proxy |
| A03 | Diamond: both experts start before the other finishes; synthesis starts after both and receives both outputs in stable order |
| A04 | Multiple inputs, fan-out/fan-in; missing required input returns 400 before LLM calls |
| A05 | draft → critique → feedback: seed, two continue decisions, then stop; no iteration mixing; output only on stop |
| A06 | Endless continue ends in budget error; missing control, invalid seed, undeclared cycles rejected |
| A07 | Real Hermes tool reads test file; owning node resumes with result and supplies synthesis payload; tool executes in Hermes |
| A08 | Two nodes request tools: internal ID collisions isolated, results routed to owners, parallel_tool_calls=false honored |
| A09 | Identical questions in independent requests do not mix; unknown IDs, changed repeated results, replay covered |
| A10 | Restart after tool-call delivery: old IDs complete the same run; interrupted active calls marked interrupted |
| A11 | SSE tool JSON, finish_reason, DONE correct; final stream excludes intermediate/control; nonstream equivalent |
| A12 | UI creates/saves/opens, edits prompt/ports/feedback, publishes/imports/exports; restart preserves data |
| A13 | Edit during run does not change snapshot; revision conflicts do not overwrite; drafts hidden from models |
| A14 | Timeout/upstream failure/cancel/late results produce correct terminal status; queue overflow returns 429 |
| A15 | Clean Windows/WSL2 Compose with external Ollama: UI/API and real Hermes smoke work; restart preserves history |
| A16 | Schema/path validation and logs prevent arbitrary paths/token leaks; concurrency globally bounded across runs |

Unit/contract tests use deterministic fake provider and clocks; integration uses mock Ollama HTTP/SSE. Real Hermes/Ollama and target Windows/WSL2 smoke are separately required. If unavailable to the implementer, keep the live gate open and provide a runnable procedure; static checks cannot establish runtime PASS.

Implement real commands: make test, make lint, make test-contract, make test-e2e, make smoke-hermes, make smoke-compose. Commands must execute claimed checks and fail nonzero on errors; placeholders/always-green smoke are prohibited. Python: pytest/ruff; frontend: TypeScript check/tests; UI E2E: Playwright. Live smoke uses a dedicated Hermes test directory and never deletes user files.

Do not base performance promises on another GPU's token rate. Fake-provider tests prove concurrent ready-node startup, semaphore bounds, and no deadlocks. On target hardware measure wall time, queue time, node durations/call counts; compare diamond versus sequential execution on the same model. Record results without promising speedup if Ollama effectively serializes computation.

