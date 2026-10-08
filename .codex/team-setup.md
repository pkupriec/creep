# Codex Agent Team setup

Setup completed on 2026-10-03; project policy tightened afterward at the user's request. Product specification and implementation are pending.

## Environment and preservation

- Root: `D:/Sources/creep`; Windows 11 Pro, version 10.0.26200.
- Existing Codex CLI: `0.160.0`; desktop runtime reports `26.930.31730`. No second Codex copy installed.
- Existing ChatGPT login, default OpenAI provider and global configuration preserved. No credential values read or copied. The external Ollama server is an application dependency, not the Codex provider.
- Global config SHA256 before/final verification: `5fcf7a1f0bba8a5405617a1a7b02cba0bb431090be0a5557712dbc2c66b23a3e`.
- Existing project trust was already `trusted`; no trust or sandbox policy changed. Project approval policy now uses on-request with the user as reviewer; automatic approval review is disabled for future project sessions.
- Existing Git repository: unborn `main`, no commits, clean empty working directory before setup. Existing `origin` retained. No commit, branch switch, staging, push or history rewrite performed.
- No existing project or ancestor AGENTS.md files or product configuration were found. AGENTS.md was added rather than replacing instructions.
- Python 3.11.15 and existing PyYAML 6.0.3 available; no dependencies installed. Docker 28.3.2 / Compose v2.38.2-desktop.1 available. Ubuntu and docker-desktop are running WSL2 distributions.

## Source and installed scope

Upstream: [aws-samples/sample-codex-agent-team](https://github.com/aws-samples/sample-codex-agent-team), commit `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`. Full clone remains outside the product repository in a temporary directory. `team-source.json` records provenance and source hashes.

Reviewed README installation guidance, SECURITY.md, custom roles, plugin manifest, workflow skills, commands, rules and both logging hooks. Installed only the adapted local workflow configuration, relevant templates and safety rules. No sample application, unrelated documentation, AWS plugin/MCP/cloud configuration or credentials were copied.

The repository marketplace `.agents/plugins/marketplace.json` exposes `codex-agent-team@creep-local`. Trusted project `.codex/config.toml` enables it. This client supports repository discovery and automatic cache materialization: `skills/list` with project cwd installed/refreshed the plugin, and subsequent `plugin/list` returned installed=true/enabled=true. The maintained source is `.codex/plugins/codex-agent-team`; the generated client cache is outside the project. No global marketplace registration or global enablement was required. Plain CLI `plugin list` does not pass repository cwds and is not the verification authority for this repo marketplace.

Included skills: team-brainstorm, team-spec-workflow, team-coordination, team-review-cycle, team-documentation, git-workflow. Optional setup auditing, AWS guidance, bulk product-fetch patterns and third-party skills/MCPs were omitted. Native project tests and diagnosis replace optional companion workflows.

Logging hooks were omitted: they are optional metadata logging, use POSIX shell paths, and subagent logging imports fcntl. No hooks are required for coordination or the durable review counter. No hook trust bypass was used.

## Roles, models and workflow

| Position / role | Model | Reasoning |
| --- | --- | --- |
| Main coordinator | gpt-6.1-sol | high |
| fullstack-agent | gpt-6.1-sol | high |
| coding-agent | gpt-6.1-sol | high |
| devops-agent | gpt-6.1-sol | high |
| review-agent | gpt-6-astra | high |
| sa-agent | gpt-6-astra | high |

The authenticated `codex debug models` catalog advertises both IDs and high reasoning. A fresh CLI execution successfully used both models in the smoke test. The main thread remains coordinator; fullstack-agent is available when an explicit lead profile or spawn plan is useful. SA is adapted to local application architecture and external Ollama rather than AWS.

Concurrency: at most three spawned agents plus the primary coordinator; max_depth=1. Per-role ceilings are coding=2, DevOps=1, review=3, SA=1, subject to the total cap. File-disjoint writes, one shared-file owner, independent review, stable task-group IDs and non-resetting maximum three-cycle review budgets are preserved. Cycle consumption is recorded before synthesizer spawn; replacements/interrupted retries count. Cycle 3 non-PASS is terminal for the affected group.

After specification, durable versionable files go in `.codex/specs/<feature-slug>/`: requirements, spec, design, tasks, decisions, review evidence and optional architecture review. Only blank templates exist now.

## Verification and limits

- `python -B .codex/verify-team.py`: exit 0; TOML/JSON, matrix, references, rules and scope validated.
- Existing PyYAML parsed all six skill frontmatter blocks and six discovery metadata files successfully.
- Installed CLI app-server with `--strict-config`: initialization and `config/read` succeeded with the project model, concurrency/depth and enablement values.
- `plugin/list` with project cwd: adapted plugin installed and enabled.
- `skills/list` with forceReload and project cwd: all six plugin skills discovered and enabled without duplicates.
- Installed plugin files matched source by SHA256; refresh was performed through the supported client discovery mechanism.
- Fresh read-only CLI custom-role smoke: structure check PASS, independent setup review PASS, both completed. Details and persistent review counter are in `team-verification.md`.
- No application, Docker deployment or external Ollama runtime test was attempted. Those require the specification and endpoint details.
- Maximum concurrency/depth rejection was not stress-tested. Three other roles were discovered but not separately executed.
- Inherited Apps MCP startup errors and an unrelated malformed user skill produced warnings in the standalone CLI. They did not prevent the team smoke test. Unrelated global configuration/files were left untouched.

## User-requested policy reconciliation

- Baseline remains `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`. Newer upstream revisions require a recorded diff review before use.
- Project-only MCP overrides disable inherited Playwright and node_repl. Apps connectors are disabled for this local workflow; app and MCP approval defaults are prompt, with user approval routing. The global configuration is preserved.
- Disabled Playwright is pinned to the already cached package `@playwright/mcp@0.0.70`; no dependency was downloaded or enabled. No active workflow dependency uses latest.
- PASS now requires no severe findings and complete passing required acceptance/verification/reviewer evidence. Missing required evidence means FAIL independently of severity; optional warnings may remain on PASS. The hard maximum is three synthesizer spawns per stable group, with no fourth-cycle exception in workflow instructions.
- Bulk-fetch defaults are explicitly excluded from LLM inference, tool execution and state-changing requests. Team concurrency remains three children plus coordinator, depth one; it does not authorize inference fan-out or response persistence.
- Cycle 2 returned FAIL for a missing host-policy gate: nested CLI probes ran in the untrusted CodexSandboxOffline account. Cycle 3 reviews actual trusted-host client evidence, without modifying sandbox trust. The group's counter is not reset. Details are in team-verification.md and tool-policy-evidence.json.
- Running sessions may retain their original permission/tool snapshot or explicit CLI overrides. Open a new project chat to load these settings; configuration changes do not retroactively disable currently exposed tools.
- Final independent cycle 3 returned PASS. All 23 policy-source hashes, 16 installed plugin files, 11 project origins and the unchanged global config hash were independently verified. No required configuration evidence gap remains; the setup review budget is exhausted at 3/3. Product implementation still awaits the specification.

## Remaining user action

Open a **new chat in this project** so the desktop session loads the installed team roles and skills. No trust confirmation is currently needed. A full app restart is not required by the fresh-client results; restart once only if the new desktop chat does not expose the team. This existing chat's original tool/skill catalog has not been claimed to hot-reload.

Suggested specification prompt:

> Use the Codex Agent Team to plan this specification in .codex/specs/<slug>/. Wait for my approval before implementation: [specification]

## Files added

- `AGENTS.md`, `.gitignore`
- `.agents/plugins/marketplace.json`
- `.codex/config.toml`
- `.codex/agents/{fullstack-agent,coding-agent,devops-agent,review-agent,sa-agent}.toml`
- `.codex/plugins/codex-agent-team/.codex-plugin/plugin.json`, `LICENSE`, two command shortcuts and six skills with discovery metadata
- `.codex/rules/codex-agent-team.rules`
- `.codex/specs/README.md` and seven templates (requirements, spec, design, tasks, decisions, review, sa-review)
- `.codex/team-source.json`, `.codex/team-setup.md`, `.codex/team-verification.md`, `.codex/tool-policy-evidence.json`, `.codex/verify-team.py`

All additions are untracked and ready for later Git review/versioning. Nothing was committed.

Configuration references: [official custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), [official repo-plugin packaging and enablement](https://developers.openai.com/plugins/build/plugins), and [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference). Installed-client schema and execution results were used to verify compatibility.
