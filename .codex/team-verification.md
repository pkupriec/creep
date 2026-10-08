# Team setup verification

Setup scope only; no product requirements or implementation tasks.

## Stable setup review group

- Group: `G-TEAM-SETUP`
- Reviews consumed: **3 of 3**, all completed. Final verdict **PASS**; no fourth cycle under this workflow.
- Cycle 1: read-only independent review of configuration, plugin discovery, scope preservation and security boundaries. Parent records returned evidence here; reviewer may edit no files.
- Retries/replacement synthesizers consume the next cycle. Never reset this counter across sessions, waves or renamed review files. Cycle 3 non-PASS is terminal.
- One smoke explorer may inspect structure. No agent may edit product or setup files during the smoke test.

## Cycle 1 result: PASS

Fresh Codex 0.160.0 CLI session `01a102d8-c5b6-7ba0-b1d5-60185bf8a878`, using the existing ChatGPT authentication and provider, ran with the stricter read-only sandbox. No setup/product files were edited by any smoke participant.

- Actual custom-role schema exposed all five roles and their selected model/reasoning values.
- `structure-smoke`: custom `coding-agent`, thread `01a102d9-6cf1-7531-8d11-ab7bd561b1ff`, completed with PASS. No product files, product requirements or implementation tasks exist.
- `setup-review`: custom `review-agent`, thread `01a102d9-bd10-77c3-a240-0749d61d020b`, completed with independent PASS. No Critical/Severe/High findings or failed checks.
- Local session turn contexts show the coordinator and structure agent using `gpt-6.1-sol` / `high`, and the independent reviewer using `gpt-6-astra` / `high`. Accepted spawns selected `agent_type` explicitly without model overrides. This is client execution evidence, not backend identity attestation.
- `python -B .codex/verify-team.py`: exit 0, static PASS, independently rerun by both workers.
- All 16 workflow plugin files matched the installed cache by SHA256 during review.
- All six workflow skills were present in the actual model-visible session catalog.
- Final lifecycle check: both workers completed; no required worker remained active. This client exposes no close API, so no session-closure claim is made.

The configured three-child concurrency limit and depth-one limit were validated by strict config loading; their maximum-capacity rejection behavior was not stress-tested. Architecture and DevOps roles were discovered but were not separately executed. Product runtime testing awaits the specification.

## Post-review metadata maintenance

Removed a fourth default prompt ignored by this client (maximum three), removed an obsolete ARN placeholder in the spec template, and refreshed the plugin version to `0.1.0-creep.2`. No role behavior or ownership/review rules changed. Static parsing, strict config loading, plugin/skill discovery and cache comparison were rerun afterward. No second synthesizer was spawned; the persistent counter remains **1 of 3**.

## Cycle 2: policy reconciliation

Reserved before reviewer spawn for the same `G-TEAM-SETUP` group. This is not a new budget. Current policy adaptation: `0.1.0-creep.3`, with the same reviewed upstream commit.

Required acceptance: strict project config loads with user approval routing and disabled unnecessary MCP/Apps connectors; no enabled latest dependency; repository installation and baseline pin retained; review acceptance and hard three-cycle budgets agree; excluded fetch patterns do not affect LLM inference/tool execution/state changes; models, concurrency, global configuration, credentials and product scope preserved. Configuration-level enforcement is required; capacity stress testing and server identity attestation remain optional/out of scope.

Independent reviewer had no writable files. Cycle 2 returned **FAIL**, with no Critical/Severe/High defect: its nested app-server probe ran under `CodexSandboxOffline`, which had no project trust and skipped the project layer. Static verification, .3 source/cache equality, model/concurrency preservation, baseline, bulk-fetch exclusions and the four review pressure cases passed. Reviewer thread `01a102e4-3e82-7b43-9a77-a23a3f7bc044` completed; no required worker remains active from cycle 2.

## Cycle 3: final host-policy evidence review

The same group consumes its final cycle; no fourth cycle is permitted. Required policy behavior remains unchanged. The evidence fix captures strict client configuration loading under the existing trusted desktop user, instead of the isolated review account. No project trust is added to the sandbox and no approval control is bypassed.

`.codex/tool-policy-evidence.json` records the installed client's config/read result, project origins, plugin/skill discovery and source hashes, filtered to relevant non-secret fields. It is host execution evidence for the original required configuration-level gate; acceptance was not made optional. The read-only reviewer reconciled its hashes and policy values with current source and returned the final verdict below.

### Cycle 3 result: PASS

Coordinator session `01a102eb-6dcb-7a40-9fdc-c9cb1a59dfc7` spawned exactly one custom `review-agent`, thread `01a102ec-472f-7592-a0f1-0a0ec87fcf71`. The reviewer returned independent PASS and reached verified terminal completed status. No findings or required evidence gaps remained.

- `python -B .codex/verify-team.py`: exit 0.
- Two independent read-only Python assertion runs: exit 0; all 23 captured source SHA256s, 16 plugin/cache files, 11 project origins and unchanged global-config hash matched.
- Captured trusted-host strict config/read, plugin/list and skills/list evidence matched current source: on-request/user approvals, prompt app/MCP modes, Apps/playwright/node_repl disabled, Playwright pinned to cached 0.0.70, models/concurrency/depth preserved, plugin .3 and six enabled discovered skills.
- Missing required verification means FAIL; optional warnings with complete required checks may PASS; interrupted synthesizers consume their cycle; renaming cannot reset exhaustion. No fourth-cycle exception remains in workflow rules.
- The effective-policy gate passed without changing trust. This read-only CLI session's never override differs from the recorded trusted-host project policy and does not invalidate that host evidence.
- No reviewer edits, nested delegation, installs, commits, deployment or product work. No required worker remains active. No close API exists, so no session-closure claim is made.

The setup group's budget is now exhausted at 3/3. Product runtime, capacity stress tests and backend model identity attestation remain outside this configuration-only scope. Fresh desktop chats must load the project policy; existing sessions can retain earlier tool/permission snapshots or explicit overrides.
