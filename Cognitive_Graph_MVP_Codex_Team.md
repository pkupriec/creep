# Cognitive Graph: MVP Technical Specification for Codex Agent Team

Version 1.1 · October 3, 2026 · Slug: `cognitive-graph-mvp` · English edition

Status: user requirements are recorded. The architecture below is the proposed implementation contract. Hermes compatibility and editor selection require validation through R&D. This is an implementation assignment, not a report of completed development. This edition translates the original handoff without changing its product scope.

## 1. Purpose and Team Handoff

Build a local cognitive engine: an HTTP proxy between Hermes Agent and an external Ollama server that executes a graph of specialized nodes instead of a single model request. One model instance serves nodes with different prompts and contexts. Nodes synthesize predecessor outputs. The coordinator schedules execution according to explicit rules and does not make substantive decisions.

Implementation team: https://github.com/aws-samples/sample-codex-agent-team

Team repository tree revision examined for the original specification: `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`. This repository is a sample Codex configuration, not the product's agent execution platform. Keep the Codex development team separate from the local engine's Thought Nodes.

The handoff follows `docs/specs/templates/{spec,design,tasks}.md` and `team-spec-workflow`. At project startup, extract the following artifacts without losing requirements:

| File under `.codex/specs/cognitive-graph-mvp/` | Contents |
| --- | --- |
| `requirements.md` | Section 2: approved user intent |
| `spec.md` | Sections 3–8 and 10: contracts, behavior, acceptance |
| `design.md` | Sections 9 and 11: components, deployment, R&D |
| `tasks.md` | Section 12: groups, dependencies, waves |
| `decisions.md` | R&D outcomes, exact versions, deviations, blockers |
| `review.md` | Independent review history for each task group |

The team sample ignores generated specifications in git by default. Explicitly version these artifacts through `.gitignore` rules or keep canonical copies under `docs/specs/`. Do not leave the sole requirements source in an untracked temporary directory.

## 2. Approved User Requirements

| ID | Requirement |
| --- | --- |
| R01 | Hermes compatibility; proxy between the client and Ollama |
| R02 | Published graphs appear as virtual models; direct Ollama mode |
| R03 | Nodes can use the environment and tools available to an ordinary model in Hermes |
| R04 | A node waits for all inputs; the objective is synthesis, rather than competition between nodes |
| R05 | A loop terminates according to a condition |
| R06 | An explicit output node supplies the client response; intermediate results appear in the UI |
| R07 | Create, select, and edit graphs; store graphs as files; retain run history |
| R08 | Simple left-to-right visual editor: multiple inputs, many-to-many connections, cycles, node prompts; select an existing editor through short R&D |
| R09 | Test execution, statuses, node results, cancellation, graph import/export |
| R10 | Windows + WSL2, Docker Compose, external Ollama, Python/FastAPI + React |
| R11 | The specification must be executable by Codex using the selected team |

Streaming and full chat history were included in the proposal accepted by the user. Support `stream=true/false`, receive the history supplied by Hermes, and account for client-side compression. Multiple named inputs are configured in the UI; a standard Hermes request maps to the `chat` input. A separate visual layer for a sequence of graphs is not required in the MVP. One graph defines the pipeline, while internal interfaces leave room for future graph composition.

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

## 9. Architecture and Deployment

FastAPI components: GraphRepository, Validator, GraphRuntime, OllamaAdapter, ToolBridge, RunRepository, EventBus. The HTTP layer does not own execution: runtime survives individual requests. Asyncio scheduler plus SQLite WAL suffices; Redis/Celery/Kafka are unnecessary. Keep checkpoint/event/mapping transactions short; never hold a DB transaction during LLM/HTTP calls.

Entities: runs (snapshot/context/status/budgets), activations (node/loop/iteration/messages/payload), pending_tools (mapping/status/result), events (run_id/event_id/type/payload), response_cache (continuation hash/response). Persist events before SSE publication. Enforce idempotency through unique constraints, not only in-memory dictionaries. Use one backend worker; multiple Uvicorn workers are prohibited until an interprocess scheduler exists.

Layout: backend/app/contracts, graphs, runtime, providers, tools, storage, api; backend/tests; frontend/src; examples; docs; scripts; compose.yaml; Dockerfiles/lockfiles. One owner creates shared contracts/bootstrap; others import them. Do not manually duplicate frontend/backend schemas without consistency checks.

Compose services: backend and frontend (production static build, reverse proxy for /api and /v1); named volume cg_data:/data. Ollama remains external; no GPU passthrough is required. UI: 127.0.0.1:8080; API: 127.0.0.1:8000. Disable SSE buffering and set proxy timeouts above the active-run budget. Validate host.docker.internal on Docker Desktop. For native Docker Engine in WSL2, document host-gateway and actual reachability of Windows Ollama; do not assume these paths are interchangeable.

Start from WSL2: `docker compose up --build -d`. Prerequisites: Docker Desktop with WSL2 integration or separate Docker Engine, pinned dependencies, installed tool-capable Ollama model. readiness reports upstream connectivity clearly. Runbook covers safe container access to Ollama, volume persistence across down, SQLite/graph backups. Identify down -v explicitly as data deletion.

Local security: localhost binding, same-origin UI, HTTP/JSON size limits, bounded queues/concurrency, no arbitrary eval/path traversal, environment tokens excluded from graph files, sanitized logs. If LAN access is introduced, document mandatory auth/TLS; it is outside default deployment.

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

## 11. Required R&D Before Main Implementation

### RD1 — Hermes Tool Continuation

On a pinned Hermes revision inspect custom-provider/chat_completions routing, session/history, tool-ID normalization, maximum tool iterations, timeouts, streaming, compressor. Prototype two nodes, one tool round, final response; then two tool-capable nodes, replay, restart. Capture actual request/response traces without secrets. Verify Hermes does not treat the first tool response as completed work and that a full graph fits client iteration/time limits. Record exact setup and minimum Ollama model capabilities.

Deliver docs/research/hermes-protocol.md, reproducible test, decision in decisions.md. Unproven transparent compatibility makes G0 BLOCKED; do not build the main implementation on an unvalidated bridge. Discuss restricted compatibility profile or explicit Hermes adapter if necessary; never silently change requirements.

### RD2 — Existing Graph Editor

Compare React Flow (@xyflow/react) and Rete.js in a small React prototype. React Flow is the initial simplicity candidate, not a completed decision. Demonstrate diamond, multiple ports, feedback arc, loop membership/seed, prompt edit, JSON round-trip. Frontend execution engines must not define backend scheduler semantics.

Criteria: open-project-compatible license, sufficient OSS features, TypeScript/React, custom nodes/handles, serializable positions/edges, cycles allowed by configuration, usable loop selection, minimal integration complexity. Record versions/license/limitations and select one package. ELK/dagre only if needed; default coordinates suffice.

Deliver docs/research/graph-editor.md, short screenshot/test, selection ADR. Verify current documentation at installation and pin dependencies.

## 12. Team Plan: Groups and Waves

Main Codex thread or fullstack-agent owns specs, contracts, boundaries, consolidation. coding-agent owns runtime/API/UI/tests; devops-agent owns Compose/CI/runbook; review-agent provides independent PASS/FAIL; sa-agent optionally evaluates reliability/boundaries without adding AWS. Sample AWS plugins/IaC/MCP are not MVP dependencies; transfer only necessary reviewed configuration.

Each task includes group ID, dependency, writable files, criteria, command. Before delegation expand directory scopes into exact writable files in tasks.md and state no-edit boundaries. Shared files/lockfiles have one owner. Do not delegate broad backend implementation concurrently with its contract changes.

| Group | Outcome | Dependency |
| --- | --- | --- |
| G0-research | RD1/RD2, proven bridge and editor choice | None |
| G1-contracts | Schema, API, scheduler/continuation contracts | G0 |
| G2-runtime | DAG/loops/state/recovery, fake tests | G1 |
| G3-proxy | Ollama, Hermes tools, JSON/SSE API | G1; integrate G2 |
| G4-ui | Editor, graph file API, traces/history | G1; integrate G2/G3 |
| G5-delivery | Compose/CI/runbooks | G1; smoke after G2–G4 |
| G6-integration | All acceptance, real Hermes/WSL2 | G2–G5 |

### Wave 0: Validate Risks

- [ ] [coding] RD1 Hermes compatibility | `experiments/hermes_bridge.py`, `experiments/test_hermes_bridge.py`, `docs/research/hermes-protocol.md` | A07–A10; consumes actual Hermes protocol, produces validated bridge. Run: `python -m pytest experiments/test_hermes_bridge.py`; record live trace separately.
- [ ] [coding] RD2 canvas | `experiments/editor/**`, `docs/research/graph-editor.md` | Diamond/cycle/round-trip. Run: pinned TypeScript/UI checks; write exact command in tasks.md before execution.

Research scopes are disjoint. Coordinator consolidates decisions and prevents RD2 changing R04/R05.

### Wave 1: One Contract/Bootstrap Owner

- [ ] [coding] Schema/skeleton | `backend/app/contracts/**`, `backend/app/main.py`, `backend/pyproject.toml`, `backend/uv.lock`, `frontend/package.json`, frontend lockfile, `frontend/src/contracts/**`, `Makefile`, `docs/api.md` | R01–R10; outputs JSON Schema/TS/error/continuation contracts. Run: `make lint` and schema contract tests.
- [ ] [sa] Review contracts/recovery | `sa-review.md` | SCC initialization, identity, side effects, terminal states; consumes design, produces concrete findings. Run: `[skip-verify]` — documented A05–A10 analysis without runtime PASS claim.

### Wave 2: Independent Modules on Frozen Contracts

- [ ] [coding] Runtime/state | `backend/app/runtime/**`, `backend/app/storage/**`, `backend/tests/runtime/**`, `backend/tests/storage/**` | A03–A06/A09/A10/A14/A16; DAG/barriers/checkpoints/events. Run: `make test-runtime` (implement real target).
- [ ] [coding] GraphRepository/API | `backend/app/graphs/**`, `backend/app/api/graphs.py`, `backend/tests/graphs/**`, `examples/**` | A04/A12/A13; files/revision/publication/validation. Run: `make test-graphs`.
- [ ] [coding] OllamaAdapter/ToolBridge | `backend/app/providers/**`, `backend/app/tools/**`, `backend/tests/providers/**`, `backend/tests/tools/**` | A02/A07–A11; consumes G1 checkpoint interface, produces adapters. Run: `make test-contract`.
- [ ] [coding] UI | `frontend/src/editor/**`, `frontend/src/runs/**`, `frontend/src/api/**`, component tests | A12/A13; mock API first, integration later. Run: frontend typecheck/test/build.
- [ ] [devops] Delivery skeleton | `compose.yaml`, `.env.example`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `.github/workflows/ci.yml`, `docs/runbook.md` | R10; SSE/volume/loopback, consumes G1 ports. Run: `docker compose config`, build, local health smoke.

Route dependency/lockfile changes to one bootstrap owner, apply sequentially. That owner adds Makefile targets. Test scopes must not overlap.

### Wave 3: Integration

- [ ] [coding] Public API orchestration | `backend/app/api/chat.py`, `backend/app/api/runs.py`, `backend/app/api/models.py`, `backend/app/main.py`, `backend/tests/api/**` | A01/A07–A11/A14; runtime survives requests, publication snapshots. Run: `make test`, `make test-contract`.
- [ ] [coding] UI bootstrap/E2E | `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/e2e/**`, `frontend/playwright.config.ts` | A12/A13; real backend. Run: `make test-e2e`.
- [ ] [devops] Live smoke/docs | `scripts/smoke_hermes.py`, `scripts/smoke_compose.sh`, `docs/hermes-compatibility.md`, `docs/runbook.md`, `README.md` | A01/A07/A15; exact real versions/targets and truthful gates. Run: `make smoke-hermes`, `make smoke-compose` on target.

### Wave 4: Independent Review and Closure

Review each implemented group; G6 verifies interactions. Do not defer protocol-contract violations until UI completion.

review-agent receives group ID, spec refs, exact diff/files, evidence. One synthesizer owns verdict/review.md; analysts provide findings only. Maximum three cycles per stable group; spawning synthesizer consumes a cycle. FAIL in 1/2 permits one scoped fix wave and affected checks. FAIL in 3 means BLOCKED; never reset counters/rename groups. This development-review limit is unrelated to runtime graph loops.

Completed tasks record commands, exit codes, summary, commit/ref, open live gates. DONE requires PASS of every mandatory group, A01–A16, accurate docs. Without target access report “implemented; live validation open,” not complete acceptance.

## 13. Codex Model Selection and Team Setup

For maximum architecture/review capability: gpt-6-astra when available. Practical primary implementer: gpt-6.1-sol, the officially recommended complex-coding option at lower cost. Suggested MVP workflow: Sol with high reasoning for implementation; Astra with high for G0/G1 and continuation review if available. This is a workflow recommendation, not a guarantee based on model name.

The sample uses provider-specific IDs such as openai.gpt-5.6-sol and openai.gpt-5.6-terra; public config omits private provider settings. Do not copy IDs into standard ChatGPT-auth without validation. Check /model, assign compatible IDs to main thread and .codex/agents/*.toml, verify discovery. Never automatically replace credentials/provider. Verify availability/capabilities at installation.

Use $team-spec-workflow after installation. Review hooks/rules/MCP/config using README/SECURITY; create git project; install plugin from repository marketplace according to README; transfer reviewed project agents separately; start a new Codex session. Role agents are not ordinary plugin files. Do not clone the entire sample over an existing project and overwrite AGENTS.md/config.

## 14. Codex Launch Prompt

Place this file at the target project root, install and verify the team configuration, then paste the following into Codex. Required filename: Cognitive_Graph_MVP_Codex_Team.md.

```text
Use the Codex Agent Team workflow from aws-samples/sample-codex-agent-team.
Read Cognitive_Graph_MVP_Codex_Team.md completely. It is the authoritative
MVP handoff. Preserve approved requirements R01–R11; do not expand scope.

Use $team-spec-workflow. Extract requirements.md, spec.md, design.md,
tasks.md and initialize decisions.md/review.md in
.codex/specs/cognitive-graph-mvp/. Preserve durable artifacts in git.
Keep one authoritative decision location and use stable task group IDs G0–G6.

Use the main thread or fullstack-agent as development coordinator.
Verify installed role agents and available model IDs before delegating.
Run G0 research first: real Hermes tool continuation and a small graph-editor
comparison. Pin source/dependency versions and record evidence. An unproven
Hermes bridge is a blocker, not permission to remove tools from the MVP.

Then freeze shared contracts in G1. Implement the dependency-ready waves
using coding-agent and devops-agent with explicit, file-disjoint ownership.
For every worker provide role, group ID, spec refs, exact writable files,
no-edit boundary, produced/consumed contracts, acceptance tests and commands.
Use only as many workers as there are independent scopes. One owner edits
bootstrap, schemas and lockfiles. Do not add AWS dependencies to this local app.

Build the FastAPI/React proxy and UI, file-backed versioned graphs, deterministic
fan-in and seeded feedback cycles, resumable Hermes tool bridge, run history,
and Docker Compose for Windows/WSL2 with external Ollama.
Tool execution remains in Hermes. Use one configured local model per graph.
Do not conflate graph loops with the development team's review-cycle budget.

Run independent review-agent PASS/FAIL for each required group, respecting
its persistent maximum three-cycle budget. Keep evidence and blockers.
Run meaningful fake-provider/contract/UI tests and real Hermes/Ollama/WSL2
smoke when available. Never report live PASS from static checks alone.
Proceed autonomously within this specification; ask only for material product
changes or information genuinely unavailable from code/environment.
Return implemented behavior, verification evidence, setup/run commands,
and precise remaining blockers. Do not publish/deploy cloud infrastructure.
```

## 15. Sources and Confidence Boundaries

Sources examined for the original specification on October 3, 2026:

- Team README: https://github.com/aws-samples/sample-codex-agent-team/blob/main/README.md
- Templates: https://github.com/aws-samples/sample-codex-agent-team/tree/main/docs/specs/templates
- Workflow: https://github.com/aws-samples/sample-codex-agent-team/blob/main/plugins/codex-agent-team/skills/team-spec-workflow/SKILL.md
- Hermes: https://github.com/NousResearch/hermes-agent/blob/main/run_agent.py — custom base_url, chat_completions and tool-ID handling exist; transparent graph continuation still requires RD1.
- Ollama: https://docs.ollama.com/api/openai-compatibility — documentation does not replace testing a specific model/version.
- React Flow: https://reactflow.dev/learn
- Rete.js: https://retejs.org/docs/
- Codex models: https://learn.chatgpt.com/docs/models
- Model selection: https://developers.openai.com/api/docs/guides/model-selection

Loop architecture, namespaces, format, limits, storage, task decomposition are design decisions in this specification, not advertised library capabilities. Performance, live Hermes compatibility, and final editor selection remain unvalidated until research tasks finish.

