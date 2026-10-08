# Local Cognitive Graph runbook

Owner: local project operator; implementation and open-gate disposition belong
to the main coordinator. No cloud service or external resource is managed here.
The backend executes a graph and calls external Ollama; Hermes executes tools
outside Compose. The frontend is a static React bundle with same-origin Nginx
forwarding `/api`, `/v1` and `/health` to `backend:8000`.

Current delivery state (2026-10-06): G2-runtime attempt6 independently PASSed
after the scoped local `referencing==0.37.0+cg.1` wheel correction, preserving
the accepted schema profile. Fresh full Windows and WSL2 Compose/Hermes smokes
both exited0 with current engine `7a9ccb1e...`, all29 production backend files
and installed wheel members matched to current source. The evidence and exact
commands are in [verification.md](verification.md#current-source-full-live-validation-2026-10-06)
and [live-current-summary.json](../.codex/specs/cognitive-graph-mvp/live-current-summary.json).
For current review status, see [current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md).
G5 independently PASSed cycle2 (2/3) after the helper failure-path correction;
G6 independently PASSed cycle1 (1/3), closing all mandatory MVP gates.
Earlier failures and outcomes remain historical; residual limitations are in
the completion report linked from current-state.md.

## Setup and launch

Use the locked [development commands](dependencies.md), Python3.11.15,
uv0.11.28, Node24.14.0/npm11.9.0. Docker Desktop must use its Linux daemon and
enable integration for your WSL2 distribution. Observed Desktop4.43.2,
Docker28.3.2, Compose2.38.2-desktop.1 and WSL2.7.8 are research facts, not an
instruction to downgrade another working installation. Dockerfiles use exact
immutable [image pins](research/delivery-preflight.md). No global dependencies,
unbounded package version or model installation is needed.

From Windows PowerShell at `D:/Sources/creep`:

```powershell
docker context show
docker --context desktop-linux version --format '{{.Server.Os}}/{{.Server.Arch}}'
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml config --quiet
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml up --build -d --wait
curl.exe --fail http://127.0.0.1:8080/health/ready
```

`desktop-linux` is this host's observed context; preserve your explicitly
selected context rather than switching it. Actual Windows pinned production
builds/startup now passed after the recorded Nginx temp-path correction, plus
direct JSON/SSE, history/volume recreation and target measurements. Complete
corrected-provider Windows and WSL2 smokes also passed with original Hermes,
waiting-tool restart, replay and compression. WSL used the existing native
Windows client outside Compose with matching daemon/pin checks. Current-source
production reconciliation passed on both platforms; G0–G4 independently PASS,
including G2 attempt6 with F1–F6 closed. Follow
[current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md) for the
accepted G5/G6 reviews and [verification](verification.md) for exact
source-scoped evidence before a completion claim.

The equivalent WSL2 commands, with Docker Desktop integration:

```bash
cd /mnt/d/Sources/creep
docker context show
docker compose -p cognitive-graph -f compose.yaml config --quiet
docker compose -p cognitive-graph -f compose.yaml up --build -d --wait
curl --fail http://127.0.0.1:8080/health/ready
```

Native development uses Windows paths and `backend/.venv/Scripts`; WSL uv uses
Linux paths/venv executables. Do not reuse one platform's venv on the other.
Container build contexts copy only allowlisted source/manifests/locks; they
exclude native dependency trees, `.env`, tokens, traces and user data. There
are no source bind mounts, Docker sockets, Windows tool directories or GPUs.
Run shell smoke through `bash scripts/smoke_compose.sh`; Git execute bits are
not assumed. Shell files are UTF-8/LF. `make` delegates the same Python wrapper;
Windows uses `python scripts/dev.py` where Make is unavailable.

## External Ollama and access

Compose's default is `http://host.docker.internal:11434/v1`; native development
on this host uses `http://127.0.0.1:11434/v1`. Docker Desktop's host alias and a
native WSL Engine's `host-gateway` are different routing mechanisms. Compose
includes the standard host-gateway mapping. The actual production backend
container demonstrated its unchanged default route to external Ollama0.33.3
and Gemma4:12b digest4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c.
Historical native Windows/Ubuntu loopback probes succeeded while host-side
host.docker.internal probes failed; those host failures do not describe the
now-demonstrated application-container route. The current Windows
gateway172.26.144.1 worked from Ubuntu but is not a stable default. Do not
silently substitute it, attach to the unrelated user-owned Ollama container,
change Ollama's bind/firewall policy, or add an inference service.

For native WSL Engine, determine the Windows server's actual reachable address
and verify it from the backend before setting an explicit OLLAMA_BASE_URL.
Server exposure/firewall changes require the user's approval. Loopback inside
the backend means that backend container, not Windows. Read-only diagnostics:

```powershell
curl.exe --fail --connect-timeout 3 --max-time 8 http://127.0.0.1:11434/api/version
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml ps
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml logs --tail 100 backend
```

Readiness separates storage/recovery from `ollama_available`; upstream failure
is an explicit503/502/504 response, not a successful empty answer. Liveness
and readiness are unauthenticated boolean diagnostics. API surfaces require
the bearer token when configured. Supply CG_API_TOKEN in the launching process
environment; neither commands nor evidence should print it. The UI holds it
in memory and uses authenticated fetch SSE. Token rotation changes namespace
and prevents access to earlier token-bound runs; do not rotate to fix a pending
continuation. Never place tokens in URLs or graph/export files.

## Configuration and timing

`.env.example` lists the frozen defaults. An optional `.env` may contain only
nonsecret local overrides; launching process values take precedence in Compose.
Native Settings reads process environment directly. Configuration changes need
restart. Compose fixes CG_DATA_DIR to `/data` and volume cg_data; use a native
CG_DATA_DIR override only for native launch. Smoke rejects a conflicting
container data-dir override rather than silently writing elsewhere.

The global provider limit defaults2, shared admitted capacity4 and reserved
queue20. Waiting tools retain an active lease but release inference capacity.
CG_LLM_TIMEOUT_SECONDS=300 is per full upstream exchange; active-run wall time
1800 excludes queued and quiescent tool waiting. CG_TOOL_WAIT_TIMEOUT_SECONDS=1800
is a fixed UTC batch deadline, including process downtime; partial results and
replays never extend it. Node budget100 and exposed-tool-batch budget20 are
failure caps, not substitutes for strict conditional loop termination.

Nginx renders only its timeout marker from the maximum validated positive
CG_RUN_ACTIVE_TIMEOUT_SECONDS, CG_TOOL_WAIT_TIMEOUT_SECONDS and
CG_LLM_TIMEOUT_SECONDS plus60seconds, preserving Nginx `$host/$uri`
variables. Buffering, request buffering, proxy cache and gzip are off for API
locations. SSE should expose committed monotonic events and final externally
valid content only. After SSE starts, an error event closes the stream without
a fabricated successful stop. This configuration requires actual stream proof;
static syntax is insufficient. Backend runs one Uvicorn worker as UID10001;
frontend runs Nginx as UID101. Read-only roots have `/tmp` tmpfs. A new data
volume inherits `/data` UID10001/mode0700 from the image. An existing volume
with incompatible ownership fails explicitly; startup does not chown user data.

## Graphs, history and failure recovery

Choose an installed physical model in the editor; create or import JSON,
validate, save with expected_revision and publish. Virtual `cg/<id>` models
appear only after publication. Examples use an explicit model placeholder;
replace it with your selected installed name before import. Each input port
has one provider; feedback requires a loop/controller/seed/exit decision.
Manual tool results support UI testing; actual tools require Hermes.

Runs retain immutable graph snapshots/hashes, original history, node/loop
results and events. Editing/republication changes future runs only. Retry a
revision409 by reloading and resolving edits, never blind overwrite. Cancel is
idempotent; it prevents new scheduling and rejects late results but cannot
undo a tool already executing in Hermes. A lost initial connection may cancel
unexposed work; exposed tool IDs remain durable. Reconnect events using
Last-Event-ID; reload detail/history from the API instead of relying on UI memory.

Restart the owned backend only:

```powershell
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml restart backend
curl.exe --fail http://127.0.0.1:8080/health/ready
```

Required recovery semantics: valid waiting_tools retains IDs and original TTL;
expired waits fail, queued work recovers, uncertain active inference becomes
interrupted without automatic rerun. Exact saved continuation may replay after
success; changed/late/terminal results fail. Restart does not make an interrupted
tool operation safe to repeat. Diagnose saved status/error and Hermes's actual
tool effects before starting a new run. Completed history/publication/immutable
snapshots survived an actual owned backend restart and new-container down/up
on the retained volume. Waiting-tool IDs/owners/TTL across actual process restart
and native continuation replay remain open until their instrumented smoke passes.

## Smoke and verification

Use unused localhost ports8000/8080. Full Compose smoke allocates a fresh
`cg-smoke-<uuid>` project, refuses existing containers/network/volume, asserts
context/files/profiles/ports/mount/target, builds, checks production UI/API,
JSON/SSE/native direct tool delivery/errors/durable events, probes external
Ollama from the actual non-root backend,
checks writable data/SQLite WAL, edits a draft after snapshot, restarts and
checks history. It downs only its project without `-v`, independently checks
container/network residue and reports the retained uniquely named data volume.
It never deletes a user volume or prunes Docker. Explicit project/context/file
input is preserved; unsupported extra services/profiles/mounts fail closed.

```powershell
python scripts/smoke_compose.py --context desktop-linux --validate-only
$env:CG_SMOKE_MODEL = 'gemma4:12b' # Choose your already installed model.
python scripts/smoke_compose.py --context desktop-linux --model $env:CG_SMOKE_MODEL
# WSL wrapper, same real Python helper:
wsl -d Ubuntu --cd /mnt/d/Sources/creep bash scripts/smoke_compose.sh --model gemma4:12b
```

`python scripts/dev.py smoke-compose --validate-only` dispatches this WSL/bash
helper without runtime actions. The wrapper converts Windows paths and forwards
explicit arguments plus allowlisted model/project/frozen configuration variables
through child-local WSLENV without printing their values. For full smoke, use
`python scripts/dev.py smoke-compose --model gemma4:12b`; Make accepts the same
flags through `SMOKE_ARGS='--model gemma4:12b'`. A raw `wsl` invocation does not
automatically inherit Windows environment, so pass the model directly as shown.
The direct native Python invocation provides Windows-side evidence separately. A failed command or
missing prerequisite exits nonzero. Never reinterpret an unavailable check
as PASS. [Hermes smoke instructions](hermes-compatibility.md) use actual Hermes
outside Compose. Full smoke also records seven direct physical-model HTTP
exchanges (ordinary/multiturn JSON/SSE and native function request/result pairs,
with zero tool execution), live SSE frame arrival times, actual backend route,
image/source/package hashes, Nginx configuration, completed-history restart,
volume-preserving down/up publication/history checks, and same-model three-call
diamond versus sequential wall/queue/node timings. One sample per shape is
evidence for this target, not a GPU speedup promise. The helper tears down only
its new project's containers/network and retains its volume, including
`/data/delivery-smoke.json` when all requested checks finish.

For the known installed Gemma test model and existing pinned G0 Hermes Python,
use a fresh Windows project to include real Hermes outside Compose, literal
`cg/synthesis`, two owners, serialized continuation/replay, actual waiting-tool
backend restart, and native pending-ID compression:

```powershell
$cgSmokeProject = 'cg-smoke-win-' + [guid]::NewGuid().ToString('N').Substring(0,12)
python scripts/smoke_compose.py --context desktop-linux --project $cgSmokeProject --model gemma4:12b --reasoning-effort none --hermes-python D:/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent
if ($LASTEXITCODE -ne 0) { throw 'Required integrated smoke failed; preserve reported evidence' }
```

The explicit reasoning setting applies to dedicated stored graph nodes and the
isolated native compression fixture only. Physical public direct requests keep
the accepted API profile. The existing pinned interpreter/source are required;
this command installs or downloads neither tools nor models. Compression calls
the external local Ollama endpoint through Hermes, not a Docker executor.
Never target a user project or overwrite an existing synthesis graph; initial
creation fails on conflicts. Fixture/home/evidence directories are retained.

Then obtain separate WSL2 full application evidence after the Windows helper
has finished its scoped teardown:

```powershell
$cgWslProject = 'cg-smoke-wsl-' + [guid]::NewGuid().ToString('N').Substring(0,12)
python scripts/dev.py smoke-compose --project $cgWslProject --model gemma4:12b --reasoning-effort none --hermes-python /mnt/d/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root /mnt/c/Users/pkupr/AppData/Local/hermes/hermes-agent --hermes-docker-context desktop-linux
if ($LASTEXITCODE -ne 0) { throw 'WSL2 integrated smoke failed; preserve reported evidence' }
```

This invocation launches Compose from WSL2 and runs actual production
images/API/UI/direct-model exchange and target measurements. Its existing
Windows-native Hermes client runs outside Compose through WSL interoperability;
only script/source/fixture paths are explicitly converted with wslpath. It
checks pinned client versions and equality of the Linux caller's and explicit
Windows Docker context's daemon IDs before native execution. It does not import
Windows venv packages into Linux or require another Hermes installation. Omit
the three Hermes options for a stack-only check, which leaves that native gate
OPEN. The commands above are verification instructions; executed outcomes,
including unavailable routes and prerequisites, are recorded in verification.md.
The 2026-10-06 current-source execution completed both full commands with
separate new projects, scoped teardown and retained volumes. Windows Compose
used native Hermes; WSL Compose used the same pinned Windows client through
interop. Both JSON/SSE cases completed native fixture reads, owner continuation
and exact replay; the JSON case also proved waiting-ID restart and compression.
All29 backend source files and installed patched-wheel members were compared
read-only against current repository bytes. Do not reuse the recorded project
names or interpret historical engine/image hashes as current proof.

## Consistent backup, rollback and teardown

If the actual application container cannot reach external Ollama, the following
explicit native fallback verifies independent production HTTP/Hermes behavior.
Run only after the coordinator releases native port8000 and records the actual
container failure; it changes no Compose endpoint, network or Ollama setting:

```powershell
$cgNativeWork = Join-Path $PWD ('.venv/native-delivery-' + [guid]::NewGuid().ToString('N'))
& .venv/hermes-research/Scripts/python.exe scripts/smoke_hermes.py --base-url http://127.0.0.1:8000 --model gemma4:12b --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent --work-dir $cgNativeWork --native-backend-python backend/.venv/Scripts/python.exe --native-ollama-url http://127.0.0.1:11434/v1 --reasoning-effort none --compress --compression-url http://127.0.0.1:11434/v1
if ($LASTEXITCODE -ne 0) { throw 'Native delivery smoke failed; retain its work directory' }
```

This requires the already pinned interpreters and source, not an installation.
It owns one Uvicorn process, starts the exact production app with a new data
directory, proves a waiting-tool process replacement on that same data, and
stops only its own process in `finally`. Windows termination is abrupt; Linux
uses SIGTERM with a bounded wait. Evidence, log and SQLite/graph files remain.
It also runs real direct JSON/SSE/native-tool transport and same-model target
measurements. No executor runs inside the backend. Container routing, Nginx,
container volume and Windows/WSL2 Compose gates remain OPEN regardless of a
native-only success. Source changes during the native fixture invalidate it.

For isolated image persistence verification before integrated startup:

```powershell
python scripts/smoke_compose.py --context desktop-linux --persistence-only
```

This distinct mode needs no physical model. It builds only the real backend
image and runs a bounded production SQLite/graph-file fixture with networknone,
no published ports, HTTP server, health probe, Ollama or executor. It preserves
the non-root/read-only/capability controls, allocates a fresh project/volume,
and retains its exited container and evidence/state. Never reuse the displayed
project names or delete prior volume data to force a pass. The 2026-10-04
executed result and two corrected verifier-fixture failures are recorded in
[verification.md](verification.md). This check covers WAL/CAS/claim rollback/
reopen and actual Linux fsync/symlink guards; it does not prove integrated
startup, waiting-ID process restart or close other live acceptance gates.

Graphs/publications and SQLite history reside in the named volume
`<project>_cg_data`. Host disk protection and Docker volume access controls
protect local data; the product does not claim encryption at rest. Default
retention30days removes terminal history only, preserving graphs and live waits.
Set retention deliberately; it is data policy, not an automatic troubleshooting
step. Logs omit access records and raw upstream exceptions; inspect run errors
and IDs without dumping tokens or private history.

The operator drill executed graceful Compose stop, whole-directory `docker cp`,
whole-volume tar backup, separate-empty-volume restore and restarted production
readiness/history/checkpoint checks on new fixtures. It used the cached current
backend image, UID10001, networknone/read-only/cap-drop controls and zero
inference/tool effects. Its pending checkpoint was synthetic; real Hermes
restart evidence is separately attributed above. Exact failures, successful
audit and retained volumes appear in [verification](verification.md).

For a consistent backup, schedule downtime and stop the selected backend.
Stopping interrupts uncertain active work; tool-wait deadlines include downtime.
Keep the entire data snapshot together, including SQLite/WAL/SHM when present,
graphs and publications. Do not merge live WAL files from different snapshots.
The following PowerShell procedure uses an existing cached immutable backend
image and creates only fresh backup/restore resources. Actual user-data backup
or restoring an existing deployment requires operator authorization; the drill
accessed only newly created test data.

```powershell
$cgProject = 'cognitive-graph' # Select the intended existing local project.
$cgContext = 'desktop-linux'
$cgFile = (Resolve-Path compose.yaml).Path
$cgBackend = docker --context $cgContext compose -p $cgProject -f $cgFile ps --all --quiet backend
if ($LASTEXITCODE -ne 0 -or -not $cgBackend) { throw 'Backend identity unavailable' }
$cgLabel = docker --context $cgContext inspect $cgBackend --format '{{index .Config.Labels "com.docker.compose.project"}}'
if ($LASTEXITCODE -ne 0 -or $cgLabel -ne $cgProject) { throw 'Unexpected project' }
$cgImage = docker --context $cgContext inspect $cgBackend --format '{{.Image}}'
if ($LASTEXITCODE -ne 0 -or $cgImage -notmatch '^sha256:[0-9a-f]{64}$') { throw 'Image identity unavailable' }
$cgMounts = docker --context $cgContext inspect $cgBackend --format '{{json .Mounts}}' | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Mount identity unavailable' }
$cgSource = @($cgMounts | Where-Object { $_.Destination -eq '/data' -and $_.Type -eq 'volume' })
if ($cgSource.Count -ne 1 -or $cgSource[0].Name -ne "${cgProject}_cg_data") { throw 'Unexpected data volume' }
$cgSourceVolume = $cgSource[0].Name
docker --context $cgContext compose -p $cgProject -f $cgFile stop --timeout 45 backend
if ($LASTEXITCODE -ne 0) { throw 'Stop failed; do not copy active data' }
$cgState = docker --context $cgContext inspect $cgBackend --format '{{json .State}}' | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $cgState.Status -ne 'exited' -or $cgState.OOMKilled -or $cgState.Error) { throw 'Shutdown failed' }
# Inspect only shutdown lines; never dump private history or environments.
docker --context $cgContext compose -p $cgProject -f $cgFile logs --no-color --tail 30 backend
if ($LASTEXITCODE -ne 0) { throw 'Shutdown evidence unavailable' }
# Require Application shutdown complete / Finished server process.
# Pinned Uvicorn re-raises SIGTERM after graceful shutdown: process status143
# can accompany Compose stop0. SIGKILL137 or absent shutdown completion is failure.
$cgSuffix = [guid]::NewGuid().ToString('N')
$cgBackupVolume = "${cgProject}_backup_$cgSuffix"
$cgRestoreProject = "$cgProject-restore-$cgSuffix"
$cgRestoreVolume = "${cgRestoreProject}_cg_data"
$cgBackupDir = Join-Path $PWD "backups/$cgSuffix"
New-Item -ItemType Directory -Path $cgBackupDir -ErrorAction Stop | Out-Null
$cgExisting = docker --context $cgContext volume ls --format '{{.Name}}'
if ($LASTEXITCODE -ne 0 -or $cgBackupVolume -in $cgExisting -or $cgRestoreVolume -in $cgExisting) { throw 'Require fresh volumes' }
docker --context $cgContext volume create --label "cg.backup=$cgSuffix" $cgBackupVolume
if ($LASTEXITCODE -ne 0) { throw 'Backup volume creation failed' }
$cgArchiveCode = @'
import pathlib,subprocess,os,hashlib
p=pathlib.Path('/data/cg-backup.tar'); assert not p.exists()
subprocess.run(['tar','--numeric-owner','--create','--file='+str(p),'--directory=/source','.'],stdin=subprocess.DEVNULL,check=True)
with p.open('rb') as f: os.fsync(f.fileno())
print(hashlib.sha256(p.read_bytes()).hexdigest())
'@
$cgArchiveHash = docker --context $cgContext run --rm --pull never --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges --mount "type=volume,src=$cgSourceVolume,dst=/source,readonly" --mount "type=volume,src=$cgBackupVolume,dst=/data" $cgImage python -c $cgArchiveCode
if ($LASTEXITCODE -ne 0) { throw 'Archive failed; preserve original and backup volume' }
$cgExport = "cg-backup-export-$cgSuffix"
docker --context $cgContext create --pull never --name $cgExport --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges --mount "type=volume,src=$cgBackupVolume,dst=/data,readonly" $cgImage true
if ($LASTEXITCODE -ne 0) { throw 'Export helper creation failed' }
docker --context $cgContext cp "${cgExport}:/data/cg-backup.tar" (Join-Path $cgBackupDir 'cg-backup.tar')
if ($LASTEXITCODE -ne 0) { throw 'Archive copy failed; retain export helper for diagnosis' }
if ((Get-FileHash (Join-Path $cgBackupDir 'cg-backup.tar')).Hash.ToLowerInvariant() -ne $cgArchiveHash) { throw 'Archive hash mismatch' }
docker --context $cgContext rm $cgExport # Only this stopped, newly created helper.
if ($LASTEXITCODE -ne 0) { throw 'Export helper cleanup failed' }
```

The new backup volume uses the image's empty `/data` ownership initialization;
no existing volume is chowned. Windows directory `docker cp` was also exercised
and its file hashes matched, but NTFS copy ownership is not Linux UID metadata.
Keep the tar archive for restoration; it preserves Linux modes/numeric owners.
On WSL, the same Docker argv use `/mnt/d/...` for mounted Windows destinations
or a native Linux path for Linux destinations. Linux Docker cp destination
ownership follows that host filesystem/user; neither host directory copy is
advertised as a replacement for the tested archive restore. The Windows-host
copy and Linux container restore were executed; a WSL host-copy variant was
not separately executed in this drill. Restrict backup access because history
and tool results can contain private local data.

Restore into the new, separate empty volume, leaving the original stopped:

```powershell
docker --context $cgContext volume create --label "cg.backup=$cgSuffix" $cgRestoreVolume
if ($LASTEXITCODE -ne 0) { throw 'Restore volume creation failed' }
$cgRestoreCode = @'
import pathlib,tarfile,subprocess,os
root=pathlib.Path('/data'); assert list(root.iterdir())==[], 'Refuse nonempty restore'
archive=pathlib.Path('/backup/cg-backup.tar')
with tarfile.open(archive) as tar:
    members=tar.getmembers(); assert members
    for m in members:
        path=pathlib.PurePosixPath(m.name)
        assert not path.is_absolute() and '..' not in path.parts
        assert m.isdir() or m.isfile()
        assert m.uid==10001 and m.gid==10001
subprocess.run(['tar','--extract','--no-same-owner','--file='+str(archive),'--directory='+str(root)],stdin=subprocess.DEVNULL,check=True)
for path in root.rglob('*'):
    assert path.stat().st_uid==10001 and path.stat().st_gid==10001
'@
docker --context $cgContext run --rm --pull never --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges --mount "type=volume,src=$cgBackupVolume,dst=/backup,readonly" --mount "type=volume,src=$cgRestoreVolume,dst=/data" $cgImage python -c $cgRestoreCode
if ($LASTEXITCODE -ne 0) { throw 'Restore failed; preserve all copies' }
```

Before starting restored services, compare every archive/volume file hash,
mode and UID and run SQLite integrity/FK checks on the isolated copy. The drill
used read-only `immutable=1` inspection after confirmed graceful shutdown,
avoiding a verifier-created WAL/SHM pair. Never use immutable inspection on an
active database or ignore a nonempty WAL. After startup SQLite physical bytes
can change; check logical rows, run IDs/snapshot hashes, graph/publication files,
pending owners/IDs/deadlines/counters, readiness and another restart rather than
requiring identical SQLite physical bytes after writes.

The executed fixture started source/restored services with networknone and no
host ports, using explicit test-only upstream127.0.0.1:9 and the immutable image.
Readiness remained storage-ready with Ollama unavailable; no inference/tool
effects ran. For an authorized application restore, use a separate Compose
project mapped to the fresh volume and release the original project's ports
first. Verify the rendered image/volume/endpoint configuration before startup.
That operator port cutover and restoration from an arbitrary user backup were
not part of the fixture drill. Retain the original volume, backup archive,
restored volume and evidence; never extract over existing data automatically.

To roll back application code, retain the current volume/backup and rebuild the
last known local reviewed revision in a separate checkout. Do not run broad Git
reset or assume older schema compatibility; inspect migration compatibility
first. Recreate only the owned services, then repeat health/history/tool-wait
checks. If storage compatibility is unknown, stop and request disposition.

Volume-preserving teardown:

```powershell
docker --context desktop-linux compose -p cognitive-graph -f compose.yaml down --timeout 45
docker --context desktop-linux ps --all --filter label=com.docker.compose.project=cognitive-graph
docker --context desktop-linux network ls --filter label=com.docker.compose.project=cognitive-graph
docker --context desktop-linux volume ls --filter name=cognitive-graph_cg_data
```

`docker compose down -v` deletes graph files/history/checkpoints; it requires
explicit data-deletion authorization and is never used by smoke. Never use
`docker system prune`, broad cleanup, or stop the user-owned external Ollama.
Escalate policy rejection, missing upstream route, corrupt storage, or exhausted
review/live gates to the main coordinator with command/exit/resource identity;
do not bypass trust controls or silently weaken acceptance.
