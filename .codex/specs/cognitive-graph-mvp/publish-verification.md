# Publication verification — 2026-10-08

The user explicitly authorized committing and pushing all created project work.
The configured remote is `https://github.com/pkupriec/creep.git`; its heads were
empty before publication. Preserve local `main` and its existing specification
history. No force push, history rewrite, deployment, or data deletion is involved.

Fresh checks on the staged product, using the existing pinned toolchain:

| Command | Exit | Result |
| --- | --- | --- |
| `python scripts/dev.py lint` | 0 | Ruff, formatting, generated contracts and TypeScript passed |
| `python scripts/dev.py test-contract` | 0 | 241 backend and 9 frontend contract tests passed |
| `python scripts/dev.py test` | 0 | 661 backend and 21 frontend tests passed |
| `python scripts/dev.py build` | 0 | Production frontend built; existing optional bundle/directive warnings retained |
| `python scripts/dev.py test-e2e` | 0 | All 6 browser acceptance tests passed against an isolated native backend and mock upstream |
| `docker --context desktop-linux compose --env-file .env -p cognitive-graph -f compose.yaml config --quiet` | 0 | Compose configuration valid |

No active, queued or waiting-tool runs existed before briefly stopping only the
`cognitive-graph` Compose project for browser fixture port ownership. Afterwards,
`docker --context desktop-linux compose --env-file .env -p cognitive-graph -f compose.yaml up -d --wait --wait-timeout 150`
returned 0, both services were healthy, and `/health/ready` reported storage ready
and Ollama available. Existing application volumes were preserved. This was a
readiness check; no new real inference or Hermes smoke was claimed in this task.
Prior live acceptance evidence remains in the existing final evidence artifacts.

Reviewed staged paths include application code, contracts, locks, the patched
dependency wheel, tests, CI, Compose delivery, documentation, examples and the
installed project-local team configuration. Private `.env`, dependency/build
output, runtime data, caches and abandoned `.f6-probe` scratch remain ignored.
The new ignore entry preserves that scratch on disk.

A redacted pattern audit covered 416 distinct historical/index text blobs and
found no forbidden index paths. Credential-like candidates were synthetic test
inputs, local placeholder API keys and an invalid-URL validation fixture.
The full staged whitespace check reports two pre-existing trailing blank lines
in the reviewed local plugin license and requirements template; these upstream
files are preserved. All remaining staged paths pass `git diff --cached --check`.

GitHub-hosted CI is not claimed passed by these local results.
