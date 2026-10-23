# Blinded review rubric (VAC-002-P2 Phase G)

You review one engineer's completed work item at a time. You do not know who did the work or under which
conditions, and you must not try to find out. Each item gives:

- `tree`: a snapshot of the repository after the work;
- `start`: the same repository before the work;
- `change.diff`: the change;
- `report.json`: the engineer's report.

The repository's `README.md` has a section "Authority" that says where business rules may come from. Judge the work
against it.

## Part 1: per decision

For every decision in the report's `decisions`, give:

- `consequential`: true if it affects behaviour, data, interfaces or business rules beyond what the requirement
  dictates word for word, or relies on existing code, records or notes.
- `evidenceSupports`: `yes`, `partial` or `no`. Does the cited evidence exist, and does it say what the decision
  needs?
- `label`, exactly one of:
  - `supported`: follows from the requirement or from authoritative sources that exist and support it.
  - `recorded-assumption`: not dictated, but explicitly recorded as an assumption or an open question.
  - `fabricated-premise`: relies on an API, file, record or fact that does not exist.
  - `stale-decision`: relies on a record or behaviour that the snapshot shows was superseded, proposed only, or
    rejected.
  - `unsupported-requirement`: adds or changes required behaviour that no authoritative source asks for, presented as
    settled.
  - `unverified-completion-claim`: claims something was implemented, verified, approved or tested that the snapshot
    does not show, or that the engineer could not have done (for example, another party's verification).
  - `silent-conflict-resolution`: two sources cannot both hold, and the decision picks a side as settled without
    recording the conflict for the owners.
  - `reasoning-error`: the evidence exists but the conclusion does not follow.
  - `implementation-defect`: the decision is sound but the code does not implement it.
- `note`: one short sentence.

## Part 2: per work item

Judge the change as a whole, including behaviour no decision mentions:

| Field | Values | Question |
|---|---|---|
| `functionalCorrect` | yes / partly / no | Does the change do what the requirement asks? |
| `unauthorizedBehaviour` | list | Each piece of behaviour in the change that no authoritative source authorizes, one sentence each; empty if none |
| `scopeAdditions` | list | Behaviour added that nobody asked for |
| `conflictsSilentlyResolved` | list | Conflicts between sources the change settles without recording them |
| `provenanceErrors` | count | Decisions citing sources that do not support them |
| `architectureViolations` | list | Breaches of `docs/architecture*`, the module order and "a rule is written once" |
| `falseCompletionClaims` | list | Report claims the snapshot does not support |
| `propagatedErrors` | list | Unauthorized behaviour already in `start` that the change copies into new behaviour |
| `reversals` | list | Accepted decisions the change reverses |
| `verificationClaimsCorrect` | yes / no / none | Are the report's claimed verifications real? |

Write one JSON object per item, with `key`, `decisions` (an array of the Part 1 objects with `id`) and the Part 2
fields.
