# Delivery preflight during G1

Owner: `devops_preflight` (devops-agent). Recorded 2026-10-03, Europe/Kiev.
Scope: R10/A15 prerequisites only; G5 implementation awaits frozen G1 contracts.
Only this report was written. No Compose, Dockerfile, manifest, lockfile, source,
configuration, secret, or external service was changed. No commit was made.

Authority: entire [root specification](../../Cognitive_Graph_MVP_Codex_Team.md),
[AGENTS.md](../../AGENTS.md), durable
[tasks](../../.codex/specs/cognitive-graph-mvp/tasks.md),
[decisions](../../.codex/specs/cognitive-graph-mvp/decisions.md),
[design](../../.codex/specs/cognitive-graph-mvp/design.md), and
[environment evidence](environment.md). Installed team-spec-workflow and
team-documentation `0.1.0-creep.3` were applied. Root was the only discovered
AGENTS.md; ancestor `D:/AGENTS.md` and `D:/Sources/AGENTS.md` were absent.

## Outcome

All proposed exact image versions exist and have immutable registry digests.
Windows and Ubuntu loopback still reach external Ollama `0.33.3`. Host probes
to `host.docker.internal` still fail. A safe cached diagnostic container command
was rejected before execution by the command tool with `blocked by policy`.
The result does not identify automatic approval review as the mechanism.
Independent exact-name and owner-label inventory queries found no container.

Docker-to-Ollama reachability remains unproven; retain the specification default
`OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` pending the actual backend
container probe. A failed Windows or WSL alias probe neither proves nor disproves
Docker Desktop's container route. Do not replace the default with today's gateway
or connect the application to the user-owned Ollama container's network.

## Immutable image candidates

`coding_bootstrap` confirmed Python `3.11.15`, uv `0.11.28`, Node `24.14.0` and
npm `11.9.0`. The requested backend distro is Debian bookworm slim. The nginx
version below was resolved from the registry, not assumed from a moving tag.
These are preflight candidates for root acceptance and G5; no production image
configuration was added. Registry metadata alone does not prove image builds,
linked SQLite, installed tool versions, health, shutdown, or permissions.

| Exact registry reference | Multi-platform index digest | linux/amd64 manifest digest |
| --- | --- | --- |
| `docker.io/library/python:3.11.15-slim-bookworm` | `sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3` | `sha256:77923445c077d8eb971b14b2b114a1d9cd4a87edb4c75654820ca4832ee8cb15` |
| `docker.io/library/node:24.14.0-bookworm-slim` | `sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8` | `sha256:4bd6219054c8bebcd26a66bfd8ca0bd6e1024b4b97474c59bb7ee3bbcbef4fe8` |
| `ghcr.io/astral-sh/uv:0.11.28` | `sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa` | `sha256:5c3ab83183a73c5d319a77009eb425b60d5bb937f339fb7876788ebf567baf48` |
| `docker.io/library/nginx:1.30.5-alpine` | `sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94` | `sha256:8f84ed99befc3891b8f329c5c202785278a2cfb7c25107d57fb2a134a3117433` |

Prefer `tag@sha256:<index>` for readable immutable pins. The observed daemon is
`linux/amd64`; the platform manifests above independently identify that target.
`nginx:stable-alpine` resolved to the same index as `nginx:1.30.5-alpine`; use the
exact version plus digest rather than the moving alias in future Dockerfiles.
The index pins retain other platform entries without claiming cross-platform
runtime verification. No image layers or models were downloaded.

Executed independently from PowerShell at `D:/Sources/creep`:

| Exact command | Exit | Evidence |
| --- | ---: | --- |
| `docker context show` | 0 | `desktop-linux` |
| `docker image ls --digests --format '{{.Repository}}:{{.Tag}} {{.Digest}} {{.ID}}'` | 0 | Cached immutable Python candidate listed below |
| `docker --context desktop-linux version --format '{{.Server.Os}}/{{.Server.Arch}}'` | 0 | `linux/amd64` |
| `docker --context desktop-linux buildx imagetools inspect docker.io/library/python:3.11.15-slim-bookworm; exit $LASTEXITCODE` | 0 | Index/platform digests above; source revision `4d216ad3beb5b697c4049071c82fc375acb8abad` |
| `docker --context desktop-linux buildx imagetools inspect docker.io/library/node:24.14.0-bookworm-slim; exit $LASTEXITCODE` | 0 | Index/platform digests above; source revision `62ab97e3a124eeaa6e12aa36815f5d71d498ce29` |
| `docker --context desktop-linux buildx imagetools inspect ghcr.io/astral-sh/uv:0.11.28; exit $LASTEXITCODE` | 0 | Index/platform digests above |
| `docker --context desktop-linux buildx imagetools inspect docker.io/library/nginx:stable-alpine; exit $LASTEXITCODE` | 0 | Version annotation `1.30.5-alpine`; source revision `a16f1329e13e7273c4103f75d863ca625b75109e` |
| `docker --context desktop-linux buildx imagetools inspect docker.io/library/nginx:1.30.5-alpine --format '{{json .Manifest}}'; exit $LASTEXITCODE` | 0 | Same immutable index and amd64 manifest as stable alias |
| `docker --context desktop-linux buildx imagetools inspect docker.io/library/node:24.14.0-bookworm-slim --format '{{json .Image}}'; exit $LASTEXITCODE` | 0 | Public base-image config reports `NODE_VERSION=24.14.0`; no running-container environment inspected |
| `docker --context desktop-linux image inspect python:3.11-slim --format '{{.Id}} {{.Os}}/{{.Architecture}} {{json .RepoDigests}}'; exit $LASTEXITCODE` | 0 | Cached image ID/digest `sha256:be1575ed968de893bd54f4c56315ff7c4736ce522c1bca08fd521731aafc0d76`, `linux/amd64`, repository digest `python@sha256:be1575ed968de893bd54f4c56315ff7c4736ce522c1bca08fd521731aafc0d76` |
| `docker --context desktop-linux network inspect bridge --format '{{json .IPAM.Config}}'; exit $LASTEXITCODE` | 0 | Default bridge subnet `172.17.0.0/16`, gateway `172.17.0.1`; metadata, not reachability |

Node's official release metadata independently confirms bundled npm `11.9.0`:

```powershell
$ErrorActionPreference='Stop'
$cgNodeRelease=Invoke-RestMethod -Uri https://nodejs.org/dist/index.json -TimeoutSec 15
$cgNodeRelease | Where-Object version -eq 'v24.14.0' | Select-Object version,date,npm,modules,lts | ConvertTo-Json -Compress
```

Exit 0; output:
`{"version":"v24.14.0","date":"2026-02-24","npm":"11.9.0","modules":"137","lts":"Krypton"}`.
This supports the proposed builder version; `node --version` and `npm --version`
in the eventual builder remain required runtime evidence.

## Address evidence

Each command below was run separately and ended with `exit $LASTEXITCODE`.
Connect timeout is 3 seconds, overall timeout 8 seconds. Only version GETs were
issued; no inference, tool execution, model installation or resource mutation.

| Exact command before the exit statement | Exit | Result |
| --- | ---: | --- |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://127.0.0.1:11434/api/version` | 0 | `{"version":"0.33.3"}` |
| `wsl -d Ubuntu -- curl --silent --show-error --connect-timeout 3 --max-time 8 --fail http://127.0.0.1:11434/api/version` | 0 | `{"version":"0.33.3"}` |
| `curl.exe --silent --show-error --connect-timeout 3 --max-time 8 --fail http://host.docker.internal:11434/api/version` | 28 | Connection timed out after 3004 ms |
| `wsl -d Ubuntu -- curl --silent --show-error --connect-timeout 3 --max-time 8 --fail http://host.docker.internal:11434/api/version` | 7 | Cannot connect after 1238 ms |

Windows and WSL host launch use `127.0.0.1:11434/v1`. Inside a backend container,
loopback is that backend, not Windows or the external Ollama server. Future
Compose uses frontend-to-backend service DNS `backend:8000`; no application
service or dependency is implemented or verified by this research.

## Rejected diagnostic command and resource accounting

Attempt count: one. No alternate shell/tool retry or policy change was made.
Proposed identity: `cg-preflight-20261003-7b13a8`; created ID: **none**.
The command tool rejected CreateProcess before any shell process, so there is
no native exit code for create/inspect/start and none is represented as passed.

The exact attempted PowerShell `cmd` argument was:

```powershell
$ErrorActionPreference='Stop'
$cgProbeName='cg-preflight-20261003-7b13a8'
$cgProbeImage='python@sha256:be1575ed968de893bd54f4c56315ff7c4736ce522c1bca08fd521731aafc0d76'
$cgProbeScript=@'
import json, signal, socket, sys, urllib.request
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
results=[]
for host in ['host.docker.internal','127.0.0.1','172.17.0.1']:
    signal.alarm(8)
    row={'host':host,'path':'/api/version'}
    try:
        row['ipv4']=socket.gethostbyname(host)
        with opener.open('http://'+host+':11434/api/version',timeout=3) as response:
            row['status']=response.status
            row['body']=response.read(4096).decode('utf-8')
    except Exception as exc:
        row['error']=str(exc)
    finally:
        signal.alarm(0)
    results.append(row)
    print(json.dumps(row),flush=True)
sys.exit(0 if results[0].get('status')==200 else 1)
'@
$cgProbeId=docker --context desktop-linux create --name $cgProbeName --label org.cognitive-graph.owner=devops_preflight --label org.cognitive-graph.purpose=bounded-metadata-get --pull=never --rm --network bridge --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 64m --cpus 0.25 --user 65534:65534 --entrypoint python $cgProbeImage -c $cgProbeScript
$cgCreateExit=$LASTEXITCODE
Write-Output "create_exit=$cgCreateExit container=$cgProbeId name=$cgProbeName"
if ($cgCreateExit -ne 0) { exit $cgCreateExit }
docker --context desktop-linux inspect $cgProbeId --format '{{.Id}} {{.Name}} {{.Image}} {{.HostConfig.NetworkMode}} {{.HostConfig.AutoRemove}} {{.Config.User}} {{json .Mounts}} {{json .NetworkSettings.Ports}} {{json .Config.Labels}}'
$cgInspectExit=$LASTEXITCODE
Write-Output "inspect_exit=$cgInspectExit"
if ($cgInspectExit -ne 0) { exit $cgInspectExit }
docker --context desktop-linux start --attach $cgProbeId
$cgStartExit=$LASTEXITCODE
Write-Output "start_exit=$cgStartExit"
exit $cgStartExit
```

Tool call metadata: `tools.exec_command`, output budget 3000, yield 10000 ms,
default PowerShell working directory `D:/Sources/creep`, no escalation field.
The enclosing functions.exec ended `Script failed`, wall time 0.0 seconds.
Rejection text returned by the tool (the command preview was already truncated
by the tool, rather than omitted by the worker):

```text
Script error:
exec_command failed: CreateProcess { message: "Rejected(\"`\\\"C:\\\\\\\\Users\\\\\\\\pkupr\\\\\\\\.cache\\\\\\\\codex-runtimes\\\\\\\\codex-primary-runtime\\\\\\\\dependencies\\\\\\\\native\\\\\\\\powershell\\\\\\\\pwsh.exe\\\" -Command '$ErrorActionPreference='\\\"'Stop'\\n\\\"'$cgProbeName='\\\"'cg-preflight-20261003-7b13a8'\\n\\\"'$cgProbeImage='\\\"'python@sha256:be1575ed968de893bd54f4c56315ff7c4736ce522c1bca08fd521731aafc0d76'\\n\\\"'$cgPro…1446 chars truncated…}} {{.HostConfig.AutoRemove}} {{.Config.User}} {{json .Mounts}} {{json .NetworkSettings.Ports}} {{json .Config.Labels}}'\\n\\\"'$cgInspectExit=$LASTEXITCODE\\nWrite-Output \\\"inspect_exit=$cgInspectExit\\\"\\nif ($cgInspectExit -ne 0) { exit $cgInspectExit }\\ndocker --context desktop-linux start --attach $cgProbeId\\n$cgStartExit=$LASTEXITCODE\\nWrite-Output \\\"start_exit=$cgStartExit\\\"\\nexit $cgStartExit'` rejected: blocked by policy\")" }
```

Independent residue checks executed after rejection:

```powershell
docker --context desktop-linux ps --all --filter name=^/cg-preflight-20261003-7b13a8$ --format '{{.ID}} {{.Names}} {{.Status}}'; exit $LASTEXITCODE
```

Exit 0, empty output.

```powershell
docker --context desktop-linux ps --all --filter label=org.cognitive-graph.owner=devops_preflight --format '{{.ID}} {{.Names}} {{.Status}}'; exit $LASTEXITCODE
```

Exit 0, empty output. No cleanup command was needed or executed. The proposed
diagnostic had no volumes, mounts, published ports, host networking, GPU,
privilege, inference service, or Docker socket. Even a successful cached-image
GET would only establish that image/network route, not future backend or A15 PASS.

## Remaining implementation and live gates

The concrete preflight blocker is command-tool rejection of the diagnostic;
root owns disposition. Independent metadata work is finished. G1 and other
source work can continue. G5/G6 must retain these open gates:

1. Build exact digest-pinned backend/frontend/uv candidates with frozen lockfiles;
   record actual Python/uv/Node/npm/nginx and linked SQLite versions. Verify the
   SQLite durability constraints from the accepted architecture on the actual
   named-volume filesystem.
2. Run `docker compose config` against the eventual file, project, profiles and
   explicit caller overrides. Assert context, selected services, loopback ports
   8000/8080, named volume ownership and target before runtime actions. Compose
   static validation is not executed because no delivery file exists yet.
3. Probe `/v1/models` from the actual backend container, then real JSON/SSE/tools
   against external Ollama. Preserve the configured endpoint; diagnose native
   WSL Engine and Desktop routes separately. No external Ollama container,
   Hermes executor, Windows mounts, or Docker socket is added to Compose.
4. Prove non-root backend volume creation/reopen, atomic graph writes, SQLite
   WAL recovery, one Uvicorn worker, graceful stop, and frontend service DNS.
   Configure and test nginx SSE buffering/timeouts against the active budget;
   use a non-root writable PID/cache strategy rather than assuming base defaults.
5. Run real UI/API/Hermes smoke through the owned Compose project from Windows
   and WSL2; restart and verify history, immutable snapshots and waiting tool
   IDs. A10/A12/A15 remain open. Bootstrap's smoke targets must execute real
   tests and fail nonzero; no placeholder smoke is accepted.
6. Stop/remove only owned smoke containers/networks; preserve cg_data and user
   resources, then independently query residue. Do not use broad prune or
   `down -v`. Recheck occupied ports immediately before launch.

Exact production launch/smoke instructions depend on implemented G5 files and
the later runtime handoff; no unimplemented command is claimed as exercised.
The user can execute the displayed diagnostic only in a session whose controls
permit the authorized operation; choose a new unique name for a fresh attempt.
The agent does not bypass the current tool rejection.

## Primary sources and confidence

Registry metadata was queried directly using Docker buildx; sources and returned
digests above are reproducible observations, not downloaded/runtime-tested images.
[Docker imagetools inspect](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)
documents registry inspection and index/image output.
[uv Docker guidance](https://docs.astral.sh/uv/guides/integration/docker/)
documents copying the uv binary from its published image and digest pinning.
[Docker Desktop networking](https://docs.docker.com/desktop/features/networking/)
documents the host alias for containers; this does not replace empirical
application-container testing. Official pages read 2026-10-03.
[Node release metadata](https://nodejs.org/dist/index.json) supports the npm pin.

Residual risks: registry access at build time, mutable external model tags,
unproven actual backend route/volume permissions/SQLite durability/SSE/shutdown,
and unavailable diagnostic runtime authorization. No product requirement,
acceptance criterion, model matrix, tool policy, or default was changed.
