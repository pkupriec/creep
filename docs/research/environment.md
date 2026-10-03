# G0 environment evidence

Owner: `devops_env` (DevOps), Wave 0. Recorded 2026-10-03, Europe/Kiev.
Scope: R10 and A15 prerequisites; read-only discovery, not product delivery acceptance.
Authority: root `AGENTS.md`, entire `Cognitive_Graph_MVP_Codex_Team.md` v1.1,
and `.codex/specs/cognitive-graph-mvp/{requirements,spec,design,tasks,decisions}.md`.
Workflows: installed `team-spec-workflow` and `team-documentation`,
`codex-agent-team` `0.1.0-creep.3`. No ancestor AGENTS.md was present at
`D:/AGENTS.md` or `D:/Sources/AGENTS.md`; the repository inventory found only root guidance.

## Result and boundaries

Windows and Ubuntu WSL2 can query external Ollama at loopback port 11434.
Its HTTP version is `0.33.3` and its inventory advertises installed models with
native function tools. These metadata checks do not prove inference, generated
tool calls, JSON Schema control output, streaming, or Hermes continuation.
RD1 owns the actual protocol experiment and selected inference test model.

Docker Desktop and Compose are usable from Windows and Ubuntu. A future owned
backend container must still prove connectivity to the configured upstream.
`host.docker.internal` currently resolves in Ubuntu to `192.168.50.186` but
cannot connect to port 11434; Ubuntu loopback and its current Windows gateway
`172.26.144.1` work. Do not infer container DNS behavior from either host.

An existing, unrelated container named `ollama` publishes port 11434. It remains
external to this project's future Compose file and was not started, stopped,
changed, attached to another network, or used as an application-owned service.
No containers were created, images pulled, models downloaded, secrets read,
global packages installed, or configuration changed. No inference requests were
sent by this worker. No external writes occurred.

## Exact observed versions

Each row was executed independently. Commands run in PowerShell from
`D:/Sources/creep`; `wsl -d Ubuntu -- ...` executes the specified Linux command.
For failed native commands, explicit `exit $LASTEXITCODE` preserves the native
code. Initial grouped discovery output was not used to attribute independent
success to its component commands.

| Exact command | Exit | Evidence |
| --- | ---: | --- |
| `python --version` | 0 | Windows Python `3.11.15` |
| `node --version` | 0 | Windows Node `v24.14.0` |
| `npm --version` | 0 | Windows npm `11.9.0` |
| `uv --version` | 0 | `0.11.28`, build `ebf0f43d7`, 2026-07-07, x86_64-pc-windows-msvc |
| `& C:/Users/pkupr/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe --version` | 0 | Hermes venv Python `3.11.15` |
| `docker context show` | 0 | `desktop-linux` |
| `docker context inspect --format '{{json .Endpoints.docker.Host}}'` | 0 | `npipe:////./pipe/dockerDesktopLinuxEngine` |
| `docker version --format '{{.Client.Version}} {{.Server.Version}} {{.Server.Platform.Name}}'` | 0 | Client/server `28.3.2`; Docker Desktop `4.43.2 (199162)` |
| `docker compose version` | 0 | `v2.38.2-desktop.1` |
| `wsl --version` | 0 | WSL `2.7.8.0`; kernel `6.18.33.1-1`; Windows `10.0.26200.9457` |
| `wsl --list --verbose` | 0 | `Ubuntu` and `docker-desktop` Running, version 2 |
| `wsl -d Ubuntu -- python3 --version` | 0 | Python `3.12.3` |
| `wsl -d Ubuntu -- node --version; exit $LASTEXITCODE` | 127 | Node not installed in Ubuntu; Windows frontend tooling is available |
| `wsl -d Ubuntu -- docker version --format '{{.Server.Version}}'` | 0 | Docker server `28.3.2` |
| `wsl -d Ubuntu -- docker compose version` | 0 | Compose `v2.38.2-desktop.1` |
| `wsl -d Ubuntu -- wslpath -u D:/Sources/creep; exit $LASTEXITCODE` | 0 | `/mnt/d/Sources/creep` |
| `wsl -d Ubuntu -- bash -lc 'test -f /mnt/d/Sources/creep/AGENTS.md && printf "%s\n" /mnt/d/Sources/creep'; exit $LASTEXITCODE` | 0 | Repository accessible through mounted drive |

The Windows `py` launcher was absent in initial discovery. It is unnecessary
when using an explicit interpreter. An initial backslash-form `wslpath` probe
failed because the Linux shell removed backslashes; the independently checked
forward-slash form above is the reproducible command.

## Ollama addresses and HTTP evidence

Bounded GETs use a 3-second connect timeout and 8-second overall timeout.
Version and model inventory are read-only; no token or Hermes environment file
is needed. The OpenAI base URL omits `/api`: use `/v1` for the provider.

| Exact command | Exit | Result |
| --- | ---: | --- |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://127.0.0.1:11434/api/version` | 0 | `{"version":"0.33.3"}` |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://127.0.0.1:11434/api/tags` | 0 | Installed model inventory, including capabilities/digests |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://127.0.0.1:11434/v1/models` | 0 | OpenAI `list`, 27 physical model IDs |
| `wsl -d Ubuntu -- curl --silent --show-error --connect-timeout 3 --max-time 8 --fail http://localhost:11434/api/version` | 0 | `0.33.3` |
| `wsl -d Ubuntu -- curl --silent --show-error --connect-timeout 3 --max-time 8 --fail http://172.26.144.1:11434/api/version` | 0 | `0.33.3`; current gateway, not a stable default |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://host.docker.internal:11434/api/version; exit $LASTEXITCODE` | 28 | Connection timeout at about 3 seconds |
| `wsl -d Ubuntu -- curl --silent --show-error --connect-timeout 3 --max-time 8 --fail http://host.docker.internal:11434/api/version; exit $LASTEXITCODE` | 7 | Cannot connect |
| `wsl -d Ubuntu -- bash -lc 'ip -4 route show default; getent hosts host.docker.internal'` | 0 | Gateway `172.26.144.1`; alias `192.168.50.186` |

Compact model metadata was also read with the independently successful command:

```powershell
$ErrorActionPreference='Stop'
$r=Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags -TimeoutSec 8
$r.models | Select-Object name,digest,size,capabilities | ConvertTo-Json -Depth 5
```

Selected available candidates for RD1, not a product hardcoded model:

| Installed ID | Immutable observed digest | Advertised capabilities | File bytes |
| --- | --- | --- | ---: |
| `gemma4:12b` | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` | completion, tools, thinking, vision | 7556508396 |
| `gpt-oss:20b` | `17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7` | completion, tools, thinking | 13793441244 |
| `qwen3.8:27b` | `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` | completion, tools, thinking, vision | 17741872154 |
| `qwen3-coder:30b-a3b-q4_K_M` | `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca` | completion, tools | 18556700761 |
| `qwen3:32b` | `030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840` | completion, tools, thinking | 20201253829 |

For example, the installed `qwen3.8:27b-q6_k` advertises only completion/vision,
so its similar model name is insufficient evidence of native tool support.
Graph creation must select an installed ID and separately verify required
capabilities. Tags are mutable; repeat inventory and record digest at smoke time.

Existing external resource identity, inspected without environment fields:

```powershell
docker inspect ollama --format '{{.Id}} {{.Config.Image}} {{.Image}} {{json .NetworkSettings.Ports}}'
docker image inspect ollama/ollama:latest --format '{{.Id}} {{json .RepoDigests}}'
```

Both exit 0. Container ID
`7d26cf9986a2d29fb38359de2565c3d2cb511ccf4781387c8ab317a4374e663e`,
existing image digest `ollama/ollama@sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2`.
Port metadata advertises `0.0.0.0:11434` and `[::]:11434`. This is evidence
about an existing user service, not an image choice for this project or proof
that all HTTP addresses necessarily route to that container.

`Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in 8000,8080,11434 } | Select-Object LocalAddress,LocalPort,OwningProcess`
exited 0 and listed only port 11434 listeners. Ports 8000/8080 were free at
probe time; recheck immediately before the owned delivery smoke.

## Hermes revision and dirty-state qualification

```powershell
git -C C:/Users/pkupr/AppData/Local/hermes/hermes-agent rev-parse HEAD
& C:/Users/pkupr/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -c 'import importlib.metadata as m; print(m.version("hermes-agent"))'
git -C C:/Users/pkupr/AppData/Local/hermes/hermes-agent status --short -- run_agent.py agent/transports/chat_completions.py trajectory_compressor.py pyproject.toml setup.py; exit $LASTEXITCODE
git -C C:/Users/pkupr/AppData/Local/hermes/hermes-agent diff --numstat -- run_agent.py agent/transports/chat_completions.py trajectory_compressor.py pyproject.toml setup.py
git -C C:/Users/pkupr/AppData/Local/hermes/hermes-agent diff --ignore-space-at-eol --numstat -- trajectory_compressor.py; exit $LASTEXITCODE
```

All exit 0. SHA `caed552de1c8a8f9983bc555512412a1ac0e0a9e`; installed
package metadata `0.18.2`. The full checkout has extensive local differences;
it was not changed or cleaned. Of the targeted files, only
`trajectory_compressor.py` was dirty (`1574/1574` raw numstat). Ignoring
end-of-line whitespace yielded no difference, consistent with line-ending
conversion rather than changed compression logic. RD1 still owns interpretation
and proof of actual transport/compressor behavior.

`Get-FileHash <the three paths below> -Algorithm SHA256 | Format-Table -AutoSize`
exited 0 and yielded:

| File relative to installed Hermes | Current SHA256 |
| --- | --- |
| `run_agent.py` | `2D0592E65218BC90AB6F8152DA41A666B513DB1666815E175102F8E4A11DFD36` |
| `agent/transports/chat_completions.py` | `D892982129B44096737859525BEC04E491666A0E24241C337567D4077D7848EA` |
| `trajectory_compressor.py` | `A61FCD01503B68878BA6A3B86B577586EF2489CD696A26258339E26409E175AC` |

The exact hash command used full paths under
`C:/Users/pkupr/AppData/Local/hermes/hermes-agent/` for those three files.

## Open delivery gates and later runnable procedure

G0 environment discovery is complete. It does not close G0/RD1 or A15.
There is no unknown Ollama URL/model inventory blocking the research worker.
Required future evidence remains:

1. RD1 must prove actual Hermes continuation plus real model tools/control JSON
   and streaming at the recorded SHA/file state. Manual UI tool results do not
   substitute for Hermes.
2. G5 must validate the eventual pinned Compose config, image builds, non-root
   volume permissions, graceful shutdown, SSE reverse proxy, and upstream
   connectivity from an owned application container.
3. G6/A15 must launch the exact project from both Windows and WSL2, verify UI/API
   and real Hermes smoke, restart, prove immutable history persists, and clean
   only owned smoke resources while retaining application data.

After G1 defines and G5 implements `compose.yaml`, these are the intended
commands, **not executed in Wave 0**:

```powershell
Set-Location D:/Sources/creep
docker context show
docker --context desktop-linux compose -p cognitive-graph-mvp -f compose.yaml config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Compose validation failed' }
docker --context desktop-linux compose -p cognitive-graph-mvp -f compose.yaml build
if ($LASTEXITCODE -ne 0) { throw 'Compose build failed' }
```

Runtime startup requires a delivery handoff with the exact project name,
files/profiles, loopback ports, volumes and smoke target asserted first.
The specification's launch command is `docker compose up --build -d` from WSL2;
the implementation runbook must make project/context/file selection explicit
and preserve caller-provided values. WSL path is `/mnt/d/Sources/creep`.
`OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` is still the specification
default for Docker Desktop, pending a real application-container probe.
If that fails, record the concrete safe reachable route before changing any
default; a Windows gateway derived today is not a reproducible universal URL.

The future runbook must exercise `/health/live`, `/health/ready`, `/v1/models`,
SSE through port 8080, `make smoke-hermes`, and `make smoke-compose` using real
implemented targets. No smoke scripts exist yet, so no placeholder command is
presented as executed. Never use broad prune or `down -v`: the latter deletes
graph/history data. Independently verify residue after an authorized teardown.

Residual risks: mutable external model tags, external server availability,
host/container addressing differences, and future filesystem permissions are
unproven until their corresponding live checks. Ubuntu's missing Node is not a
Compose blocker because frontend builds will run in the pinned builder image;
Windows Node/npm are available for the current local editor experiment.
