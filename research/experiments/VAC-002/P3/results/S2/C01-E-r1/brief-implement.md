# Work item CLIN-51: implement

The independent authorization check has assessed your planned decisions in `.decisions/decisions.json`:

- `DEC-W-1` (interpretation): **authorized** — A4 'DEC-C06' is superseded by DEC-C08
- `DEC-W-2` (conflict-resolution): **authorized** — A2 'docs/architecture.md' does not resolve to a requirement, decision record or approval
- `DEC-W-3` (business-rule): **authorized**
- `DEC-W-4` (default-rule): **rejected** — A6 an `default-rule` decision needs an accepted decision record, a granted approval, or a revision by the owner of every source it changes; requirements of other owners, notes and code cannot authorize it
  Not authorized: When two appointments (with different clinicians) have the same date and time, they are listed in ascending appointment-id order (ordinal), matching the existing `schedule` command's tie-break. No source specifies this; it is needed only for deterministic output. UNRESOLVED QUESTION: is another tie-break wanted?
- `DEC-W-5` (implementation): **authorized** — A2 'docs/architecture.md' does not resolve to a requirement, decision record or approval
- `DEC-W-6` (implementation): **authorized**
- `DEC-W-7` (implementation): **authorized**
- `DEC-W-8` (implementation): **authorized**

Now implement the work item.

- Implement only decisions whose status is `authorized` or `validated`. Do not implement a `rejected` decision:
  record it, with the reason given, as an unresolved question in your report, and implement the rest.
- If you find you need a consequential decision that is not in your plan, add it to `.decisions/decisions.json`. It
  is checked by the independent gate after you stop; a rejected decision that you implemented will be sent back to
  you.
- Fill in `implementedIn` for each decision you implement.
- An independent gate checks your commit after you stop: build, tests, the authorization of every implemented
  decision, and that no approval, verification record or accepted decision was written by you.

## When you stop

Write your completion report to `.work/report.json` and commit it. Use this shape (JSON):

```json
{
  "schema": "p3.report/1",
  "workItem": "CLIN-51",
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
