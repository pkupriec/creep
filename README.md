# Cognitive Graph

A local graph proxy between Hermes Agent and external Ollama. FastAPI coordinates
all-input synthesis and explicit seeded feedback loops; Hermes owns tool execution.
React Flow provides graph editing, publication, test runs and durable history.

The editor, durable runtime, proxy and Compose delivery are implemented.
G0–G6 independently PASSed; G2 attempt6 closes F1–F6, retaining all prior
attempts including the quota-terminated attempt5. The exact local
`referencing==0.37.0+cg.1` corrects Draft3 object-valued `extends` crawling
without changing engine source or the accepted schema profile. Current tests
cover661 backend cases,259 runtime/storage cases and28 F6 regressions.
All mandatory R01–R11/A01–A16 gates are closed. G5 PASS2/3 and G6 PASS1/3;
the UI's “Active duration” label currently includes tool waits (optional Low).
The [compact status ledger](.codex/specs/cognitive-graph-mvp/current-state.md)
is the current coordination authority; full review history remains preserved.

Current production images passed complete Windows and WSL2 smoke tests with
external Ollama and original pinned Hermes JSON/SSE, guarded fixture reads,
waiting-tool backend restart, original IDs, exact replay and real compression.
The WSL stack used the existing Windows-native Hermes client through explicit
interoperability. All application files and the corrected dependency matched
the tested containers. Test containers/networks were removed and
volumes retained.
See [verification](docs/verification.md) and the
[completion report](.codex/specs/cognitive-graph-mvp/completion.md) for exact
proof, review budgets and residual limitations.

Prerequisites: Docker Desktop with WSL2 integration (observed Docker28.3.2,
Compose2.38.2-desktop.1), an external Ollama server and an already installed
text/function-tool capable model. Native development pins Python3.11.15,
uv0.11.28, Node24.14.0 and npm11.9.0; all dependency locks are repository-local.
No model, inference server, GPU service, tool executor or cloud resource is
installed by Compose.

From PowerShell in the repository root:

```powershell
$env:NODE_OPTIONS = '--use-system-ca'
python scripts/dev.py setup
python scripts/dev.py lint
python scripts/dev.py test-contract
python scripts/dev.py test
python scripts/dev.py build
python scripts/dev.py test-e2e
```

Native launch uses two terminals. Select an external upstream reachable from
the native backend and a local data directory:

```powershell
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:CG_DATA_DIR = Join-Path $PWD '.local-data'
python scripts/dev.py backend
# Second terminal:
python scripts/dev.py frontend
```

Container launch (Windows/WSL smoke and independent delivery review passed):

```powershell
docker context show
docker compose -p cognitive-graph -f compose.yaml config --quiet
docker compose -p cognitive-graph -f compose.yaml up --build -d --wait
curl.exe --fail http://127.0.0.1:8080/health/ready
```

Open `http://127.0.0.1:8080`; API is also on `127.0.0.1:8000`. Choose an installed
physical model, create/import a graph, validate and publish it. Hermes uses
base URL `http://127.0.0.1:8080/v1` and `cg/<graph_id>`; direct requests use
`ollama/<installed_model_name>`. Optional `CG_API_TOKEN` protects both API
surfaces; supply it through the process environment and UI memory, never a URL
or graph file.

[Runbook](docs/runbook.md) covers Windows/WSL paths, upstream routing, exact
smoke commands, backups, retention, restart and volume-preserving teardown.
[API contracts](docs/api.md), [Hermes profile](docs/hermes-compatibility.md),
[dependency pins](docs/dependencies.md) and the
[authoritative specification](.codex/specs/cognitive-graph-mvp/spec.md) describe
the boundaries. Ordinary `docker compose down` retains history;
`docker compose down -v` **deletes data** and is not part of verification.
