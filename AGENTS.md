# Codex Defaults

## Authorization And Approval

- For requests to answer, explain, review, diagnose, or plan, inspect the
  relevant materials and report the result. Do not implement changes unless the
  request asks for them.
- For requests to change, build, fix, migrate, or configure, make the requested
  in-scope local edits and run relevant non-destructive validation without
  asking again for each file.
- Safe local reads, edits, tests, builds, linting, formatting, and read-only
  inspection are authorized when they are necessary to complete an approved
  task.
- Require confirmation for external writes, destructive or difficult-to-reverse
  actions, purchases, deployment or live-resource mutation, secret access,
  production-data access, and material scope expansion. Explain the concrete
  impact before requesting approval.
- User approval applies to the described scope, not to adjacent cleanup or an
  inferred broader redesign. Surface newly discovered expansion separately.

## Working Method

- Read repository guidance and existing patterns before editing. Keep changes
  scoped and preserve user or peer work; never revert unrelated changes.
- Re-read a target immediately before changing it when work has been
  interrupted or another actor may have edited nearby files.
- Run commands non-interactively and without pagers. Provide input through
  arguments, environment variables, or files; do not depend on an editor,
  confirmation prompt, stdin, or an attached TTY.
- Use project-local dependency isolation and the repository's existing package
  manager, wrappers, lock files, and toolchain pins. Do not install project
  dependencies globally or introduce a second package manager casually.
- Parallelize independent reads. Parallelize writes only when file ownership is
  disjoint and the user requested delegation or team-style work.
- Use applicable skills for specialized workflows. Use bounded concurrency and caching only when approved requirements and data sensitivity justify them.
- Keep comments and abstractions proportional to the code. Avoid unrelated
  refactors, broad formatting churn, generated metadata changes, or speculative
  features.

## Source Of Truth

- Current files and diffs are authoritative for implementation state.
- Durable artifacts under `.codex/specs/<slug>/` are authoritative for agreed
  requirements, task ownership, decisions, blockers, review history, and open
  gates.
- Fresh command output is authoritative for verification claims. Check exit
  codes and parsed summaries rather than inferring success from quiet output.
- Returned agent results and messages are evidence, but stale summaries,
  delayed messages, or silence do not override current disk state.
- When sources disagree, re-read the relevant file, artifact, and verification
  output before acting. Record the discrepancy instead of choosing the most
  convenient account.

## Team Activation And Ownership

- The main thread is the lead unless the user explicitly requests
  `fullstack-agent` or a generated Spawn Plan. Do not activate a team workflow
  merely because multiple files are present.
- When team work is requested, use the `codex-agent-team` skills as the source
  of procedure. Keep artifacts under `.codex/specs/<slug>/`.
- The lead owns research, requirements, design decisions, task waves,
  delegation, consolidation, blockers, and final communication. Role agents
  own their delegated implementation or review scope.
- Delegate file-disjoint scopes. No two concurrent writers may own the same
  file. Serialize overlap or identify one merge owner before work begins.
- Every handoff must name the role and unique instance, spec/task reference,
  exact files, no-edit boundary, acceptance criteria, interface contract,
  verification command or evidence, expected output, peer-concurrency warning,
  and whether the lead must wait for all requested agents before consolidation.
- Use `sa-agent` for local architecture, persistence, network exposure, external Ollama and delivery design.

## Liveness, Recovery, And Closure

- Silence is not failure. A quiet agent may be running a long build, test,
  plan, or review. Inspect durable artifacts and agent state, and wait for a
  returned result before deciding that work is lost.
- Require positive evidence before recovery or reassignment: an explicit
  terminal failure, confirmed termination, unusable/corrupt output, or durable
  evidence that the assigned acceptance criteria cannot complete.
- Do not duplicate an in-flight scope, take over broad implementation in the
  lead thread, or cross a destructive/billable gate because an agent is quiet.
  Steer the agent when possible; otherwise respawn only the unfinished,
  file-disjoint scope.
- Wait for all requested agents before consolidating a wave. If a requested
  result is unavailable, record the missing evidence and resulting assurance
  gap rather than fabricating a summary.
- Harvest each completed result, preserve its evidence, and close every agent
  that is no longer needed. Before final completion, perform an active-worker
  check and confirm that no required worker remains active.
- After an interruption or resume, inspect current artifacts and existing
  agent state before spawning replacements. Do not create duplicate workers
  from an old transcript or stale plan.

## Independent Review

- Keep review adversarial and independent. Implementation is not complete until
  the assigned review synthesizer reports PASS; self-review is not a verdict.
- Give every independently reviewable task group a durable group identifier in
  `tasks.md` and review handoffs. Limit each task group to three review cycles.
  A cycle is consumed when that group's synthesizer is spawned, including its
  initial review, targeted re-reviews, replacements, and interrupted retries.
- Each task-group counter is non-resetting across that group's implementation
  waves, fix waves, reviewers, review files, processes, and resumed sessions.
  Renaming or artificially splitting an exhausted group does not create a new
  budget. A genuinely distinct planned task group has its own counter.
- A FAIL in cycle 1 or 2 may create one scoped fix wave followed by the next
  review for that group. Cycle 3 is terminal for the affected task group: if it
  does not report PASS, stop that group's automatic fix/review loop, preserve
  its findings and verification evidence, and report the group blocked. Other
  independent groups may continue, but the objective cannot complete while a
  required group is blocked. Never spawn a fourth cycle for a group
  automatically.

## Verification

- Run the most relevant targeted tests plus repository checks that would block
  CI for changed files. Report exact commands, exit codes, and outcomes.
- Verify the verifier: confirm that each command actually exercises the claimed
  behavior, uses the repository's pinned tooling, and covers the acceptance
  criteria. A green but inadequate check is an open verification gap.
- Distinguish static validation from executable behavior. If a required check
  cannot run, state why, identify the unproven behavior, and leave the gate
  open.
- Static checks alone do not prove deploy scripts, CI/CD, shell tooling, or IaC
  runtime behavior. A required live-validation gate needs deploy/smoke/teardown
  or the closest safe executable equivalent.
- Completion reports must include changed files, delivered behavior, exact
  verification evidence, blockers, open live-validation gates, and residual
  risk.

## Local Stack And Safety
The application stack is Python/FastAPI + React, Docker Compose on Windows + WSL2, and external Ollama. Establish endpoint/runtime details from the forthcoming specification. No AWS plugins, MCP servers, infrastructure or cloud credentials belong in this setup. Preserve authentication/provider and security policy. Do not commit, push, deploy or delete data without scope authorization.


## Project Setup Contract

- Setup only until the user supplies the specification. Do not invent product requirements, implementation tasks, code or deployment files.
- Main thread coordinates. Roles: fullstack-agent (explicit lead/spawn plan), coding-agent, devops-agent, review-agent, sa-agent.
- Use installed codex-agent-team workflow skills. At most three spawned agents plus the coordinator, depth one. Role ceilings: coding 2, DevOps 1, review 3, architecture 1; the total limit always wins.
- Versioned state: .codex/specs/<feature-slug>/requirements.md, spec.md, design.md, tasks.md, decisions.md and review.md as needed. Templates are scaffolding, not approved requirements.
- Record stable task-group IDs and review counters before every synthesizer spawn. Each group has at most three non-resetting cycles across waves, replacements, interruptions and sessions. Only cycles 1 and 2 may lead to automatic fixes. Cycle 3 non-PASS is terminal: preserve evidence and report BLOCKED. Never create an automatic fourth cycle or reset by artificial renaming/splitting.
- One owner per shared file; reviewers are independent of implementers. Missing required acceptance or verification evidence means FAIL, even if no severe defect is proven. Optional warnings do not block PASS.
- No workflow hooks are necessary. Reviewed optional upstream logging hooks are omitted. Never bypass hook or project trust.
- Use actual client lifecycle capabilities. Verify terminal status if close is unavailable. Distinguish generic agents from discovered custom roles.

## Reviewed Baseline And Tool Policy

- Reviewed upstream baseline: `90b05ba04cbd49b0fb0e4f2ad7faecafad61ebb6`. Before using any newer revision, inspect its diff against this baseline, including instructions, agents, skills, hooks, rules, manifests and dependencies. Record the review and approval in setup evidence. Do not automatically update from upstream HEAD.
- Maintain the repository marketplace and project-local plugin source. Do not run the personal installer or change global configuration for this workflow.
- External MCP servers and Apps connectors are disabled for this workflow. Approval requests route to the user; do not select automatic approval review or bypass approval/trust controls. Session-level overrides may take precedence; report any mismatch rather than claiming project policy changed the current session.
- Any future external dependency must have an exact version or immutable revision and an explicit scope justification; never use `@latest` or unbounded version ranges. Disabled Playwright is pinned to the already cached `0.0.70` package, without installing or enabling it.
- Do not apply concurrent-cached-fetch defaults to LLM inference, tool execution, or state-changing requests. Do not automatically persist their responses or parallelize/retry their effects. Such behavior requires an explicit task contract and safe semantics. Preserve all explicit project concurrency limits; three-child team concurrency is not an inference/request concurrency setting.
- Review acceptance: PASS requires no Critical/Severe/High findings, all required acceptance criteria demonstrated, all required verification executed and passed, and requested review evidence collected. Otherwise FAIL. Missing evidence is an acceptance-gate failure, not a fabricated severity escalation. Optional Low/Medium/Warning/Suggestion findings may remain on PASS.
- One stable task group has at most three synthesizer spawns across waves, replacements, interruptions and sessions. No fourth cycle under this workflow. Exhausted groups require user disposition; renaming or artificial splitting never resets the budget.
