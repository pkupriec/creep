# Cognitive Graph MVP — requirements

Authority: Cognitive_Graph_MVP_Codex_Team.md v1.1, 2026-10-03.
Sections below are preserved verbatim. No research gate is closed by extraction.

## 2. Approved User Requirements

| ID | Requirement |
| --- | --- |
| R01 | Hermes compatibility; proxy between the client and Ollama |
| R02 | Published graphs appear as virtual models; direct Ollama mode |
| R03 | Nodes can use the environment and tools available to an ordinary model in Hermes |
| R04 | A node waits for all inputs; the objective is synthesis, rather than competition between nodes |
| R05 | A loop terminates according to a condition |
| R06 | An explicit output node supplies the client response; intermediate results appear in the UI |
| R07 | Create, select, and edit graphs; store graphs as files; retain run history |
| R08 | Simple left-to-right visual editor: multiple inputs, many-to-many connections, cycles, node prompts; select an existing editor through short R&D |
| R09 | Test execution, statuses, node results, cancellation, graph import/export |
| R10 | Windows + WSL2, Docker Compose, external Ollama, Python/FastAPI + React |
| R11 | The specification must be executable by Codex using the selected team |

Streaming and full chat history were included in the proposal accepted by the user. Support `stream=true/false`, receive the history supplied by Hermes, and account for client-side compression. Multiple named inputs are configured in the UI; a standard Hermes request maps to the `chat` input. A separate visual layer for a sequence of graphs is not required in the MVP. One graph defines the pipeline, while internal interfaces leave room for future graph composition.

