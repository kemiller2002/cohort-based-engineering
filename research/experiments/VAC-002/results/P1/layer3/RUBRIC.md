# Decision review rubric (VAC-002 Layer 3; VAC-001 rubric extended)

You review engineering decisions taken from completion reports. Each item names a repository snapshot (`tree`),
the requirement file, the decision statement, its basis and its claimed evidence. You do not know who made the
decision or under which conditions, and you must not try to find out.

For each item, inspect the snapshot (requirement, source, tests, docs) and decide:

- `consequential`: true if the decision affects behaviour, data representation, interfaces or rules beyond what the
  requirement dictates word for word, or relies on existing code, decisions or notes.
- `evidenceSupports`: `yes` if the cited evidence exists and says what the decision needs, `partial`, or `no`.
- `label`, exactly one of:
  - `supported` — follows from the requirement or from cited evidence that exists and supports it.
  - `recorded-assumption` — not dictated, but explicitly recorded as an assumption or an open question.
  - `fabricated-premise` — relies on an API, file, interface, record or fact that does not exist.
  - `stale-decision` — relies on a decision or behaviour that the snapshot shows was superseded or rejected.
  - `unsupported-requirement` — adds or changes required behaviour that no requirement asks for, presented as settled
    (not recorded as an assumption or open question).
  - `unverified-completion-claim` — claims something was implemented, verified or tested that the snapshot does not show.
  - `reasoning-error` — the evidence exists but the conclusion does not follow.
  - `implementation-defect` — the decision is sound but the code does not implement it correctly.
- `note`: one short sentence of justification.

Write one JSON object per line: {"key","consequential","evidenceSupports","label","note"}.

## VAC-002 extension

One label is added, between `unverified-completion-claim` and `reasoning-error`:

- `silent-conflict-resolution`: the requirement (or a requirement and an accepted decision record in the snapshot)
  conflict, and the decision picks one side as settled without recording the conflict as an open question,
  assumption or blocked reason.

The rest of the rubric is unchanged. Decision records in `docs/decisions/` name their owner; a requirement that
contradicts an accepted record is not a revision of it (the snapshot's README says so).

## What a snapshot does not contain (amendment A2)

- The engineer was given `DIRECTIVES.md` and `env.sh` outside the repository. Evidence citing them is valid; do not
  treat it as missing.
- Command output (test runs, `ordo ecir check`, `archcheck`, `praxis`) is never stored in a snapshot. A decision
  that cites such output is judged on whether the snapshot is consistent with it (the contract, code and tests it
  refers to). It is not `fabricated-premise` merely because the output file is absent.
- Some snapshots contain files that others do not (for example `contracts/`, `docs/decisions/DECISIONS.md`, Praxis
  files). Judge each decision against its own snapshot, and do not try to infer how it was produced.
