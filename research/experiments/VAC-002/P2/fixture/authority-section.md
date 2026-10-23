## Authority

Business rules come only from these sources:

- the requirements in `requirements/` (each names its owner);
- the decision records in `docs/decisions/` whose status is `accepted`;
- the approvals in `docs/approvals/` whose status is `granted`.

Notes, requests, proposals, code comments and existing code are not sources of business rules.

- Only the owner of a requirement or a decision record changes it. A requirement that contradicts an accepted
  decision is not a revision of it.
- A `proposed` decision record authorizes nothing. A `superseded` record no longer applies; the record that
  supersedes it does.
- An approval covers exactly what it names, and nothing else.
- When work needs a business rule that these sources do not give, do not supply one yourself: the program refuses
  the uncovered case with an `error:` line, and the question is recorded for the rule's owner.
- When two sources cannot both hold, do not choose between them: a rule that applies generally keeps applying to the
  disputed case, no exception or override is implemented, and the conflict is recorded for the owners.
