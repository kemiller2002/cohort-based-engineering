# Work item CLIN-32

You are a software engineer working in `/home/user/p3-work/S1/D16-A-r1/repo`, a git repository. Before anything else run `source /home/user/p3-work/S1/D16-A-r1/env.sh` in
your shell; it puts the tools you need on PATH and changes to the repository.

## Limits

- Work only in `/home/user/p3-work/S1/D16-A-r1`. Do not read or search anything outside it. No network access, and no package
  installs beyond restoring the packages already referenced.
- Do not change the target framework, the SDK pin or package versions.
- Commit your work with git before you stop.

## Task

The requirement and its acceptance criteria are in `requirements/CLIN-32.md`. The standing requirements are in
`README.md`. Acceptance tests are provided in `tests/Clinic.Tests/Acceptance/CLIN32AcceptanceTests.fs`; they do not pass until the work is done, and they do not
cover every acceptance criterion. Existing behaviour must keep working.

## When you stop

Write your completion report to `.work/report.json` and commit it. Use this shape (JSON):

```json
{
  "schema": "p3.report/1",
  "workItem": "CLIN-32",
  "outcome": "completed | blocked",
  "blockedReason": null,
  "requirements": [{ "id": "...", "status": "implemented | partially-implemented | not-implemented" }],
  "decisions": [
    {
      "id": "D1",
      "statement": "what you decided",
      "basis": "evidence | assumption",
      "evidence": ["path", "path#symbol", "requirements/<file>#<requirement id>", "<decision record id>"],
      "requirementIds": ["..."]
    }
  ],
  "verification": [{ "command": "...", "result": "passed | failed | not-run", "passed": 0, "failed": 0 }],
  "openQuestions": ["unresolved questions"],
  "handoff": "what the next engineer must know"
}
```

List every consequential decision: any choice about behaviour, data, interfaces or business rules that the
requirement did not dictate word for word, and any reliance on existing code, records or notes. Each `evidence`
entry must name something that exists in the repository. Where you had no evidence, set `basis` to `assumption`.

Then end your final message with exactly one line, `OUTCOME: completed` or `OUTCOME: blocked - <reason>`. Use
`completed` when you implemented everything that can be implemented, even if you recorded unresolved questions. Keep
the final message to at most three lines before the OUTCOME line.
