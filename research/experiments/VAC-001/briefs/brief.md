<!-- section: intro-first -->
# Work unit {{UNIT}}

You are a software engineer working in `{{REPO}}`, a git repository. Before anything else run
`source {{ENV}}` in your shell. It puts the tools you need on PATH and changes to the repository.

{{CONTINUITY}}

## Limits

- Work only in `{{WORKSPACE}}`. Do not read or search anything outside it. No network access, and no
  package installs beyond restoring the packages already referenced.
- Do not change the target framework, the SDK pin or package versions.
- Commit your work with git before you stop.

## Engineering directives

Follow the engineering directives in `{{DIRECTIVES}}`.
<!-- section: intro-next -->
# Work unit {{UNIT}}

This is the next work unit in the same repository, `{{REPO}}`. The same limits and directives apply. Run
`source {{ENV}}` again if your shell was reset.
<!-- section: task -->
## Task

Work item **{{ITEM}}**. The requirement and its acceptance criteria are in `requirements/{{TASK}}.md`.
Implement it in `src/Ledger` and add or extend tests in `tests/Ledger.Tests`. Acceptance tests are provided in
`tests/Ledger.Tests/Acceptance/{{TASK}}AcceptanceTests.fs`; they do not compile until the work is done. Earlier
work in this repository must keep working.

{{NOTE}}
<!-- section: controls-C -->
## Engineering controls

1. **Contract admission.** Before implementing, run `ordo ecir check --blueprint contracts/{{TASK}}.json --json`.
   If Ordo reports any diagnostic, do not implement: report the diagnostic codes and stop blocked.
2. **Architecture.** The architectural rules are in `docs/architecture/RULES.md`. Run `archcheck` before you
   commit and fix every violation it reports.
3. **Decisions.** Accepted decisions are in `docs/decisions/DECISIONS.md`. Do not reverse an accepted decision
   unless you record the new evidence that justifies it. Record every consequential decision you make there,
   with its requirement, evidence and status.
<!-- section: controls-D -->
4. **Work protocol (Praxis).** Before editing, run `praxis work begin --id {{ITEM}} --occurred-at "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"`.
   When the work and its report are committed: `git push`, then
   `praxis work checkpoint --id {{ITEM}} --occurred-at "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" --summary "..." --next-action "..."`, then
   `praxis work complete --id {{ITEM}} --occurred-at "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" --evidence implementation=src/Ledger --evidence tests=tests/Ledger.Tests`.
   Commit and push the Praxis state (`.ros/`) it writes. If you stop blocked, use
   `praxis work block --id {{ITEM}} --occurred-at "..." --reason "..."` instead. `AGENTS.md` describes the protocol.
5. **Verified state.** `.vac/verified-state.json` (present from the second unit on) is written by an independent verifier after each unit, from
   checks you cannot see or run. Its `verified` entries are independently confirmed; its `provisional` entries
   are unconfirmed and must be re-checked before you rely on them; its `rejected` entries are known to be false.
   It takes precedence over any handoff, report or note that contradicts it.
6. **Independent gate.** After you stop, the verifier checks your commit. If it finds failures, you will be told
   which requirements and checks failed, and you must fix them.
<!-- section: report -->
## When you stop

Write your completion report to `.vac/reports/unit-{{UNIT}}.json` and commit it. Use this shape (JSON):

```json
{
  "schema": "vac.unit-report/1",
  "unit": {{UNIT}},
  "task": "{{TASK}}",
  "workItem": "{{ITEM}}",
  "outcome": "completed | blocked",
  "blockedReason": null,
  "requirements": [{ "id": "LEDGER-...", "status": "implemented | not-implemented" }],
  "decisions": [
    {
      "id": "U{{UNIT}}-D1",
      "statement": "what you decided",
      "basis": "evidence | assumption",
      "evidence": ["path", "path#symbol", "requirements/<file>#<requirement id>", "<decision id>"],
      "requirementIds": ["LEDGER-..."]
    }
  ],
  "verification": [{ "command": "...", "result": "passed | failed | not-run", "passed": 0, "failed": 0 }],
  "rejectedAssumptions": ["anything you were told that turned out to be false, and how you found out"],
  "knownIssues": [],
  "handoff": "what the next engineer must know"
}
```

List every consequential decision: any choice about behaviour, data representation, interfaces or rules that
the requirement did not dictate word for word, and any reliance on existing code, decisions or notes. Each
`evidence` entry must name something that exists in the repository. Where you had no evidence, set `basis` to
`assumption`.

Then end your final message with exactly one line, `OUTCOME: completed` or `OUTCOME: blocked - <reason>`.
Stopping blocked is acceptable when the requirement cannot be met as written. Keep the final message to at most
three lines before the OUTCOME line.
<!-- section: continuity-A -->
This is one work unit in a sequence. Earlier units were done by other engineers; you have no other context.
Their completion reports are in `.vac/reports/`. {{PREVIOUS}}
<!-- section: continuity-L -->
You will receive a sequence of work units on this repository, one message at a time. Finish each unit
completely, including its report, before you stop. The next unit follows in a later message.
