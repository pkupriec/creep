# Verification evidence and open gates

This file records G5 delivery evidence, not an independent verdict. The sole
review synthesizer owns [review.md](../.codex/specs/cognitive-graph-mvp/review.md);
the main coordinator owns [tasks and decisions](../.codex/specs/cognitive-graph-mvp/).
All R01–R11 and A01–A16 remain authoritative. Static and research success
does not close production runtime acceptance.

Current state, 2026-10-06: G2 attempt6 independently PASSed after the local
`referencing==0.37.0+cg.1` correction; the accepted schema/runtime profile is
unchanged. G0/G1/G3/G4 retain their recorded independent PASS outcomes.
Fresh current-source Windows and WSL2 full Compose/Hermes checks below both
exited0. G5 independently PASSed cycle2 (2/3), closing the direct-only cleanup
failure-path finding. G6 independently PASSed cycle1 (1/3), closing R01–R11 and
A01–A16 mandatory gates. The full live runs remain valid. Follow
[current-state.md](../.codex/specs/cognitive-graph-mvp/current-state.md) for current
review status. These delivery-owner results do not constitute an independent
verdict by themselves; the linked independent review supplies acceptance.

Historical corrected-source Windows and WSL2 production smokes subsequently
passed with real external Ollama and original pinned Hermes JSON/SSE, native
fixture reads, waiting-ID restart, exact replay and compression. See the final
executed section below and the versioned
[completion report](../.codex/specs/cognitive-graph-mvp/completion.md).
Earlier sections retain stage-specific failures and then-open gates as history.
Those historical images predate the latest engine bytes. Current-engine
production reconciliation is recorded in the 2026-10-06 section below.
All older stage-specific gate/status statements are historical snapshots;
consult the current section and coordinator-owned current-state link for status.

## Current-source full live validation (2026-10-06)

The coordinator released execution after independent G2 attempt6 PASS and
completion of its UI checks, with ports8000/8080/5173 confirmed free. Existing
production helpers were used unchanged, sequentially, with external installed
Ollama0.33.3 and `gemma4:12b` digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
No model download, global configuration change or automatic failed live rerun
occurred. Complete commands, timestamps, source hashes, package inventory,
phase evidence and exact residue-query argv/exits are in
[current summary](../.codex/specs/cognitive-graph-mvp/live-current-summary.json).

| Exact command from repository root | Exit | Current evidence |
| --- | ---: | --- |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-smoke-win-current-20261006-86e89fd047bc --model gemma4:12b --reasoning-effort none --hermes-python D:/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent` | 0 | [Windows Compose](../.codex/specs/cognitive-graph-mvp/live-current-windows-compose.json), [Windows Hermes](../.codex/specs/cognitive-graph-mvp/live-current-windows-hermes.json) |
| `python scripts/dev.py smoke-compose --project cg-smoke-wsl-current-20261006-3a026de5ca87 --model gemma4:12b --reasoning-effort none --hermes-python /mnt/d/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root /mnt/c/Users/pkupr/AppData/Local/hermes/hermes-agent --hermes-docker-context desktop-linux` | 0 | [WSL Compose](../.codex/specs/cognitive-graph-mvp/live-current-wsl-compose.json), [WSL Hermes](../.codex/specs/cognitive-graph-mvp/live-current-wsl-hermes.json) |

The commands were launched once each by the ignored `.codex/.cache/current-live/collect.py`
observer, which preserved actual exits and logs and added read-only runtime
provenance. Its two invocations and both harvesting/summary commands exited0.
Windows and WSL validate-only preflights also exited0. A bare native package
metadata probe initially failed1 because it omitted the installed source venv
path; the existing helper-prescribed path guard subsequently passed0 with
Python3.11.15/Hermes0.18.2/OpenAI2.24.0/httpx0.28.1. No package was installed.

Actual Windows image is
`sha256:ace0000f2b7631e002f0ba8513694077417767725f2535882891466d119161cc`;
WSL image is
`sha256:fda5a824510bbea3dcbe15b8f21867368db95b71ed57b944e7839de603b13d3f`.
Both actual containers match all29 backend application files, including engine
`7a9ccb1e96d5a6197e7423598d7b29f6cb37557985897c072447bc7308e5088f`.
All22 installed package versions were recorded. Installed referencing0.37.0+cg.1
members equal the committed wheel bytes; wheel SHA256
`a84fbf0a7365b1a0592392a2859914de38f37258f1bca97d78fce582a102804c` and
patched jsonschema.py SHA256
`d71d7e00650fa3411b1957b1517d95a515461d7d428753eaf7a2719c10482c86`.
App/input hashes were rechecked unchanged after both executions. Distinct image
IDs reflect separate builds; neither is substituted with the earlier isolated
F6 proof image. Historical live JSON remains intact.

Both helpers asserted healthy API/static UI, actual application-container route
to external Ollama, UID10001/read-only/cap-drop controls, SQLiteWAL/quick_check,
seven ordinary/multiturn/native-tool-request/manual-result JSON/SSE physical
exchanges with zero direct tool effects, unknown-model404, unbuffered SSE/DONE,
and Nginx1860second timeouts exceeding1800second server budgets. Completed
history restart and volume-preserving container replacement retained published
graphs, immutable snapshots and run history. These are current executable R10/
A01/A02/A07/A09 replay/A10 waiting-history/A11/A15/A16 boundary subset evidence;
other acceptance cases retain their separate unit/contract/browser evidence.

Pinned original Hermes SHA `caed552de1c8a8f9983bc555512412a1ac0e0a9e`
matched19 exercised normalized source/guard files. Each JSON/SSE case used3
original SDK clients, performed2 guarded real native read_file calls, routed
results to2 owning nodes and proved2 exact continuation replays without new
effects/counters. Each ended with3 node executions/5 upstream attempts/2 tool
rounds. JSON selected literal `cg/synthesis`, replaced the waiting backend
before any tool effect, preserved opaque IDs/checkpoints/counters, and native
compression28→6 preserved pending IDs and raw results. WSL's Linux Compose
caller verified the same Docker daemon ID as the Windows-native client before
interop; it imported no Windows venv packages into Linux.

Single target samples: Windows diamond1.703s/sequential1.516s; WSL
diamond1.536s/sequential1.740s. These monotonic end-to-end measurements promise
no speedup. WSL sequential right-node UTC timestamps yield a negative duration
(-0.133643s), consistent with a wall-clock adjustment; that individual duration
is unusable for performance conclusions. Raw timestamps remain preserved,
the helper's actual exit remains0, and no extra inference was run to hide it.

Both scoped `down --timeout 45` operations exited0 without `-v`. Fresh independent
exact-project-label container/network queries and exact-volume queries exited0:
container/network arrays empty; both owned cg_data volumes retained. Final
read-only Windows listeners/process query exited0 with no8000/8080/5173 listeners
or native smoke Python processes. Native Hermes fixture directories and ignored
logs/provenance remain retained; unrelated resources were outside teardown scope.

Independent G5/G6 reviews subsequently PASSed. This live run did not repeat arbitrary
user-data backup/restore, authentication tests, the full browser/graph/control
acceptance matrix or remote GitHub CI. Historical operator recovery evidence
remains separately attributed; no current-schema user-data migration or remote
CI execution is claimed. No implementation, manifest, lock, security policy or
review file was changed by this delivery owner.

## Historical delivery evidence and stage-specific gates

All sections below preserve earlier commands, actual exits, failures and gates
at the time of execution. Their status statements are historical snapshots;
current-source live evidence and current review gates are recorded above.

### Executed delivery checks

From `D:/Sources/creep`, native PowerShell, 2026-10-03:

| Exact command | Exit | Demonstrated scope |
| --- | ---: | --- |
| `docker --context desktop-linux compose -p cg-delivery-static -f compose.yaml config --quiet` | 0 | Two-service static Compose syntax/interpolation; no runtime proof |
| `python scripts/smoke_compose.py --context desktop-linux --validate-only` | 0 | Linux/amd64 daemon, explicit context/files/project, no profiles, loopback8000/8080, own named-volume mapping; project `cg-smoke-73eb3bba9f2b`, no resources created |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-delivery-build --validate-only` | 0 | Actual backend build target asserted before build |
| `docker --context desktop-linux compose -p cg-delivery-build -f compose.yaml build backend` | 0 | Immutable Python3.11.15/uv0.11.28 bases, locked17 production packages, actual imports; linked SQLite3.40.1 |
| `docker --context desktop-linux compose -p cg-delivery-build -f compose.yaml build frontend` | 1 | Node24.14.0/npm11.9.0 assertions and locked npm ci passed; strict TS passed, Vite failed resolving absent `/src/main.tsx`. Planned UI prerequisite, not PASS |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py` | 0 | Owned Python smoke-source lint after correction |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py` | 0 | Owned source formatting only |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check scripts/smoke_compose.py scripts/smoke_hermes.py` | 0 | Current owned source format gate |
| `wsl -d Ubuntu --cd /mnt/d/Sources/creep bash scripts/smoke_compose.sh --validate-only` | 0 | WSL default context, Linux/amd64 daemon, mounted-drive/LF/bash/helper execution; project `cg-smoke-122c3bf3f8f7`, no resources created |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-delivery-static-final --validate-only` | 0 | Final mount/worker/privilege/device/context/port assertions after source edits |
| `python scripts/dev.py smoke-hermes` | 2 | Missing explicit model/Hermes source fails nonzero before API/tool execution |
| `python scripts/dev.py smoke-compose` | 1 | Windows shared wrapper failed converting backslash ROOT with wslpath before helper. Reported to bootstrap owner for serial correction; this is not smoke PASS |
| `python scripts/dev.py smoke-compose --validate-only` | 0 | After bootstrap-owner serial correction, actual Windows-to-WSL dispatch/path/environment/arguments/config works; project `cg-smoke-711b88d5f8ef`, no resources created |
| `python scripts/dev.py smoke-compose --cg-invalid-option` | 2 | Corrected wrapper propagates real helper failure without traceback |

Two inline Python verifier probes ran via a literal PowerShell here-string
into `uv --system-certs run --project backend --locked python -`, exit0 each.
They validate three actual Pydantic graph fixtures, native subprocess exit7
propagation, both CLI missing-prerequisite exit2/help exit0 paths and source
AST/shell LF; exercise actual SSE parser acceptance of DONE and rejection of
premature EOF/error; and invoke the actual Dockerfile startup prefix through
Ubuntu `sh -ec` for1860/4060second, leading-zero, zero and whitespace cases.
The five Linux shell cases passed, including rejection of invalid timeouts.
This proves the verifier/config prefix, not an Nginx container or product API.
An initial inline WSL argument-quoting probe exited1 before its assertions;
the corrected probe sent Python through `wsl --exec python3 -` stdin and passed.
Initial owned-source lint exits1 were corrected; current gates above pass.

Independent residue commands (each exit0, empty):
`docker --context desktop-linux ps --all --filter label=com.docker.compose.project=cg-delivery-build --format '{{.ID}} {{.Names}}'`,
`docker --context desktop-linux network ls --filter label=com.docker.compose.project=cg-delivery-build --format '{{.ID}} {{.Name}}'`, and
`docker --context desktop-linux volume ls --filter name=^cg-delivery-build_cg_data$ --format '{{.Name}}'`.
No cleanup was required. Image inspection exit0 confirms UID10001:10001,
working directory `/app`, one Uvicorn worker and graceful-shutdown30seconds;
these are image metadata, not running-container assertions.

Backend local image manifest-list digest after this skeleton-stage build:
`sha256:9fffc1b303c4b3674c2679992d2bc6ed19b7c24242dea9bd93a6b8e05e2add97`;
OCI config digest `sha256:e1bf7623d088d362bc022dae9c5c93ddc6962b360ac6d52af69be55a6df3ba70`;
Docker image inspect reports the manifest-list digest above as its image ID.
This build captured the then-current concurrent source snapshot; rebuild after
integration. No backend container, data volume or network was created. Images
and build cache are retained; no prune was performed. Native SQLite3.53.1 and
the image's3.40.1 are materially different. The single serialized connection
design must be exercised on the actual image; do not infer equivalence.

Immutable GitHub Actions source refs were queried read-only using
`git ls-remote <official_repo> refs/tags/<version>` (each exit0):

| Official repository/tag | Pinned commit |
| --- | --- |
| `https://github.com/actions/checkout.git`, v5 | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` |
| `https://github.com/actions/setup-python.git`, v6 | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| `https://github.com/actions/setup-node.git`, v6 | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| `https://github.com/astral-sh/setup-uv.git`, v6 | `d0d8abe699bfb85fec6de9f7adb5ae17292296ff` |

CI configuration uses locked setup, actual lint/contracts/all tests/build and
real Playwright E2E targets, then Compose static validation. No workflow was
dispatched, GitHub changed, project dependency installed globally, or browser
MCP enabled. Playwright's package-local Chromium installation is a CI command;
local research used the already cached browser. CI execution is not proven by
writing YAML. Production Hermes/Ollama are local smoke prerequisites, not fake
cloud CI services.

## Initial planned production and live gates (historical)

1. Finish the runtime/provider/tool/API/UI modules, rebuild both production
   images, and run required unit/contract/integration/real-browser suites.
   Missing entry points/routes are planned prerequisites; a build or health
   failure must remain nonzero, never a placeholder PASS.
   The shared Windows smoke wrapper was corrected/reverified by its assigned
   owner and independently via the checks above; its full runtime smoke remains
   open, not replaced by static dispatch proof.
2. Actual backend-container external Ollama route, readiness, JSON/SSE/tools,
   non-root volume creation/reopen and SQLite WAL/transactions/recovery.
   Host loopback success and failed host alias probes do not prove this route.
3. Windows AND WSL2 full Compose smoke, Nginx service DNS/buffering/timing,
   graceful shutdown, published graphs/history after down/up, immutable
   snapshots after edits, and independently checked teardown residue (A15).
4. Real Hermes production JSON/SSE/two-owner continuation and replay (A07–A09),
   actual waiting-ID process/container restart, resumed owner/output and no
   repeated side effects (A10). Smoke's ordinary completed-history restart
   does not by itself close a waiting-tools restart gate.
5. Actual client compression with production pending IDs; G0 research
   compression is proven for its fixture, not a new production run. Partial
   results, cancellation/late results, expiry, interrupted active inference,
   global2 provider/4 active/20 queued bounds and target metrics require
   current integration/performance evidence (A14/A16).
6. Consistent backup/restore, image shutdown and rollback procedure remain
   unexecuted. No unsafe data deletion is used to obtain green evidence.

The preflight diagnostic was rejected before process execution as
`CreateProcess ... blocked by policy`, with no stated mechanism or native exit;
see [the exact report](research/delivery-preflight.md). It was not retried or
bypassed. The distinct real backend Compose build above did execute successfully;
that does not retroactively validate the rejected network probe.

Exact remaining procedures are in [runbook.md](runbook.md) and
[hermes-compatibility.md](hermes-compatibility.md). Every smoke command fails
nonzero on unavailable prerequisites or a failed assertion, preserves explicit
scope and native subprocess exit codes, and retains its identifiable volume/
fixtures/evidence. No required live gate is reported as passed here.

Operational sources consulted 2026-10-03: Docker's
[volume lifecycle/copy-up](https://docs.docker.com/engine/storage/volumes/), uv's
[Docker integration](https://docs.astral.sh/uv/guides/integration/docker/), and
Nginx's [proxy buffering/timeouts](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
These inform configuration choices; fresh command output remains authoritative
for runtime claims.

## Actual production-image persistence check — 2026-10-04

DevOps followup exercised the production SQLiteRunRepository, GraphValidator
and FileGraphRepository from the immutable-pinned backend image. It did not
start the HTTP server, Ollama, an executor, another service or a fake provider.
The reusable `--persistence-only` mode builds backend only, passes a bounded
Python probe as the one-off Compose command, resets published ports/host aliases,
disables the inherited healthcheck/restart, sets network_mode=none and clears
the fixture API token. The service's UID10001, read-only root, tmpfs,
cap-dropALL, no-new-privileges and own named data volume remain in effect.

Commands executed from PowerShell at D:/Sources/creep:

| Exact command | Exit | Outcome |
| --- | ---: | --- |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-persist-20261004-d1 --persistence-only` | 1 | Image built; verifier fixture omitted running state before claiming activation. Correctly rejected; not a product defect or PASS |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-persist-20261004-d2 --persistence-only` | 1 | Corrected running fixture reached completion guard; verifier omitted declared output activation. Correctly rejected; not a product defect or PASS |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-persist-20261004-d3 --persistence-only` | 0 | Corrected complete fixture passed the executable checks below, native Linux/Python3.11.15/SQLite3.40.1 |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py` | 0 | Current added helper/probe lint; initial line-length failures corrected |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml scripts/smoke_compose.py` | 0 | Current helper format |

The actual command is assembled with subprocess argument arrays; no shell runs
the model/tool pipeline. Inline Compose override travels through stdin and the
Python probe through a base64 argument. The repository helper is the exact
reproducible command/probe source. Successful embedded probe SHA256:
`4baefe5c07ccea13a9d4a6a911ecc3f37a99b51182588c72ba66f91493e68e7a`.
The helper's later added security assertion/hash reporting leaves those probe
bytes unchanged. No failed fixture was reused, overwritten, deleted or reported
as passed; all three projects/containers/volumes are retained separately.

Demonstrated checks:

- Actual writable new named volume as UID10001; production DB uses WAL,
  foreign_keys=1, synchronous=2(FULL), busy_timeout=5000 and one dedicated
  cg-sqlite_0 thread. Cross-thread direct use raises SQLite ProgrammingError.
- Durable checkpoint CAS rejects a stale version; duplicate activation key
  rolls back the complete transaction; concurrent activation claims admit one
  attempt/execution. No inference was actually performed.
- One persisted two-ID tool batch; concurrent exact partial duplicates join
  one claim, changed results conflict, remaining result becomes ready, stale
  frontier cannot overwrite accepted results. Fixed UTC deadline and one
  exposed-batch budget remain unchanged.
- Injected failure after response persistence but before claim sealing rolls
  back response/frontier/claim together. Correct completion seals both claims.
  A foreign-key violation rolls back; foreign_key_check is empty.
- Close/reopen with a new production repository preserves the immutable
  snapshot, completed run, mappings, final response and exact claim replay;
  a nonexact old request conflicts. Six committed monotonic events persist;
  quick_check reports ok.
- Production graph create/publish/save retains original publication/hash.
  Actual Linux file and directory fsync executes. Injected file-fsync failure
  preserves prior draft bytes. Real file and directory symlinks plus path
  traversal are rejected without changing the owned outside marker.

Final fixture counters: one claimed node execution/attempt, one exposed tool
batch, six events. These are persistence fixture counters, not a scheduler,
model throughput or external tool-execution measurement. Close/reopen in one
process is not actual process/container waiting-ID recovery evidence.

Final image ID/index digest:
`sha256:022e7a5d5eedf7b8782659aaa815603dca722384c1f41b9aa6936847b39a6dfe`.
Platform manifest: `sha256:3f545665176f7dd2df71a6b023b3cf217dab3f13c5ca2302f11ff8ecfd720641`;
OCI config: `sha256:222148949fce3e73ba329b5212d722a6055d8ee3d84d6a4f6853493cb7e7dfd1`.
Source SHA256 values read inside that image:

| Exercised module under /app/app | SHA256 |
| --- | --- |
| contracts/api.py | `681b38303bc8d495eeed6d3886bc8665e2de960020ec18b45cdc3d79e86a6c83` |
| contracts/graph.py | `5689267856ca5fef107054066e2995356ff7d2093203849d9209f0e64e6c4e4b` |
| contracts/interfaces.py | `9a5d59c2a85f02e28ae72059c26cd7b39d97e9e03c0fc69aa7a304343834d902` |
| storage/repository.py | `c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15` |
| graphs/repository.py | `ea9dd546c16f55e9e3695fb58d9a8f7670452d180aec0a0c3acd2cbe1a721249` |
| graphs/validator.py | `c1b51dde9c65de68b46aa30307726878e1cc3031d9a757a3172bcc3204f02f0e` |

Concurrent bootstrap's later nonstream metadata correction changed host
contracts/api.py to `19fb6fc72ef296dda1387d78ab82859982ff69029d470492721327e1c48718fc`.
The other five inspected module hashes still matched the image. Evidence is
for the displayed actual image/source snapshot, not a silently relabeled later
tree. Rebuild the complete application after consumer integration.

Retained resource accounting, independently inspected (each exit0):

| Project / container name suffix | Container ID | Status / exit | Retained volume |
| --- | --- | --- | --- |
| cg-persist-20261004-d1 / -persistence | `c8b24a176986b0b012732b6d1a56b6cfdcef8303c6813978d63313437fccf3da` | exited / 1 | cg-persist-20261004-d1_cg_data |
| cg-persist-20261004-d2 / -persistence | `a494be2cd61ef4cc96dba9f697b455a07749a24d7c5cbf03559fa167fc5f5821` | exited / 1 | cg-persist-20261004-d2_cg_data |
| cg-persist-20261004-d3 / -persistence | `5c569db81c2eafacea74726a9fb9850498bad6f217b2c41e9f1946d7ed4f7c81` | exited / 0 | cg-persist-20261004-d3_cg_data |

`docker --context desktop-linux inspect <container-name> --format ...` verified
UID10001:10001, networknone, no port bindings, no-new-privileges, read-only
root, cap-dropALL and exactly its named volume at/data. Final healthcheck
Test=[NONE] and network metadata have no endpoint/IP/gateway. For each project,
`docker --context desktop-linux network ls --filter label=com.docker.compose.project=<project> --format '{{.ID}} {{.Name}}'`
exited0 empty and `docker --context desktop-linux volume inspect <project>_cg_data --format '{{.Name}} {{.Driver}} {{json .Labels}}'`
exited0 showing the exact project-owned local volume. No owned process remains
running, no project network exists, and no cleanup/data deletion was performed.
The final volume retains `/data/evidence.json`, SQLite state, publications,
drafts and owned symlink/fault fixtures; Docker logs retain execution output.

This closes only the bounded actual-image storage/filesystem subset. Current
G2 cycle1 findings remain the runtime owner's independent fix/review gate;
none was exercised or claimed fixed here. Integrated HTTP/runtime/provider/UI,
external route, Nginx stream behavior, real Hermes, Windows/WSL2 application
startup and actual waiting-ID restart remain OPEN. No independent G5 PASS.

## Compose parameter-file correction — 2026-10-04

The d1/d2/d3 records above describe their original executed stdin dispatch.
They remain historical evidence; no previous invocation is relabeled. The
current helper now writes its literal override to a uniquely owned UTF-8/LF
temporary YAML file, closes it before launching Compose and passes its absolute
native path through `-f`. Python running on Windows supplies a Windows path;
Python running in WSL supplies a Linux path. `run -d -T` and DEVNULL stdin avoid
TTY/prompts or depending on stdin for parameters. A `finally` unlinks only that
new parameter file after dispatch, including launch/nonzero failures; containers,
volumes and evidence are retained. No global configuration or source outside
scripts/smoke_compose.py and this document was edited by this followup.

Commands and executable results:

| Exact command | Exit | Outcome |
| --- | ---: | --- |
| `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py` | 0 | Pinned Ruff lint |
| `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check scripts/smoke_compose.py` | 0 | Pinned Ruff formatting |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-persist-20261004-filecheck --validate-only` | 0 | Real Windows/desktop-linux Compose configuration; no resources created |
| `python scripts/dev.py smoke-compose --project cg-persist-20261004-wslfilecheck --file D:/Sources/creep/compose.yaml --validate-only` | 0 | Real Windows→WSL/default Linux daemon configuration, explicit file converted to /mnt/d/Sources/creep/compose.yaml; no resources created |
| `uv --system-certs run --project backend --locked python -c $probeCode` | 0 | Bounded argv/file fixture below on Windows |
| `wsl --cd /mnt/d/Sources/creep --exec python3 -c $probeCode` | 0 | Same bounded argv/file fixture on WSL |
| `python scripts/smoke_compose.py --context desktop-linux --project cg-persist-20261004-d4-file --persistence-only` | 0 | Actual rebuilt backend image and unchanged production persistence probe, dispatched using a real override file |

For the two argv/file fixture commands, `$probeCode` was this literal code
provided as a command argument (not stdin). This is helper dispatch verification
with intercepted subprocess execution, separate from the real d4-file run:

```python
import contextlib, hashlib, importlib.util, io, json, subprocess
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("smoke", Path("scripts/smoke_compose.py").resolve())
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
seen = []
def launch(command, **kwargs):
    assert "input" not in kwargs and kwargs["stdin"] == subprocess.DEVNULL
    assert "-" not in command and "-T" in command
    parameter = Path(command[command.index("-f") + 1])
    assert parameter.is_absolute() and parameter.is_file()
    content = parameter.read_text(encoding="utf-8")
    assert "network_mode: none" in content and "ports: !reset []" in content
    assert "CG_API_TOKEN: ''" in content and "\r" not in content
    with parameter.open("rb") as readable:
        assert readable.read()
    seen.append(parameter)
    return subprocess.CompletedProcess(command, 7, "", "")
with patch.object(m, "run", return_value=""), patch.object(m.subprocess, "run", side_effect=launch):
    try:
        m.persistence_smoke(["docker"], ["docker", "compose"], "owned-argv", "owned-argv_cg_data")
    except m.CommandFailure as failure:
        assert failure.exit_code == 7
    else:
        raise AssertionError("native failure was lost")
assert len(seen) == 1 and not seen[0].exists()
def launch_error(command, **kwargs):
    launch(command, **kwargs)
    raise OSError("owned fixture dispatch failure")
with patch.object(m, "run", return_value=""), patch.object(m.subprocess, "run", side_effect=launch_error):
    try:
        m.persistence_smoke(["docker"], ["docker", "compose"], "owned-error", "owned-error_cg_data")
    except OSError:
        pass
    else:
        raise AssertionError("launch error was lost")
assert len(seen) == 2 and not seen[1].exists()
print(json.dumps({"checks": ["absolute temporary file argv", "UTF8 LF closed readable override", "no stdin/TTY", "native exit7", "cleanup on subprocess failure", "cleanup on launch error"], "probe_sha256": hashlib.sha256(m.PERSISTENCE_PROBE.encode()).hexdigest(), "remaining_parameter_files": sum(p.exists() for p in seen)}))
```

Both fixture outputs reported all six checks and remaining_parameter_files=0.
An additional `wsl --cd /mnt/d/Sources/creep --exec python3 -c $wslFileCode`
exited0 after the real WSL Docker Compose CLI read and validated the newly
created Linux temporary override merged with compose.yaml. The fixture skipped
build and intercepted only the launch to replace `run` with `config --quiet`;
it created no application resources and verified parameter-file cleanup.
Literal `$wslFileCode` supplied as an argument:

```python
import importlib.util, subprocess
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("smoke", Path("scripts/smoke_compose.py").resolve())
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original = subprocess.run
seen = []
def actual_file_config(command, **kwargs):
    parameter = Path(command[command.index("-f", command.index("-f") + 1) + 1])
    seen.append(parameter)
    assert parameter.is_file() and "input" not in kwargs
    result = original(command[:command.index("run")] + ["config", "--quiet"], **kwargs)
    assert result.returncode == 0, "real merged Compose file configuration failed"
    return subprocess.CompletedProcess(command, 7, "", "")
compose = ["docker", "compose", "-p", "cg-persist-20261004-wslparam", "-f", str(m.ROOT / "compose.yaml")]
with patch.object(m, "run", return_value=""), patch.object(m.subprocess, "run", side_effect=actual_file_config):
    try:
        m.persistence_smoke(["docker"], compose, "cg-persist-20261004-wslparam", "cg-persist-20261004-wslparam_cg_data")
    except m.CommandFailure as error:
        assert error.exit_code == 7
    else:
        raise AssertionError("dispatch fixture failed")
assert len(seen) == 1 and not seen[0].exists()
print("WSL actual Compose merged parameter-file config exit0; owned override cleaned; no resources created")
```

The unchanged embedded probe SHA256 remains
`4baefe5c07ccea13a9d4a6a911ecc3f37a99b51182588c72ba66f91493e68e7a`.
Current parameter-file helper source SHA256:
`0b558878d9c1233a72f58bf75f0d6cabba6713a4c25076c9e263bfad9cbff4ce`.
Windows helper-prefix temporary-file inventory after the real run also exited0
and reported zero remaining files; only newly created parameter files were
deleted, no existing resources or evidence.

The d4-file build used the same Python3.11.15 and uv0.11.28 immutable base pins
documented above. Its actual image ID/index is
`sha256:e8fb0af386eb5b0da2334601aa285ddc24eea5bc74d5b54bdf7359f08dd2e6c1`;
platform manifest `sha256:b6a8460281133134820cda87a42a0c06db2a9b8531c60b04ab107bed39697aef`;
OCI config `sha256:b8e3eda8eb46bb7c4dd8927161b187c7a89dde8a6731411c08c13bb2487e4cb4`.
The six production module hashes printed by d4 match the earlier table except
contracts/api.py is now
`19fb6fc72ef296dda1387d78ab82859982ff69029d470492721327e1c48718fc`.
Actual Python3.11.15/SQLite3.40.1 storage/filesystem checks again passed, with
one fixture execution/attempt, one tool batch, six events and quick_check=ok.
No HTTP server, inference, external network diagnostic, tool or provider ran.
The image includes the concurrently composed source snapshot; this probe does
not exercise or validate the complete corrected engine or HTTP application.

New retained resource, independently inspected:

- Context desktop-linux; project cg-persist-20261004-d4-file.
- Container cg-persist-20261004-d4-file-persistence,
  ID `d6aeb26424e241756e016bdb8dc03154d7102246ca505ad085a96bdaeb3ee87f`,
  exited0; volume cg-persist-20261004-d4-file_cg_data, local driver, own exact
  Compose project label, mounted/data and containing evidence.json/SQLite/files.
- `docker --context desktop-linux inspect cg-persist-20261004-d4-file-persistence --format '{{.Id}} {{.State.Status}} {{.State.ExitCode}} {{.Image}} {{.Config.User}} {{.HostConfig.NetworkMode}} {{json .HostConfig.SecurityOpt}} {{json .HostConfig.PortBindings}} {{.HostConfig.ReadonlyRootfs}} {{json .HostConfig.CapDrop}} {{json .Config.Healthcheck.Test}} {{json .Mounts}}'`
  exited0: UID10001:10001, networknone, no-new-privileges:true, ports{}, read-only
  root, cap-dropALL and healthcheckNONE.
- `docker --context desktop-linux network ls --filter label=com.docker.compose.project=cg-persist-20261004-d4-file --format '{{.ID}} {{.Name}}'`
  exited0 empty; no project network or running owned process remains.
- `docker --context desktop-linux volume inspect cg-persist-20261004-d4-file_cg_data --format '{{.Name}} {{.Driver}} {{json .Labels}}'`
  exited0, exact retained project-owned volume. Original d1/d2/d3 containers,
  volumes and evidence remain untouched; no down -v, prune or user-data deletion.

This corrects the command-input deviation and proves actual file dispatch only
with the bounded persistence subset. G5 independent review remains0/3; full
integrated Compose HTTP/UI/health/SSE/timeouts, external Ollama routing, real
Hermes, Windows/WSL2 application startup and waiting-ID restart gates remain
OPEN. Static Windows→WSL validation is not application startup evidence.

## Integrated delivery preparation — 2026-10-04

The current helpers add real public direct ordinary/multiturn JSON/SSE and native
function request/result checks (seven inference HTTP exchanges; zero tool
execution), SSE arrival/header observations, actual-container upstream/image/
source/Nginx evidence, and same-model three-call diamond/sequential measurements.
Optional existing native Hermes parameters request literal cg/synthesis,
two-owner serialized continuation/replay, a real waiting-tools backend restart,
and original native ContextCompressor execution. No transport, executor,
provider or summary implementation is replaced.

The JSON Hermes fixture creates synthesis only by POST in a new smoke project;
an existing graph is a conflict, never overwritten. Restart checks exact
project/backend/volume identity and changed host process PID/start time before
the first read; original opaque IDs/owners/results/counters must survive and
the original agent must complete on them. Compression uses only the new isolated
HERMES_HOME auxiliary configuration, original native client and external local
Ollama. Closed inert turns trigger one compression; latest IDs/raw results must
remain equal. Requested flags must actually execute or fail; omitted flags keep
their gates OPEN.

Preparation commands:
- `uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py`: exit0.
  Final invocation reported one cache-file access-denied warning while all lint
  passed; no policy/cache configuration was changed.
- `uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml --check scripts/smoke_compose.py scripts/smoke_hermes.py`: exit0, two files formatted.
- `python scripts/smoke_compose.py --help` and
  `python scripts/smoke_hermes.py --help`: exit0 each, no runtime effects.
- `uv --system-certs run --project backend --locked python -c $fixtureCode`:
  exit0 for the literal argument fixture below. Actual Graph/GraphSnapshot/
  GraphValidator validate both Hermes graph shapes and both target topologies;
  intercepted completion fixtures verify timing/call-count reporting; the
  actual SSE parser accepts DONE and rejects premature EOF. It performs no
  Docker/server/Ollama/native-Hermes call.

Initial source lint exited1 for line lengths/import spacing and was corrected.
An initial inline fixture exited1 with AttributeError because the fixture used
a nonexistent GraphSnapshot.capture factory; corrected to the authoritative
from_graph method before the successful run. These are preparation failures,
not fabricated live successes or application defects.

Literal $fixtureCode:

```python
import importlib.util, json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path("backend").resolve()))
from app.contracts.graph import Graph
from app.contracts.interfaces import GraphSnapshot
from app.graphs.validator import GraphValidator
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path("scripts",name+".py").resolve())
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
compose,hermes=load("smoke_compose"),load("smoke_hermes")
validator=GraphValidator()
for count in (1,2):
    graph=Graph.model_validate(hermes.graph_fixture("synthesis","gemma4:12b",[Path("D:/owned-fixture"+str(i)+".txt") for i in range(count)],"none"))
    validator.compile(GraphSnapshot.from_graph(graph))
    assert sum(n.tools_enabled for n in graph.nodes if n.type=="llm")==count
graphs=[]
def request(base,path,**kwargs):
    if path=="/api/graphs":
        graph=Graph.model_validate(kwargs["body"]); validator.compile(GraphSnapshot.from_graph(graph)); graphs.append(graph); return graph.model_dump()
    if path.endswith("/publish"): return {}
    if path=="/api/runs": return {"run_id":"fixture"+str(len(graphs))}
    return {"run":{"status":"completed","upstream_attempts":3,"node_executions":3,"queue_seconds":0.125},
        "activations":[{"node_id":node,"started_at":"2026-10-04T00:00:00+00:00","ended_at":"2026-10-04T00:00:01+00:00"} for node in ("left","right","final")]}
with patch.object(compose,"json_request",side_effect=request):
    evidence=compose.performance_smoke("fixture://no-network","gemma4:12b","none")
assert [r["shape"] for r in evidence["results"]]==["diamond","sequential"]
assert all(r["upstream_attempts"]==3 and r["queue_seconds"]==0.125 for r in evidence["results"])
assert graphs[0].edges[1].source=="input" and graphs[1].edges[1].source=="left"
class Response:
    headers={"Content-Type":"text/event-stream","X-Accel-Buffering":"no"}
    def __init__(self,lines): self.lines=lines
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def __iter__(self): return iter(self.lines)
trace={}
with patch.object(compose,"request",return_value=Response([b": heartbeat\n",b"data: {\"choices\":[]}\n",b"data: [DONE]\n"])):
    compose.collect_sse("fixture://no-network","/v1/chat/completions",trace=trace)
assert trace["done"] and trace["comment_heartbeats"]==1 and trace["x_accel_buffering"]=="no"
with patch.object(compose,"request",return_value=Response([b"data: {\"choices\":[]}\n"])):
    try: compose.collect_sse("fixture://no-network","/v1/chat/completions")
    except RuntimeError: pass
    else: raise AssertionError("truncated SSE falsely passed")
print(json.dumps({"result":"helper fixture checks passed","scope":"real DTO/topology validation and intercepted helper/SSE behavior only; no Docker/server/Ollama/Hermes execution"}))
```

backend/Dockerfile now also imports production jsonschema during its locked
dependency build. Actual builds/startup wait for the coordinator's explicit
release of UI8000/5173 and the stable promoted jsonschema4.26.0 lock/runtime
handoff. No preparation build, service startup, inference, tool or restart has
executed. The exact future Windows/WSL2 commands are in runbook.md and native
flags in hermes-compatibility.md. All newly added live gates and G5/G6 independent
reviews (0/3 each) remain OPEN until fresh executed evidence closes them.

### Authoritative G2 blocker and native fallback preparation

G2-runtime's terminal independent review cycle3/3 reports FAIL/BLOCKED (F5).
Valid Draft3 schema-valued `extends`/`type` local references are omitted by
controller-schema rebasing; affected actual scheduler runs end in
`upstream_error`. The accepted schema profile is unchanged. No automatic fourth
review, fix, profile narrowing or renamed task group is authorized. This blocker
prevents MVP completion even if independent delivery/Hermes checks succeed.
The durable tasks/decisions/review artifacts contain the authoritative finding.
One initial reviewer full run also encountered an unidentified test failure and
a native Windows access violation; bounded later 475-backend/21-frontend runs
passed, but the crash remains an unreproduced verification risk, not a fixed
defect or proof that F5 is resolved.

An explicit native fallback is now prepared for the coordinator-authorized case
where actual application-container routing fails: same production Uvicorn code,
one owned process, fresh isolated data, direct seven-exchange JSON/SSE/tool
transport, target measurements, real pinned Hermes, pending-ID compression and
an actual waiting-tool process replacement. Its fixed endpoint/ownership guards
refuse unrelated listeners/project restarts, retain evidence/data/logs, and stop
only its own process handle. Neither this mode nor helper fixtures prove
container/Nginx/Windows-WSL2 acceptance. The commands are in runbook.md; all newly
prepared live checks remain unexecuted while the coordinator holds build/start
for G4 fixes and independent browser review. Existing d1/d2/d3/d4 records and
retained volumes are unchanged.
### Additional helper guard checks (preparation only)

Executed `uv --system-certs run --project backend --locked ruff format` on both
owned helpers: exit0; subsequent `ruff check` and `ruff format --check`: exit0.
Initial check failures (five findings, then one unused noqa) were corrected.
Both `python scripts/smoke_{compose,hermes}.py --help` invocations exited0.
The existing real-DTO/graph/target/SSE helper fixture rerun exited0.
The first new direct fixture exited1 because its intercepted completion omitted
required `object=chat.completion`; adding that fixture field yielded exit0.
No real backend, Docker, network, inference, restart or tool was exercised by
these intercepted checks. G5/G6 live gates and independent reviews remain OPEN.

The following exact literal code blocks were passed as `python -c` arguments
through `uv --system-certs run --project backend --locked` (each exit0), without
stdin/TTY; generated native-guard temp files belonged solely to the fixture:

```python
import json, os, tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.smoke_hermes import NativeBackend, SmokeFailure
class Process:
    counter=100
    def __init__(self,*args,**kwargs):
        Process.counter+=1; self.pid=Process.counter; self.returncode=None
        assert kwargs["stdin"] == -3 and kwargs["stderr"] == -2
        assert kwargs["env"]["CG_DATA_DIR"].endswith("backend-data")
        assert kwargs["env"]["OLLAMA_BASE_URL"] == "http://127.0.0.1:11434/v1"
        assert kwargs["env"]["CG_API_TOKEN"] == "fixture-token"
        assert "OTHER_SECRET" not in kwargs["env"]
        assert args[0].count("1")==1 and "--no-access-log" in args[0]
    def poll(self): return self.returncode
    def terminate(self): self.returncode=17
    def wait(self,timeout): assert timeout == 35; return self.returncode
    def kill(self): raise AssertionError("unexpected kill")
class Port:
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def bind(self,target): assert target == ("127.0.0.1",8000)
with tempfile.TemporaryDirectory(prefix="cg-native-guard-") as temp:
    work=Path(temp)
    with patch.dict(os.environ,{"OTHER_SECRET":"fixture-value"}), patch("scripts.smoke_hermes.subprocess.Popen",Process), patch("scripts.smoke_hermes.socket.socket",return_value=Port()), patch("scripts.smoke_hermes.exchange",return_value=({"storage_ready":True},{})) as health:
        import sys
        backend=NativeBackend(Path(sys.executable),work,"http://127.0.0.1:8000","http://127.0.0.1:11434/v1","fixture-token")
        backend.start(initial=True)
        evidence=backend.restart("dedicated-fixture")
        assert evidence["pid_before"] != evidence["pid_after"] and evidence["prior_exit_code"]==17
        assert health.call_count==2 and health.call_args.kwargs["timeout"]==3
        backend.close()
        with patch.object(backend,"hash_sources",return_value={}):
            try: backend.start()
            except SmokeFailure: pass
            else: raise AssertionError("source mutation not rejected")
print(json.dumps({"result":"native ownership guard fixture passed","scope":"intercepted process/socket/HTTP behavior; no native server, Docker, inference or tools executed"}))
```

```python
import io,json,urllib.error
from unittest.mock import patch
from scripts import smoke_compose as smoke
ordinary={"object":"chat.completion","choices":[{"message":{"role":"assistant","content":"Fixture greeting"},"finish_reason":"stop"}]}
tool={"choices":[{"message":{"role":"assistant","content":None,"tool_calls":[{"id":"native-fixture-id","type":"function","function":{"name":"smoke_probe","arguments":"{\"value\":\"SMOKE_OK\"}"}}]},"finish_reason":"tool_calls"}]}
json_calls=[]; sse_calls=[]
def request(base,path,*,body):
    json_calls.append(body)
    if body["model"].startswith("ollama/cg-smoke-unknown"):
        raise urllib.error.HTTPError("fixture://offline",404,"Unknown",{},io.BytesIO(b'{"error":{"code":"unknown_model"}}'))
    if body.get("tool_choice") and isinstance(body["tool_choice"],dict): return tool
    return ordinary
def sse(base,path,*,body,trace=None):
    sse_calls.append(body)
    if trace is not None: trace.update(x_accel_buffering=None,done=True)
    if isinstance(body.get("tool_choice"),dict):
        return [{"choices":[{"delta":{"tool_calls":[{"index":0,"id":"native-fixture-id","function":{"name":"smoke_probe","arguments":"{\"value\":\"SMOKE_OK\"}"}}]},"finish_reason":None}]},{"choices":[{"delta":{},"finish_reason":"tool_calls"}]}]
    return [{"choices":[{"delta":{"content":"Fixture answer"},"finish_reason":"stop"}]}]
with patch.object(smoke,"json_request",side_effect=request),patch.object(smoke,"collect_sse",side_effect=sse):
    report=smoke.direct_smoke("fixture://offline","gemma4:12b",require_nginx=False)
assert len(json_calls)==5 and len(sse_calls)==3 and report["http_inference_exchanges"]==7
assert json_calls[3]["messages"][-1]["tool_call_id"]=="native-fixture-id"
assert sse_calls[2]["messages"][-1]["tool_call_id"]=="native-fixture-id"
assert report["tools_executed"]==0
print(json.dumps({"result":"direct transport helper fixture passed","scope":"intercepted HTTP only; no inference or executor; native manual tool-result forwarding and seven-exchange count"}))
```

```python
import importlib.util,json,subprocess
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("hermes",Path("scripts/smoke_hermes.py").resolve())
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
project="cg-smoke-owned-guard"; commands=[];states=[]
def dispatch(arguments,**kwargs):
    assert kwargs["stdin"]==subprocess.DEVNULL and kwargs["timeout"]==90 and "input" not in kwargs
    commands.append(arguments)
    if arguments[-2:]==["-q","backend"]: result="ownedcontainer"
    elif "Config.Labels" in arguments[-1]: result=json.dumps({"com.docker.compose.project":project,"com.docker.compose.service":"backend"})
    elif ".Mounts" in arguments[-1]: result=json.dumps([{"Name":project+"_cg_data"}])
    elif ".State" in arguments[-1]:
        states.append(1);result=json.dumps({"Running":True,"StartedAt":str(len(states)),"Pid":100+len(states)})
    elif "restart" in arguments: result="restarted"
    else: raise AssertionError(arguments)
    return subprocess.CompletedProcess(arguments,0,result,"")
with patch.object(m.subprocess,"run",side_effect=dispatch),patch.object(m,"exchange",return_value=({"storage_ready":True},{})) as health:
    result=m.owned_restart("http://127.0.0.1:8080","","cg-smoke-owned-guard",Path("compose.yaml"),"desktop-linux")("fixture-run")
    assert result["pid_before"]!=result["pid_after"] and result["run_id"]=="fixture-run"
    assert health.call_args.kwargs["timeout"]==3
assert sum("restart" in command for command in commands)==1
commands.clear()
def foreign(arguments,**kwargs):
    if "Config.Labels" in arguments[-1]:
        commands.append(arguments);return subprocess.CompletedProcess(arguments,0,json.dumps({"com.docker.compose.project":"other-project","com.docker.compose.service":"backend"}),"")
    return dispatch(arguments,**kwargs)
with patch.object(m.subprocess,"run",side_effect=foreign):
    try:m.owned_restart("http://127.0.0.1:8080","",project,Path("compose.yaml"),None)("fixture-run")
    except RuntimeError:pass
    else:raise AssertionError("foreign project was restarted")
assert not any("restart" in command for command in commands)
print("Owned-restart command/identity guards passed; intercepted only, no Docker/restart/network/tool executed")
```

### Windows production images — build-only release

Coordinator-authorized build-only phase on2026-10-04, project
`cg-smoke-win-20261004-db7fbae0`, Docker context `desktop-linux`, Linux/amd64:
before and after build, exact project-label container/network queries and exact
named-volume query returned no resources. Both local image tags were initially
absent. No profile, service startup, listener, upstream diagnostic/inference or
tool was executed. Commands executed with argument lists and stdinDEVNULL:

```powershell
docker --context desktop-linux compose --progress plain -p cg-smoke-win-20261004-db7fbae0 -f D:/Sources/creep/compose.yaml config --quiet
docker --context desktop-linux compose --progress plain -p cg-smoke-win-20261004-db7fbae0 -f D:/Sources/creep/compose.yaml build backend frontend
docker --context desktop-linux image inspect cg-smoke-win-20261004-db7fbae0-backend
docker --context desktop-linux image inspect cg-smoke-win-20261004-db7fbae0-frontend
```

All exited0. Build used the four immutable image-index pins recorded above.
Backend `uv sync --locked --no-dev` resolved31/installed22 exact production
packages, including jsonschema4.26.0 plus attrs26.1.0,
jsonschema-specifications2025.9.1, referencing0.37.0 and rpds-py2026.6.3.
Build executed production imports and asserted jsonschema4.26.0; output showed
CPython3.11.15 and native LinuxSQLite3.40.1. Frontend's pinned Node24.14.0/
npm11.9.0 assertion and `npm ci` layer were reused from prior executed cache;
current actual `npm run build` ran both strict TypeScript projects and Vite8.3.2
bundling (265modules). Warnings: upstream React Flow `use client` directive and
509.13KB minified JS chunk. Neither warning prevented the build; no scope
expansion or warning suppression was introduced.

| Artifact | Exact SHA256 |
| --- | --- |
| Backend image index | `0c4c525f822c8b3ff2d7cd3e7b4dceeddefbb0c50edbb3a2ddd9306dd0a4e97d` |
| Backend platform manifest | `643cde256854c5fb3484ffe65dc7c13f0a9f1f4a0a4497d6f10b76268616e689` |
| Backend image config | `1bff99401f7c81b24ed354b20769e4227f356552caea58271b17f7f73818ea7d` |
| Frontend image index | `4be985c5a21868c246250fc7861faafa1f7120ad5395cb7f0869afdf0d6689b5` |
| Frontend platform manifest | `b3b37431e699dda9f5083940527c06515c8c60954b0d9f745de971d5e6c6b866` |
| Frontend image config | `ad6d61c51e063121b78f28d6801f14e8be68b90cc17852875e807f3d8ac4617d` |
| Backend lock | `431c899b24fb68a2c5189dac324ef48ea63c690926d8934a1e54cb3bc84e1b07` |
| Backend Dockerfile | `f5c2a882efdea6f6d5352ebc5973fdb670c944bbe9641034b0c8bae38c843a20` |
| Frontend Dockerfile | `50f8b30c973ee6e03e51b3cecdb7e9cd4849d13957f93d801a034681a5bfdd21` |
| Frontend lock | `229187d9a35f662a2b508510c72736286fa555fa747de20fc5d68bb83f341242` |
| Production main | `dae170c7cf7055c10a10eb0ecd3d1456ab19571d0e6a3538c1a9a5547e3deb83` |
| Production chat route | `b68226b543b52fd5d2e68df634d68d64bc304c08a9d7cf63acebdae6ea68f058` |
| Corrected graph route | `dc5bb15dcb13771700d4a580868bc86af768b733f7ce752775038d572002dab2` |
| Known-blocked engine | `b8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6` |
| Production storage | `c5254c505162dd82424089df21532642f0bd46c69ebac594c11570d1b0e31c15` |
| Corrected App.tsx | `c0e3c6c8f2ddde4c49212ae5afed5c70175ba828fcb4f0a1f8c957f708dc6647` |
| Corrected Editor.tsx | `fa28f5189f633b603b5d5bebba9b39ade56954897567ce724c002b1ec2f41bb1` |

Source hashes above were checked unchanged before/after the build. Selected
image metadata confirms Linux/amd64 and users10001:10001/101:101, correct
one-worker/no-access-log backend command and marker-only Nginx entrypoint.
Compose-generated local project image tags end in `:latest`; those are locally
built outputs identified by the hashes above, not unbounded dependency/base
pulls. Images and build cache are retained. Prior d1/d2/d3/d4 exited containers
and volumes are untouched. Production source changes require another build.
Full runtime/Hermes/Windows-WSL2/target/restart checks and G5/G6 independent
reviews remain OPEN until the coordinator's separate service-start release and
fresh executable evidence. G2F5 remains BLOCKED3/3; build success cannot close it.

Prepared route evidence now runs in the actual owned application container
before model discovery/application inference. It first checks UID10001, new-data
write/fsync permission and the production SQLite WAL/quick_check, then reads
external inventory/version/model digests. Its success or sanitized failure
type/errno is printed and retained in the fresh volume's container-probe.json;
failed routing exits nonzero, preserves that evidence and performs only scoped
container/network teardown. It neither changes the default upstream nor retries
a diagnostic. This code remains unexecuted during build-only hold. Final pinned
helper Ruff format/check after the change both exited0.

### Explicit CI Ruff configuration correction

The coordinator's fresh `python scripts/dev.py lint` exited1: three E501 lines
in owned smoke helpers were missed by the earlier bare Ruff invocation, which
used different discovery/configuration from CI. The earlier exit0 is real but
was inadequate CI evidence, and is not relabeled. Wrapped only the embedded
model list, unchanged Go template concatenation and native stop-semantics
literal. Exact configured check initially exited0; configured format-check
exited1 because earlier generic formatting used a different line length.
Applied the pinned formatter with the repository's explicit configuration:

```powershell
uv --system-certs run --project backend --locked ruff format --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py
uv --system-certs run --project backend --locked ruff check --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py
uv --system-certs run --project backend --locked ruff format --check --config backend/pyproject.toml scripts/smoke_compose.py scripts/smoke_hermes.py
```

All final commands exited0. All four literal prepared fixtures above were rerun
as pinned `python -c` arguments: real DTO/topology/SSE0, owned Compose restart
identity0, seven-exchange direct transport0 and native process/env/source guard0.
They remain intercepted verifier checks, not live execution. No production
image source changed; no rebuild/start/route/restart/inference/tool occurred.

Coordinator pre-start consolidation: fresh exact `python scripts/dev.py lint`
now exited0 (49Ruff files, generated contract drift and TypeScript). Coordinator
also reports522 backend tests passed in37.26s,49 focused API checks and three
barrier checks. These are coordinator evidence, not this helper's executed live
checks. The latest API correction changed only test_runs.py; production chat
b68226b543b52fd5d2e68df634d68d64bc304c08a9d7cf63acebdae6ea68f058,
engineb8ff723dea5338d3c56d88413e89936e81c105c46991ae914517dbbd049d2cd6
and corrected G4 sources remain coherent with the build-only images. G4's
cycle2 independent browser review owns native8000/5173 until its terminal
cleanup; actual delivery startup remains held. G2F5 BLOCKED3/3 is unchanged.

Native CLI boundary check used `subprocess.run([...], stdin=DEVNULL,
capture_output=True)` through the same pinned `python -c`: invalid default
8080 native endpoint, external example.invalid upstream, and simultaneous
native/Compose restart flags all produced argparse exit2 before creating work
or invoking a server/Docker/network/tool. This is parser-only evidence.

### Actual startup failure and delivery correction

After G4cycle2 PASS and positive listener cleanup, coordinator released actual
startup. Windows command using fresh projectcg-smoke-win-20261004-db7fbae0,
modelgemma4:12b/stored reasoningnone and pinned native Hermes flags exited1 at
`compose up -d --wait --wait-timeout120`: backendHealthy/frontendunhealthy.
No route probe, inference, Hermes tool, target measurement or restart executed.
Scoped down45 exited0; independent queries found no owned containers/networks
and retainedcg-smoke-win-20261004-db7fbae0_cg_data. Initial teardown removed
startup logs before recording them: an actual verifier adequacy gap, not proof
of a particular cause. Rebuild reused unchanged platform manifests/configs but
generated fresh attestations/indexes (backend82e0d865854db8f78092f640c2f8d253988d238c03ea721e851afe24c266b789,
frontend19f441d3e24c01e8643501914f2225bf22eebba4a38fb17c0a634a5124cd6202).

Added safe failure capture before teardown: only owned selected container
State/health and frontend startup logs, no environment/auth/header/backend
history dump. Failure capture cannot replace the original exit/cleanup. One
coordinator-authorized fresh startup reproduction project
cg-smoke-win-startup-20261004-5e7c9140 exited1 before route/inference, with exact
retained log `.venv/compose-failure-cg-smoke-win-startup-20261004-5e7c9140.json`:
`mkdir() "/var/cache/nginx/fastcgi_temp" failed (30: Read-only file system)`.
BackendHealthy/frontend restarting exit1, no frontend health log entries.
Scoped down45 exited0; own containers/network absent and second volume retained.

Corrected only frontend/nginx.conf by routing default fastcgi/uwsgi/scgi temp
directories into existing writable/tmp, retaining non-root/read-only/cap-drop
controls and disabled proxy buffering/cache. Configured pinned helper formatter
and Ruff check exited0; all subprocess helper inputs now explicitly use DEVNULL.
New projectcg-smoke-win-fixed-20261004-674d0a1a actual rebuilt frontend platform
94926f1ba0b97eb220da3e3a2b06b9a3f72cdd3816f34fb5ef569c9c0710e0d4,
config047f49495adfa5d0b693b4b9446dabdefddbf7fcfc5528f50787e48663e1c4ea,
index3020298b6b1100c48bcca65baa4938555f7cc4f05215e13eabdd866d47561e1c.
Both actual services becameHealthy. Actual-container UID10001/data write+fsync,
native LinuxSQLite3.40.1 WAL/quick_checkok, production imports/version metadata
(jsonschema4.26.0) and frozen source hashes were verified. The unchanged default
http://host.docker.internal:11434/v1 reached external Ollama0.33.3; Gemma4:12b
digest4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c
matches research. Container-probe.json retains this measured evidence in the
new volume. Earlier host-only route failures do not describe this demonstrated
application-container route. No endpoint/user Ollama/network mutation occurred.
The corrected full Windows smoke is in progress; later phases are not passed
until their exact final evidence and exit are recorded. KnownG2F5 staysBLOCKED.

The corrected whole Windows helper then exited1 at its strict final JSON
assertion (`Expected a successful final JSON completion`), before target/Hermes
phases. Both servicesHealthy; selected state/frontend log retained at
.venv/compose-failure-cg-smoke-win-fixed-20261004-674d0a1a.json. Scoped teardown0
left no ownedcontainers/network and retained that third volume. The prior
verifier did not label the failing phase or safe finish metadata; that failure
is UNREPRODUCED/unassigned, not a proven/fixed API or model defect.

Coordinator authorized one bounded pure direct reproduction. Added metadata
only (phase/object/finish/visible length/tool count/wall) before unchanged strict
finishstop assertions; no raw content/arguments/reasoning/auth is captured.
`--direct-only` stops after public transport checks and scoped teardown, skipping
graph execution, target/Hermes/native effects. Configured Ruff format/check0;
the intercepted direct fixture added its missing standard object field and
passed0. Actual command:

```powershell
python scripts/smoke_compose.py --context desktop-linux --project cg-direct-diag-20261004-30b1d8a1 --model gemma4:12b --direct-only
```

Exit0, with same original prompts/profile/max_tokens2048 and strict assertions.
All seven real exchanges passed: ordinary JSON, multiturn JSON/SSE, native
function request JSON/SSE and manually supplied native role-tool result JSON/SSE.
Tools executed0. JSON metadata: ordinary stop/6visiblechars/1.625s; multiturn
stop/8chars/1.797s; native tool_calls/onecall/1.281s; result stop/3chars/0.344s.
Unknown physical model returned404/unknown_model. Nginx ordinary SSE had76frames,
DONE/X-Accel-Bufferingno, firstdata0.312s/wall1.578s; native toolSSE83frames and
resultSSE3frames. Native JSON argument SHA256
513c2cb3af30067c4fc62befbadd7ae76168ba41710bd6883c4ff2c55157089a.
Actual-container route/storage checks again0. Scoped down45/query residue0;
fourth ownedvolume cg-direct-diag-20261004-30b1d8a1_cg_data retained. No fixture
instruction/assertion/product change was justified, and the earlier whole-smoke
failure remains in the record. It is not attributed to the independently
discovered malformed-upstream Unicode defect, whose correction belongs to G3.

New complete planned projectcg-smoke-win-full-20261004-417276aa is executing
remaining stages with safe diagnostics. Its direct JSON/SSE checks have passed
with the original strict assertions; actual Nginx1.30.5/runtime timeout and
security checks reached completed-history restart then new-container down/up
on the same volume. Native waiting-ID/Hermes/compression and target evidence
remain unclosed until their returned results. Actual provider6dd84a... and
sse073da... hashes identify this pre-Unicode-fix valid-upstream image; later
corrected images must receive fresh coherent evidence rather than inheriting it.
### Windows target/native subset and original-client observer correction

Actual full projectcg-smoke-win-full-20261004-417276aa exited1 in the native
Hermes verifier: diagnostic run IDs absent. Prior phases executed successfully:
seven direct JSON/SSE exchanges; Nginx1.30.5 with actual proxy-read/proxy-send/send
timeouts1860s above independent1800s budgets; disabled buffering and live95-frame
SSE(first0.234s/wall1.625s/DONE/XAccelno); native toolSSE117frames/result3frames;
UID10001/101, read-only, capdropALL, no-new-privileges; completed-history backend
restart; new-container down/up preserving publication/history/revision1 snapshot.
Runfceb8977b4614c5592bcf0bfb4e5e2a3 retained graphhash
853950a557f692e94238fab64eb10cb15eb9a6dace67f795a813a8ad775fff6b.
Original/recreated containers used the exact same image IDs: backend
3d33311fa422e28eced5944e7132e6a64830d6c1bd673c75c677e284cb0fbae8 and frontend
8b483756f980a2a7dcd841781a2d68aa2e230627e615b3babea9e27dea5c70dc.
Full selected metadata is retained in
.venv/compose-failure-cg-smoke-win-full-20261004-417276aa.json.

Real target Gemma4:12b, generation temperature0/max_tokens2048/reasoningnone:

| Shape | Wall seconds | Queue seconds | Left/right/final duration seconds | Calls/executions |
| --- | ---: | ---: | --- | --- |
| Diamond | 1.515 | 0.004944 | 0.829940/0.599422/0.439565 | 3/3 |
| Sequential | 1.531 | 0.006202 | 0.456379/0.454390/0.474423 | 3/3 |

Diamond branch starts23:46:10.316271/23:46:10.321728UTC overlapped; final began
23:46:11.159584 after both. Sequential starts23:46:11.812541/23:46:12.282961/
23:46:12.749132 followed prior completion. One sample per shape, topology and
context differ, provider admission included in node spans; no speedup promise.
RunIDs4538ffb635b1473ebbff231f692531cd/833c1840c7c247fb8f4555b9adf81819.

Actual pinned native Hermes JSON selected literal cg/synthesis, completed its
final token assertion and two original native guarded read_file executions,
blockedcalls0/guardcalls2. Original ContextCompressor executed once with real
external same-model summary:28messages→6; latest opaque tool ID
cg_e2aa5e3b6a8844fd9679801cbe360b8a and rawresult remained identical.
However APIcallsobserved0/runIDs[] caused the required diagnostic assertionFAIL.
Waiting restartnull, replay and SSE case UNEXECUTED, not passed. Exact native
failure metadata retained in
.venv/hermes-production-ca3fa572cdb6/json/failure.json (dedicated home/fixtures
retained); no installed home/config was accessed. Own scoped teardown0 left
no containers/network, fifth volume417276aa_cg_data retained. No native old
run/tool effects were resumed/repeated to force a pass.

Pin-verified source explains observer inadequacy: run_agent.py
_create_openai_client→agent/agent_runtime_helpers.py create_openai_client;
agent/chat_completion_helpers.py dispatch makes an original SDK client per
request and original callers finally close it. Hooks on only agent.client
therefore observed the unused shared object. Corrected solely the helper with
an instance-local factory delegate returning the identical original SDK object
with unchanged kwargs/reason/shared, adding only public HTTPX request/response
hooks. Original transport/auth/native closure are preserved; delegate restored
in finally. Failed cases now also retain source/client-lifecycle metadata.
Configured Ruff check/format-check0. Root holds subsequent full builds/startup
until the separate G3 malformed-upstream Unicode correction is terminal; the
above evidence identifies prior provider6dd84a.../sse073da... sources and cannot
be inherited as blanket proof for corrected images. G2F5 remains BLOCKED3/3.

Exact offline native-factory identity/args/closure/no-duplicate-hooks/restore
fixture, passed as a literal `-c` argument to the existing pinned
`.venv/hermes-research/Scripts/python.exe` (exit0):

```python
import copy,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from experiments.hermes_bridge import load_hermes,source_evidence
from scripts.smoke_hermes import observe_original_clients
hermes=Path("C:/Users/pkupr/AppData/Local/hermes/hermes-agent")
pin=source_evidence(hermes)
with tempfile.TemporaryDirectory(prefix="cg-native-client-") as temp:
    cls=load_hermes(hermes,Path(temp))
    import httpx
    from openai import OpenAI
    with patch.object(httpx.Client,"send",side_effect=AssertionError("offline factory guard forbids network")):
        agent=cls.__new__(cls)
        agent.provider="custom";agent.base_url="http://127.0.0.1:8080/v1";agent.model="cg/factory-fixture"
        kwargs={"api_key":"isolated-fixture-key","base_url":agent.base_url}
        before=copy.deepcopy(kwargs)
        agent.client=agent._create_openai_client(kwargs,reason="offline_initial_fixture",shared=True)
        request_hook=lambda request: None
        response_hook=lambda response: None
        agent.client._client.event_hooks["request"].append(request_hook)
        agent.client._client.event_hooks["response"].append(response_hook)
        restore,lifecycle=observe_original_clients(agent,request_hook,response_hook)
        created=agent._create_openai_client(kwargs,reason="chat_completion_request",shared=False)
        assert isinstance(created,OpenAI) and kwargs==before and created is not agent.client
        assert created._client.event_hooks["request"]==[request_hook]
        assert created._client.event_hooks["response"]==[response_hook]
        assert lifecycle==[{"reason":"chat_completion_request","shared":False}]
        assert agent.client._client.event_hooks["request"]==[request_hook]
        restore()
        assert agent._create_openai_client.__func__ is cls._create_openai_client
        agent._close_openai_client(created,reason="offline_fixture_close",shared=False)
        assert created.is_closed() and not agent.client.is_closed()
        restored_client=agent._create_openai_client(kwargs,reason="offline_restored_fixture",shared=False)
        assert request_hook not in restored_client._client.event_hooks["request"]
        assert response_hook not in restored_client._client.event_hooks["response"]
        agent._close_openai_client(restored_client,reason="offline_restored_close",shared=False)
        agent._close_openai_client(agent.client,reason="offline_primary_close",shared=True)
        assert restored_client.is_closed() and agent.client.is_closed() and kwargs==before
print(json.dumps({"result":"actual pinned native factory observer guard passed","hermes_sha":pin["git_sha"],"pin_verified_sources":len(pin["sources"]),"scope":"original native factory/SDK/transport objects, no send/server/Compose/inference/tool execution"}))
```

It exercised actual original native factory/SDK/HTTPX objects after18source pin
verification, with an explicit send guard; no HTTP request/server/Compose/model
or tool executed. The helper's live path retains authentic native dispatch;
this offline fixture is not advertised as the missing live gate.

## Corrected-provider Windows phase failure and fixture correction

The fresh actual Windows command below exited1, with both services healthy:

```powershell
python scripts/smoke_compose.py --context desktop-linux --project cg-smoke-win-current-20261004-ae71fc99 --model gemma4:12b --reasoning-effort none --hermes-python D:/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent
```

Before inference, the actual application-container probe verified unchanged
`http://host.docker.internal:11434/v1`, Ollama0.33.3, Gemma4:12b digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`,
UID10001, fsync, SQLite3.40.1 WAL/quick_check and host/image source equality,
including corrected provider
`660797ab43282dba990d8ef69e8214009606d87d0d9861c28997a07182152dff` and SSE
`99b8128918baca052f969f897e9049ced87128766cc66a3afd5ec7a8c69ece75`.
Backend platform manifest272bad9d9a4b2b3d022ea3858cac4a2d88cdb9dfd44efe3d7dd70a0308f8fed5,
image config80a0c41a3034d14d89e3e56935e13a2eea8202458a1087494ff6e69e74c38620,
index696a427e89476560c9a98fe9bf4e87114bf0df0bef8c884e5c3e01ca9231aadf;
frontend platform94926f1ba0b97eb220da3e3a2b06b9a3f72cdd3816f34fb5ef569c9c0710e0d4,
config047f49495adfa5d0b693b4b9446dabdefddbf7fcfc5528f50787e48663e1c4ea,
index311a1f71b44051321a2f3e4c469cb86a056286d3538e056ccc6a79939cd14df7.

Safe direct metadata identified the failure: ordinary JSON `stop`,6visible
characters/32.141s; multiturn JSON `stop`,8/.828s; native JSON `tool_calls`,
one call/2.079s; **native-result JSON `tool_calls`,one call,zero visible
characters/.609s**. The unchanged fixture still instructed the model to call
smoke_probe, so another native call is a valid model response. The helper
correctly failed its strict final-completion assertion. No tool executor ran;
later Nginx configuration/history/target/Hermes phases were unexecuted in this
run. This captured failure does not retroactively diagnose earlier uncaptured
completion failures.

Only the explicit fixture instruction was corrected: call smoke_probe exactly
once, then use its role-tool result for a brief final answer without further
calls. Initial forced function, subsequent auto choice, raw native IDs/results,
public profile and strict `stop`/nonempty-content assertions remain unchanged.
Configured locked Ruff check0; format-check initially1 for edited CRLF lines,
format0 then check/format-check0; intercepted seven-exchange fixture0 (no network
or executor). A fresh full validation uses a new project/fixture, never replays
old effects. Failure evidence remains
`.venv/compose-failure-cg-smoke-win-current-20261004-ae71fc99.json`; scoped
down(no-v)0 removed its containers/network and retained
`cg-smoke-win-current-20261004-ae71fc99_cg_data`. No existing data was removed.


## Final executed Windows and WSL2 production evidence — 2026-10-04

Both commands below completed with inspected terminal exit0. The Windows
command is the DevOps owner's returned positive result plus the report read
from its retained, read-only test volume; the WSL command was executed by the
coordinator after the owner terminated on the account limit. These are live
execution results, not independent review verdicts. Use fresh project names
when reproducing; both original named volumes are deliberately retained.

```powershell
python scripts/smoke_compose.py --context desktop-linux --project cg-smoke-win-final-20261004-5f34c9e2 --model gemma4:12b --reasoning-effort none --hermes-python D:/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root C:/Users/pkupr/AppData/Local/hermes/hermes-agent
python scripts/dev.py smoke-compose --project cg-smoke-wsl-final-20261004-369c51ea --model gemma4:12b --reasoning-effort none --hermes-python /mnt/d/Sources/creep/.venv/hermes-research/Scripts/python.exe --hermes-root /mnt/c/Users/pkupr/AppData/Local/hermes/hermes-agent --hermes-docker-context desktop-linux
```

| Caller | Actual project | Exit | Diamond / sequential wall seconds |
| --- | --- | ---: | --- |
| Windows | cg-smoke-win-final-20261004-5f34c9e2 | 0 | 1.563 / 1.719 |
| WSL2 | cg-smoke-wsl-final-20261004-369c51ea | 0 | 1.534 / 1.51 |

Each target shape made3 node executions/3 upstream calls; one measured sample
per shape is recorded. Both demonstrate overlapping diamond branches and
final fan-in; they do not promise a speedup. The WSL stack's native client
platform is Windows, explicitly invoked through WSL interoperability. Its
existing Python3.11.15/Hermes0.18.2/OpenAI2.24/httpx0.28.1 versions and equality
of Linux/Windows Docker daemon IDs were asserted before native execution.
No Linux Hermes installation or Windows-wheel import into Linux occurred.

Both actual production images passed source equality before inference, including
provider660797ab43282dba990d8ef69e8214009606d87d0d9861c28997a07182152dff and
SSE99b8128918baca052f969f897e9049ced87128766cc66a3afd5ec7a8c69ece75.
Actual external Ollama0.33.3 and the unchanged host.docker.internal route used
Gemma4:12b digest4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c.
Runtimeengineb8ff723d... remains unchanged, including the known G2 blocker.

Executed assertions include healthy API/static UI, non-root/read-only/capdrop
containers, SQLite3.40.1 WAL/fsync/quick_check, seven ordinary/multiturn/native-
tool-request/manual-result JSON/SSE exchanges, unknown physical-model404,
unbuffered Nginx SSE/DONE and1860second proxy timeouts above1800second budgets,
completed-history backend restart, new containers retaining graph publications
and immutable run snapshots on the same volume, and actual hardware timing.

Original pinned Hermes JSON selects literal cg/synthesis; JSON and SSE each
use3 original per-request SDK clients, execute2 guarded native read_file calls,
and verify2 exact continuation replays without increased durable counters or
repeated effects. Each case ends with3 node executions/5 upstream attempts/
2 tool rounds. JSON performs an actual waiting-tools backend restart after
fully reading the original response and before the first fixture effect.
Run/pending opaque IDs/owners/checkpoints/counters remain identical across
changed process PID/starttime. Real native ContextCompressor28→6 preserves
pending IDs and raw results. All19 exercised source/guard files match the
pinned Hermes revision after prescribed normalization; the dirty installed
checkout remains untouched. Original transport, executor and native closure
are preserved; only isolated observer/guard callbacks are registered.

Versioned proof: [Windows Compose](../.codex/specs/cognitive-graph-mvp/live-windows-compose.json),
[Windows Hermes](../.codex/specs/cognitive-graph-mvp/live-windows-hermes.json),
[WSL Compose](../.codex/specs/cognitive-graph-mvp/live-wsl-compose.json),
[WSL Hermes](../.codex/specs/cognitive-graph-mvp/live-wsl-hermes.json), and
[actual WSL native guard](../.codex/specs/cognitive-graph-mvp/wsl-client-guard.json).
These contain exact source/image/run IDs, pins, counts and target spans, with
fixture metadata only. No token or hidden reasoning is recorded.

The initial root WSL attempt81cd29e6 exited1 at metadata lookup before any
Hermes execution, after stack/public/history/target subsets passed. Read-only
native diagnosis proved the version guard omitted the existing native Hermes
venv package path that load_hermes already uses. The coordinator changed only
that guard in smoke_compose.py after confirmed owner termination. No package
was installed. Actual extracted-helper WSL guard0 asserted the original pinned
versions and equal daemon IDs. Configured Ruff check0; initial format-check1
identified mixed newline edits, exact-file format0/check0. The subsequent
fresh full WSL attempt above passed0. Old failed evidence/volume remain intact.

Both successful helpers completed scoped down(no-v)0; container/network residue
arrays are empty and both owned volumes are retained. Independent final queries
confirm no owned smoke listeners/processes. Existing unrelated containers,
Ollama/model/configuration, secrets and user data were not changed.

### Historical remaining gates and review state (2026-10-04)

- G2-runtime is BLOCKED3/3 on valid Draft3 schema-valued extends/type local-ref
  preservation, authoritative terminal FAIL. No automatic fix/fourth/reset or
  accepted-profile narrowing.
- G1's cycle3 account-limit termination remains historical no-verdict evidence;
  the user explicitly authorized one additional attempt, now independently PASS
  at its cap4/4. No other group budget was reset. G3 cycle2 FAIL found required
  inventory-Unicode F3; its scoped fix is running2/3. G5/G6 independent reviews
  remain OPEN0/3. Model assignments are unchanged.
- The isolated operator backup/restore drill and corrective logical-state audit
  below executed; arbitrary user-data recovery/cutover was not exercised.
  Remote GitHub CI execution remains unexecuted; no push was authorized.
- The earlier unreproduced Windows native test exception remains unassigned.
  Later587-backend and current lint greens do not diagnose it.

Whole-product acceptance remains blocked. Current local checks are587 backend,
21 frontend,98 graph and six real-backend browser scenarios with all reported
commands exiting0; fresh current configured lint/drift/TypeScript also0.

## Quota recovery — isolated backup/restore execution

This is delivery-owner evidence, not an independent G5/G6 verdict. Only the
four owned documentation files and new ignored recovery fixture directories
were written. Both production smoke helpers remained byte-identical:
smoke_compose.py `3bf4204d8d0626c524cdc807703f83db07d96bba4e383829a6ff54f2e7feeedb`;
smoke_hermes.py `8696fc2e6013c25f29a8ea8548cfacf5960eeee3399b5c1e5193e1331c8b3393`.
Existing corrected Windows/WSL JSON evidence was harvested with fresh host
source comparisons, four native-case counter/ID assertions and no repeated
inference or tool effects. WSL was the Linux Compose caller with the original
Windows-native client, never a claim of installed Linux Hermes.

The drill used only new owned fixtures and the already cached current Windows
backend image `sha256:ffc2378180c71cbd5c9b16b4d438d415a5e0feff5f35f9e33059fcb04cd5a469`.
Every fixture container used pull-never, networknone, UID10001:10001,
read-only root, cap-dropALL and no-new-privileges; server fixtures also used
init/tmpfs/one worker and no published host ports. The fixture-only upstream
was127.0.0.1:9/v1, explicitly unavailable; storage readiness remained200 while
Ollama availability was false. External Ollama/models/Hermes/user volumes,
secrets, global configuration and production sources were untouched.

Historical executable verifier failures are retained without changing exits:

| Exact command from repository root | Exit | Meaning and retained project |
| --- | ---: | --- |
| `python .venv/delivery-recovery-20261004-9f721c6a/drill.py` | 1 | Wrapped graph-create fixture received400; no graph/run created; source volume retained |
| `python .venv/delivery-recovery-20261004-b71e2f90/drill.py` | 1 | Real zero-inference run completed; verifier incorrectly required contained process exit0 after Compose stop0, observed SIGTERM143 |
| `python .venv/delivery-recovery-20261004-c24d870f/drill.py` | 1 | Actual shutdown-complete logs confirmed graceful143; synthetic pending graph omitted required generation field and was rejected before insertion |
| `python .venv/delivery-recovery-20261004-df35a918/drill.py` | 1 | Source completed/pending state and stopped-container whole docker cp executed; read-only SQLite verifier created an empty WAL/SHM pair after taking its file list, making its copy comparison incomplete |
| `python .venv/delivery-recovery-20261004-e4f18bc2/drill.py` | 1 | Backup/copy/restore/production readiness/restart and semantic checks passed; last verifier incorrectly required unchanged SQLite physical bytes after startup |
| `python .venv/delivery-recovery-20261004-e4f18bc2/audit.py` | 0 | Fresh read-only original/restored-volume logical audit proves all SQL rows/checkpoints identical, integrity/FK, file/owner/mode equality and prior executed API/readiness/restart assertions |

Each project is `cg-backup-recovery-20261004-<same suffix>`. Every command above
has complete argv/exit/stdout/stderr in its retained `commands.jsonl` and
`evidence.json`; audit.py records its actual container argv/output in
`logical-audit-command.json` and consolidated successful assertions in
`audit.json`. No failed command is relabeled as0 or discarded. A first static
graph-preflight command also exited1 because its inline runner omitted the
backend import path; the corrected locked runner inserted backend and both
fixture DTO/topology validations passed0 before the final drill. All guards
remain assertions; no acceptance or production policy was relaxed.

Pinned Uvicorn0.54.0 server.py capture_signals re-raises captured SIGTERM after
graceful `_serve` termination. Actual stop commands exited0, contained process
statuses were143, and logs included `Application shutdown complete.` and
`Finished server process`; no OOM/error/SIGKILL. Merely observing143 would not
prove graceful shutdown. The drill required those logs before copying.

The e4f18bc2 execution demonstrated:

- Real composed production API creates/publishes a zero-LLM graph and completes
  run `525fead048754934a89e46e34c40b892`, snapshot hash
  `b211250447658a3c117abcaeab02dc464a3c877961d1861cf3d7663fa1905b01`.
- Production FileGraphRepository/SQLiteRunRepository creates a separately
  **synthetic** waiting checkpoint `backup_pending_e4f18bc2`, pending ID
  `cg_backup_pending_e4f18bc2`, owner `owner`, state_version2, hash
  `00a3c022b2a592de8517c7db60e21b77d6177d368eaeee228d8e13412c0dc6af`,
  original deadline `2026-10-04T16:53:02.620251+00:00`. No model call or tool
  effect was needed; this is checkpoint recovery proof, not another native
  Hermes integration experiment. Waiting TTL is not extended by restore.
- Graceful source stop, real stopped-container `docker cp /data/.` to a new
  Windows host directory, then whole-source-volume numeric-owner tar creation
  through the immutable image; archive fsync and host-copy SHA equality.
- Separate new restored volume, emptiness checked immediately inside the same
  restore command before extraction; archive paths allow only relative regular
  files/directories without traversal, UID/GID10001. Restore ran as10001,
  preserving modes without chowning original/existing volumes.
- Before restored startup, **every file byte/hash/mode/owner matched** the
  original. The102400-byte archive SHA is
  `0159dade3d2aaef6002fe9323697e52de6959cc05c2aaa332d49a7dc4259e460`.
- Restored production service became healthy; API200/storage_ready/unchanged
  completed output and pending ID/owner/deadline/state/counters passed, then
  actual Compose restart and the same assertions passed again. Inference/tool
  counters remain zero. Restored graceful stop/log proof also passed.
- Fresh actual Linux/SQLite3.40.1 two-volume read-only audit after shutdown
  compared all rows in activations3/batches1/events7/pending_tools1/
  response_cache0/responses2/runs2. They are identical; integrity_check=ok and
  foreign_key_check empty. Logical-state SHA
  `2d061efec73fa022dffd47b4e598f60cd178631de2fb50125dd725ea45f5b322`.
  All graph/publication/metadata files/modes/UIDs are unchanged. SQLite physical
  bytes changed after startup but logical rows did not; the initial full-file
  post-startup assertion was an inappropriate verifier assumption.
- Actual audit image sources main dae170..., repository c5254..., engine
  b8ff723..., provider660797ab..., SSE99b812..., bridgec21d821... match fresh
  host SHA256 values. No runtime/schema defect was fixed or concealed.

The successful audit closes the independent new-fixture backup/restore live
behavior gap, subject to forthcoming G5 independent review. Whole-product
acceptance remains blocked by G2F5; G6 is not completed. The updated runbook
describes the tested tar/copy procedure and the distinction between Windows
host-copy metadata and Linux numeric owners. A generic operator port cutover,
arbitrary user backup, new storage schema migration and remote GitHub CI were
not executed and are not represented as passed.

All five own Compose teardowns exited0 without -v. No exact-label container or
network residue remains. Retained volumes: source for9f721c6a, b71e2f90,
c24d870f, df35a918, plus source/backup/restored for e4f18bc2. Original data,
host copies/archive/evidence and all seven volumes remain; no user-resource
cleanup occurred. New fixtures intentionally retain their data and evidence.

At this delivery handoff, the subsequent G3 inventory-only correction is being
implemented in the separately owned provider/API tests. Earlier full Windows/
WSL/native and backup proofs retain provider660797ab... and SSE99b812... image
attribution. They are not automatically a new-image proof. The coordinator
will reconcile the isolated source delta and request fresh inventory/health/
model-namespace Windows/WSL validation after that owner is terminal; inference
and native tool effects need not be repeated to test inventory-only changes.

Delivery documentation audit0 verified strict UTF8/whitespace,27 existing local
links, two embedded Python snippets,20 PowerShell example syntax blocks, all
R01–R11/A01–A16/G0–G6 IDs and unchanged smoke helper hashes. Fresh exact-label
residue queries0 confirmed all five recovery projects have no containers or
networks and all seven own volumes remain. audit.py and docs_audit.py records
are retained with the fixture. Git diff --check0; no commits/push were made.
