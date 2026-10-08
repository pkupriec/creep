# Tasks: <slug>

Tasks are organized into parallel waves. Tasks in one wave may run at the same time only when their file scopes do not overlap.

## Wave 1: <description>

Spec ref: `spec.md#<section>` - <what this implements>.

- [ ] [coding] <verb> <what> | `<file paths>` | <acceptance criteria>. Run: `<command>`
- [ ] [devops] <verb> <what> | `<file paths>` | <acceptance criteria>. Run: `<command>`
- [ ] [sa] <verb> <what> | `<file paths>` | <acceptance criteria>. Run: `<command>` or `[skip-verify]`

## Completion Notes

Use `> Done. <summary>` under completed items. Use `[!]` and a blocker note for blocked work.

## Stable Review Groups

| Group ID | Acceptance scope | Shared-file owner | Reviews consumed (0..3) | Next cycle | Verdict / open gates |
| --- | --- | --- | --- | --- | --- |

Record consumption before every synthesizer spawn. Retries, replacements and resumed sessions consume the same counter. Cycle 3 non-PASS is terminal.
