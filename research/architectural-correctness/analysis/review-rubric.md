# ARCH-001 blinded architecture review rubric (ARC-REV-01..03)

Preregistration draft. The reviewer is an independent Claude Code session (same model as the trial agents,
its own nonce, tools Read and Bash used read-only). It receives only: the architecture doctrine
(`FOUR-TIER-ARCHITECTURE.md`, SDE-DOCTRINE-003 v0.2.1), the repository's `LENDING-ARCHITECTURE.md`, this
rubric, the two requirement texts, and two **scrubbed** change sets of one trial:

- change set 1: base repository → the commit submitted for the initial requirement;
- change set 2: the follow-up starting commit → the commit submitted for the follow-up requirement.

Scrubbing (harness/review-scrub.py) removes `docs/architecture/` and `docs/contracts/`, blob ids, decision ids
(`DEC-…` → `DECISION-REF`) everywhere, and the words ARCH001, ordo, archcheck, submit, arm, contract, verifier
from code comments; commit messages are replaced by the neutral labels above and files appear in path order.
The reviewer is never told which arm, task replicate or run produced the change sets.

Score each criterion **0, 1 or 2** for each change set, citing evidence (file and line of the diff, with a
short quote). Judge only what the change set adds or changes, in the context of the code it touches.

## ARC-REV-01 Semantic authority (doctrine AR-07)

Domain meaning — what a value *is*, which rule applies, whether something is allowed — is decided in Tier 1
(semantic) and Tier 2 (transition) code, and other tiers ask those tiers rather than re-deciding.

- **2**: every new or changed domain rule lives in Tier 1/2; Tiers 3/4 only call it.
- **1**: the rule lives in Tier 1/2, but a Tier 3/4 site also re-derives part of it (a duplicated predicate, a
  local special case) without contradicting it.
- **0**: a domain rule is decided in Tier 3 or Tier 4 (application service, persistence adapter, CLI), or two
  tiers decide it differently.

## ARC-REV-02 Effect flow (doctrine AR-09)

Effects (clock, randomness, I/O, persistence, console) enter only at the Tier 4 edge and reach the core through
ports (records of functions defined in Tier 3); decisions are made by pure code and their results carried out
by the edge.

- **2**: no new effect below Tier 4; new effects go through an existing or new port wired in the composition root.
- **1**: effects stay in Tier 3/4 but bypass a port (e.g. a Tier 3 function reads a file directly), or a decision
  is interleaved with effects in a way that makes it untestable without them.
- **0**: an effect is performed or read in Tier 1/2, or Tier 4 presentation/persistence re-enters Tier 2
  decisions directly.

## ARC-REV-03 Single authority for duplicated facts (doctrine AR-19)

Each domain fact (a limit, a rate, a date rule, a status derivation) has one authoritative definition that
every use references.

- **2**: every fact the change introduces or uses has one definition, referenced everywhere.
- **1**: one fact is restated (a literal or predicate copied) but the copies agree.
- **0**: a fact is defined in two places that can drift, or the change set contradicts an existing definition.

## Output

Reply with one JSON object and nothing else:

```json
{
  "schema": "arch001.review/1",
  "changeSets": {
    "1": {"ARC-REV-01": {"score": 2, "evidence": [{"file": "src/...", "line": 12, "quote": "..."}], "rationale": "..."},
          "ARC-REV-02": {"score": 2, "evidence": [], "rationale": "..."},
          "ARC-REV-03": {"score": 2, "evidence": [], "rationale": "..."}},
    "2": {"ARC-REV-01": {"...": "..."}, "ARC-REV-02": {"...": "..."}, "ARC-REV-03": {"...": "..."}}
  }
}
```

A score below 2 must cite at least one evidence item. An empty change set (no production change) scores 2 on
every criterion with the rationale "no production change".

## Use in the analysis

Review scores are a secondary, descriptive outcome (they do not enter the primary metric or the Holm family).
The review session's cost is recorded as **evaluation cost**, separately from arm cost.
