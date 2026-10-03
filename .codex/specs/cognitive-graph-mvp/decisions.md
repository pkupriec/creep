# Cognitive Graph MVP decisions and blockers

## 2026-10-03 — initialization and team preservation

- User authorized implementation, team delegation, local tests/reversible setup, and Git versioning of these artifacts. No external writes, pushes, cloud deployment, secret access or data deletion authorized.
- Full root specification v1.1 and AGENTS.md read before product work. Approved sections extracted verbatim; no acceptance weakened.
- `python .codex/verify-team.py`: exit 0, static PASS. All 16 maintained plugin files match installed `0.1.0-creep.3` cache by SHA256; no reinstall/update performed. Upstream baseline remains `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`.
- Custom roles are explicitly exposed by this client's spawn schema. Configured matrix: main/fullstack/coding/devops `gpt-6.1-sol` high; review/SA `gpt-6-astra` high. Spawns select custom role without model overrides.
- Session mismatch: danger-full-access and never approval plus exposed external connectors differ from on-request/user and disabled connector project configuration. No config/trust/authentication changes; workflow uses local tools and honors user approval boundaries.
- Existing repository is unborn main; all setup/spec files initially untracked. Preserve all existing files; commit only newly created durable specification/research artifacts when ready, as explicitly requested.
- Installed Hermes source SHA discovered: `caed552de1c8a8f9983bc555512412a1ac0e0a9e`. G0 must verify source state and actual protocol. Docker Engine responds with 28.3.2; Ubuntu/docker-desktop are running WSL2. No live acceptance inferred.
- G0 research gates remain OPEN. G1–G6 wait on proven RD1/RD2. Unknown external Ollama details are investigated without reading credentials.
