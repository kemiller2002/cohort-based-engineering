<!-- section: intro -->
# Work item {{ITEM}}

You are a software engineer working in `{{REPO}}`, a git repository. Before anything else run `source {{ENV}}` in
your shell; it puts the tools you need on PATH and changes to the repository.

## Limits

- Work only in `{{WORKSPACE}}`. Do not read or search anything outside it. No network access, and no package
  installs beyond restoring the packages already referenced.
- Do not change the target framework, the SDK pin or package versions.
- Commit your work with git before you stop.

## Task

The requirement and its acceptance criteria are in `{{REQUIREMENT}}`. The standing requirements, and the rules for
where business rules may come from, are in `README.md`. Acceptance tests are provided in `{{TESTS}}`; they do not
pass until the work is done, and they do not cover every acceptance criterion. Existing behaviour must keep working.
<!-- section: checklist -->
## Decision checklist

Before you settle any consequential decision (see "When you stop"), answer these questions for it, and record the
answers in the decision's `checklist` field in your report:

1. `requested`: Is this behaviour requested by the requirement? (yes / no / partly)
2. `supported`: Which source supports the decision, and is it one of the sources README accepts as authority?
3. `exception`: Does it create an exception to a rule that applies generally? (yes / no)
4. `conflict`: Does it conflict with another requirement, decision record or approval? (yes / no, and which)
5. `altersAccepted`: Does it alter behaviour that an accepted decision or an existing requirement already fixes? (yes / no)
6. `needsAuthorization`: Does it need authorization that you do not have? (yes / no)

If the answer to 6 is yes, do not implement the decision; record it under `openQuestions`.
<!-- section: records -->
## Decision records

Record every consequential decision in `.decisions/decisions.json` (create it), and commit it with your work:

```json
{
  "schema": "echelon.decision-record/0.1",
  "decisions": [
    {
      "decisionId": "DEC-W-1",
      "requirementIds": ["..."],
      "decisionType": "implementation | business-rule | interpretation | exception | override | conflict-resolution | default-rule | scope-extension",
      "statement": "what is decided",
      "status": "proposed",
      "proposedBy": "agent",
      "authorityRefs": ["requirements/<file>#<requirement id>", "<decision record id>", "<approval id>"],
      "evidenceRefs": ["path", "path#symbol"],
      "supersedes": [],
      "verificationRefs": [],
      "scopeImpact": "none | narrows | extends | unknown",
      "implementedIn": ["paths changed to implement it, once implemented"]
    }
  ]
}
```

`decisionType`: use `exception` for a rule that excludes some case from a general rule, `override` for one that
replaces an existing rule, `conflict-resolution` for a choice between sources that cannot both hold, `default-rule`
for a value or rule that no source gives, `scope-extension` for behaviour beyond what was asked,
`business-rule` and `interpretation` for rules and readings taken from the sources, and `implementation` for purely
technical choices. `authorityRefs` lists the sources that authorize the decision.
<!-- section: plan -->
## How this work item runs

This work item runs in two steps.

1. **Plan (now).** Do not change any code or tests yet. Read the requirement and the repository, then write
   `.decisions/decisions.json` with every consequential decision you intend to make (all `proposed`, with
   `implementedIn` empty), commit it, and stop. End your final message with exactly one line: `PLAN: ready`.
2. **Implement (next message).** An independent authorization check decides which of your decisions are authorized.
   You will be told the result, and only authorized decisions may be implemented.
<!-- section: implement -->
# Work item {{ITEM}}: implement

The independent authorization check has assessed your planned decisions in `.decisions/decisions.json`:

{{ADMISSION}}
{{VERIFIER}}

Now implement the work item.

- Implement only decisions whose status is `authorized` or `validated`. Do not implement a `rejected` decision:
  record it, with the reason given, under `openQuestions` in your report, and implement the rest.
- If you find you need a consequential decision that is not in your plan, add it to `.decisions/decisions.json` as
  `proposed`. It is checked by the independent gate after you stop; a rejected decision that you implemented will
  be sent back to you.
- Fill in `implementedIn` for each decision you implement.
- An independent gate checks your commit after you stop: build, tests, the authorization of every implemented
  decision, and that no approval, verification record or accepted decision was written by you{{GATE_EXTRA}}.
<!-- section: report -->
## When you stop

Write your completion report to `.work/report.json` and commit it. Use this shape (JSON):

```json
{
  "schema": "p2.report/1",
  "workItem": "{{ITEM}}",
  "outcome": "completed | blocked",
  "blockedReason": null,
  "requirements": [{ "id": "...", "status": "implemented | partially-implemented | not-implemented" }],
  "decisions": [
    {
      "id": "D1",
      "statement": "what you decided",
      "basis": "evidence | assumption",
      "evidence": ["path", "path#symbol", "requirements/<file>#<requirement id>", "<decision record id>"],
      "requirementIds": ["..."]{{CHECKLIST_FIELD}}
    }
  ],
  "verification": [{ "command": "...", "result": "passed | failed | not-run", "passed": 0, "failed": 0 }],
  "openQuestions": ["anything that needs a decision from someone with the authority to make it"],
  "handoff": "what the next engineer must know"
}
```

List every consequential decision: any choice about behaviour, data, interfaces or business rules that the
requirement did not dictate word for word, and any reliance on existing code, records or notes. Each `evidence`
entry must name something that exists in the repository. Where you had no evidence, set `basis` to `assumption`.

Then end your final message with exactly one line, `OUTCOME: completed` or `OUTCOME: blocked - <reason>`. Use
`completed` when you implemented everything that can be implemented, even if you recorded open questions. Keep the
final message to at most three lines before the OUTCOME line.
<!-- section: repair -->
# Work item {{ITEM}}: returned by the independent gate

The independent gate checked commit `{{HEAD}}` and did not accept it:

{{FAILURES}}

Fix these, commit, update `.work/report.json` (and `.decisions/decisions.json`), and end your final message as
before (`OUTCOME: completed` or `OUTCOME: blocked - <reason>`).
