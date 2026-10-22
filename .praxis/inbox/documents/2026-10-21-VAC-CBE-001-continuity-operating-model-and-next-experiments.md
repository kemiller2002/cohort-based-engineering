# VAC-CBE-001: Operating-model updates from VAC-001, and the next continuity experiments

Priority: P2
Owner system: Cohort-Based Engineering (operating model and methodology)
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Existing material: CBE principle 5 ("Preserve useful context. Prefer continuity within a cohort") and
`docs/operating-model.md`. This input adds measured support and scope, plus the experiments needed before stronger
claims.

Experimental finding: `research/verified-agent-continuity/` (all deliverables) and `research/experiments/VAC-001/`.

## Findings in scope

- **Continuity cost.** Continuity within a chain of related, independently verified changes cut cost per accepted
  requirement by ~40%. No correctness, drift or hallucination cost appeared at 8 changes and 167k tokens.
- **Controls without measured benefit.** The full Echelon controls added +14% to +31% over continuity, with no
  measured benefit at ceiling correctness.
- **Verified state is not a cost lever.** Reconstruction from verified state cost +86% versus continuity, so it is
  a restart safety net, not a cost lever.
- **Dominant unsupported decision.** The commonest unsupported decision was a scope addition presented as settled
  (8/202 adjudicated).

## Requirements (proposed)

- **VAC-CBE-001-R1 (operating model).** In `docs/operating-model.md`, state that a cohort's agent continues across
  its successive work items by default, and restarts only on events: context pressure, a change of repository or
  ownership, or a gate failure that repair does not fix. Cite VAC-001 with its scope.
- **VAC-CBE-001-R2 (operating model).** Agents must record any extension of a rule to behaviour no requirement
  names as an assumption or open question. They must not present it as settled.
- **VAC-CBE-001-R3 (experiment R-EXP-1).** Design a fixture whose baseline fails. Candidates:
  - premises the repository cannot contradict;
  - decisions that live only in decision records or verified state;
  - underspecified requirements with hidden expectations;
  - cross-feature invariants without visible tests.

  Preregister H3, H5 and H6 against it.
- **VAC-CBE-001-R4 (experiment R-EXP-2).** Run chains of ≥ 24 changes that pass the compaction threshold, in the
  K1 isolated-CLI cache condition, with Layer 3 reviewers from another model family. The goal is to test
  lifetime-dependence (H2) and the compaction questions.

## Acceptance evidence

- An operating-model diff citing VAC-001.
- Preregistered protocols for R-EXP-1 and R-EXP-2, committed before any trial.
- Canonical work items created by Praxis with provenance linking to this input. Do not use GitHub Issues.
