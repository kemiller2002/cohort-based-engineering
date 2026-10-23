# Work item CLIN-52

You are a software engineer working in `/home/user/p3-work/S2/C03-C-r3/repo`, a git repository. Before anything else run `source /home/user/p3-work/S2/C03-C-r3/env.sh` in
your shell; it puts the tools you need on PATH and changes to the repository.

## Limits

- Work only in `/home/user/p3-work/S2/C03-C-r3`. Do not read or search anything outside it. No network access, and no package
  installs beyond restoring the packages already referenced.
- Do not change the target framework, the SDK pin or package versions.
- Commit your work with git before you stop.

## Task

The requirement and its acceptance criteria are in `requirements/CLIN-52.md`. The standing requirements are in
`README.md`. Acceptance tests are provided in `tests/Clinic.Tests/Acceptance/CLIN52AcceptanceTests.fs`; they do not pass until the work is done, and they do not
cover every acceptance criterion. Existing behaviour must keep working.

## Authority

Implement only behavior supported by requirements or accepted decisions. Do not invent exceptions, precedence rules, or business policies. Record unsupported interpretations as unresolved questions. Do not treat your own proposed decisions as authorized.

## Decision checklist

Before you settle any consequential decision (see "When you stop"), answer these three questions for it, and record
the answers in the decision's `checklist` field in your report:

1. `support`: Which requirement or accepted decision supports it?
2. `invents`: Does it create an exception, a precedence rule or a business policy that no requirement or accepted
   decision states? (yes / no)
3. `otherBasis`: Does it rest on a note, a proposal, existing code or your own reasoning instead? (yes / no)

If 1 has no answer, or 2 or 3 is yes, do not implement the decision; record it as an unresolved question.

## When you stop

Write your completion report to `.work/report.json` and commit it. Use this shape (JSON):

```json
{
  "schema": "p3.report/1",
  "workItem": "CLIN-52",
  "outcome": "completed | blocked",
  "blockedReason": null,
  "requirements": [{ "id": "...", "status": "implemented | partially-implemented | not-implemented" }],
  "decisions": [
    {
      "id": "D1",
      "statement": "what you decided",
      "basis": "evidence | assumption",
      "evidence": ["path", "path#symbol", "requirements/<file>#<requirement id>", "<decision record id>"],
      "requirementIds": ["..."],
      "checklist": { "support": "...", "invents": "...", "otherBasis": "..." }
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
