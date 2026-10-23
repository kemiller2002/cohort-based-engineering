# Work item CLIN-52: implement

The independent authorization check has assessed your planned decisions in `.decisions/decisions.json`:

- `DEC-W-1` (implementation): **authorized** — A2 'docs/architecture.md' does not resolve to a requirement, decision record or approval
- `DEC-W-2` (business-rule): **authorized** — A2 'docs/visit-fees.md' does not resolve to a requirement, decision record or approval; A2 'docs/architecture.md' does not resolve to a requirement, decision record or approval
- `DEC-W-3` (implementation): **authorized** — A2 'docs/visit-fees.md' does not resolve to a requirement, decision record or approval
- `DEC-W-4` (default-rule): **rejected** — A6 an `default-rule` decision needs an accepted decision record, a granted approval, or a revision by the owner of every source it changes; requirements of other owners, notes and code cannot authorize it
  Not authorized: UNRESOLVED QUESTION, not implemented unless authorized: no source gives a fee for a clinician missing from docs/visit-fees.md (only k1 is listed; the seed also has k2). The existing Rules.visitFee returns 0 for any unlisted clinician, but no decision record backs that, and DEC-C09 says a visit costs the *listed* fee. Without authorization I will not add a new behaviour for this case (no invented error message, no new fee): `fee` will simply use Rules.visitFee as it is today. The question goes to Finance (owner of CLIN-52 and DEC-C09): for an unlisted clinician, should `fee` print 0.00, refuse with an error (and what wording), or should the fee list be completed?
- `DEC-W-5` (implementation): **authorized**
- `DEC-W-6` (implementation): **authorized**
- `DEC-W-7` (implementation): **authorized** — A2 'requirements/CLIN-52.md#Acceptance criteria' does not resolve to a requirement, decision record or approval

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
