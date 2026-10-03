# Cognitive Graph MVP — design

Authority: Cognitive_Graph_MVP_Codex_Team.md v1.1, 2026-10-03.
Sections below are preserved verbatim. No research gate is closed by extraction.

## 9. Architecture and Deployment

FastAPI components: GraphRepository, Validator, GraphRuntime, OllamaAdapter, ToolBridge, RunRepository, EventBus. The HTTP layer does not own execution: runtime survives individual requests. Asyncio scheduler plus SQLite WAL suffices; Redis/Celery/Kafka are unnecessary. Keep checkpoint/event/mapping transactions short; never hold a DB transaction during LLM/HTTP calls.

Entities: runs (snapshot/context/status/budgets), activations (node/loop/iteration/messages/payload), pending_tools (mapping/status/result), events (run_id/event_id/type/payload), response_cache (continuation hash/response). Persist events before SSE publication. Enforce idempotency through unique constraints, not only in-memory dictionaries. Use one backend worker; multiple Uvicorn workers are prohibited until an interprocess scheduler exists.

Layout: backend/app/contracts, graphs, runtime, providers, tools, storage, api; backend/tests; frontend/src; examples; docs; scripts; compose.yaml; Dockerfiles/lockfiles. One owner creates shared contracts/bootstrap; others import them. Do not manually duplicate frontend/backend schemas without consistency checks.

Compose services: backend and frontend (production static build, reverse proxy for /api and /v1); named volume cg_data:/data. Ollama remains external; no GPU passthrough is required. UI: 127.0.0.1:8080; API: 127.0.0.1:8000. Disable SSE buffering and set proxy timeouts above the active-run budget. Validate host.docker.internal on Docker Desktop. For native Docker Engine in WSL2, document host-gateway and actual reachability of Windows Ollama; do not assume these paths are interchangeable.

Start from WSL2: `docker compose up --build -d`. Prerequisites: Docker Desktop with WSL2 integration or separate Docker Engine, pinned dependencies, installed tool-capable Ollama model. readiness reports upstream connectivity clearly. Runbook covers safe container access to Ollama, volume persistence across down, SQLite/graph backups. Identify down -v explicitly as data deletion.

Local security: localhost binding, same-origin UI, HTTP/JSON size limits, bounded queues/concurrency, no arbitrary eval/path traversal, environment tokens excluded from graph files, sanitized logs. If LAN access is introduced, document mandatory auth/TLS; it is outside default deployment.


## 11. Required R&D Before Main Implementation

### RD1 — Hermes Tool Continuation

On a pinned Hermes revision inspect custom-provider/chat_completions routing, session/history, tool-ID normalization, maximum tool iterations, timeouts, streaming, compressor. Prototype two nodes, one tool round, final response; then two tool-capable nodes, replay, restart. Capture actual request/response traces without secrets. Verify Hermes does not treat the first tool response as completed work and that a full graph fits client iteration/time limits. Record exact setup and minimum Ollama model capabilities.

Deliver docs/research/hermes-protocol.md, reproducible test, decision in decisions.md. Unproven transparent compatibility makes G0 BLOCKED; do not build the main implementation on an unvalidated bridge. Discuss restricted compatibility profile or explicit Hermes adapter if necessary; never silently change requirements.

### RD2 — Existing Graph Editor

Compare React Flow (@xyflow/react) and Rete.js in a small React prototype. React Flow is the initial simplicity candidate, not a completed decision. Demonstrate diamond, multiple ports, feedback arc, loop membership/seed, prompt edit, JSON round-trip. Frontend execution engines must not define backend scheduler semantics.

Criteria: open-project-compatible license, sufficient OSS features, TypeScript/React, custom nodes/handles, serializable positions/edges, cycles allowed by configuration, usable loop selection, minimal integration complexity. Record versions/license/limitations and select one package. ELK/dagre only if needed; default coordinates suffice.

Deliver docs/research/graph-editor.md, short screenshot/test, selection ADR. Verify current documentation at installation and pin dependencies.

## Security Considerations

Implementation is gated on G0; these are constraints from the authoritative specification, not claims about deployed controls.

- Identity: local single user; optional CG_API_TOKEN protects both management and OpenAI API surfaces. Caller namespace derives from token without persisting its value, or one local anonymous namespace. No account system.
- Trust boundaries: browser uses same-origin reverse proxy; backend communicates only with configured external Ollama. Hermes owns tool execution and its environment. No backend shell/MCP executor, host filesystem grant, or Docker socket mount.
- Exposure: Compose binds UI/API to 127.0.0.1:8080/8000. LAN access and cloud deployment are excluded; default local HTTP does not claim TLS.
- Secrets and data: tokens are excluded from graph export, traces, logs, and snapshots. User history and tool outputs may contain sensitive local data; the SQLite volume and graph files rely on host access controls and host disk protection. No product-managed at-rest encryption claim.
- Validation: safe graph IDs, strict schemas, one provider per port, bounded requests/queues/global inference pool, no arbitrary expressions/eval or paths. Inference concurrency remains exactly the configured global semaphore; no generic disk cache or minimum concurrency applies.
- Durability: graph writes use fsync and atomic replace; immutable run snapshots, tool mappings, checkpoints and response-cache unique constraints reside in SQLite WAL. No transaction spans inference/network awaits. Restart preserves waiting IDs and marks uncertain active upstream executions interrupted.
- Side effects: tool delivery is checkpointed before response. Exact continuation replay must not repeat nodes or external actions. Cancellation prevents new work; it cannot undo or forcibly terminate a tool already running in Hermes.
- Retention and backups: configured history retention defaults to 30 days and never deletes graph files. Document consistent SQLite/graph backup and restore. Container down preserves named volume; down -v deletes data and is outside automatic verification.
- Closure evidence: A09/A10 idempotency/recovery, A13 snapshot/revision isolation, A14 late-result/cancellation/overflow handling, A16 path/token/global-concurrency tests, and A15 real Windows/WSL2 runtime evidence. All remain open until executed.

