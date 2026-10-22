# VAC-002-03: A discriminating corpus and a second pilot before any confirmatory spend

Priority: P2
Owner system: Cohort-Based Engineering (research methodology)
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/` (`PILOT-RESULTS.md` §1 and §8, `RECOMMENDATIONS.md` R-EXP-4
to R-EXP-7). It continues VAC-CBE-001-R3 and R4.

## Finding

The VAC-002 pilot was designed to produce failures. In 72 units over six arms it produced none:

- 0 unit failures;
- 0 consequential errors;
- 0 architecture violations;
- 0 of 18 premises accepted;
- the dependency change was detected in every arm.

This is the third ceiling result in a row (VAC-001, ARCH-001, VAC-002). Under the preregistered power rule, a
confirmatory run on this corpus (about 5,850 units, about $4,000–4,500) could establish no reliability claim at any
spend.

## Requirements (proposed)

- **VAC-002-03-R1.** Build a harder 12-unit variant. Candidates:
  - the natural-language arms without the four-tier documents;
  - a brownfield fixture with existing violations to imitate (coordinate with ARCH-002);
  - a silent semantic dependency change, with no compile or test break;
  - premises only decision records or verified state can contradict;
  - tasks whose working implementation within the turn budget crosses a boundary unless a port is added.
- **VAC-002-03-R2.** Run it as a second pilot (about $45 of model cost at P1 rates) under VAC-002's frozen harness.
  Proceed to confirmatory chains only if some arm's unit-failure rate is ≥ 10% (`PROTOCOL.md` §7).
- **VAC-002-03-R3.** Before any confirmatory run:
  - implement the preregistered IRLS logistic model and the cluster bootstrap, validated on simulated chains with
    known effects;
  - use Layer 3 reviewers from a different model family.
- **VAC-002-03-R4.** Record an explicit spending ceiling for the confirmatory run before it starts.

## Acceptance evidence

- A sealed oracle and self-check for the new variant, committed before its pilot.
- Pilot results reporting the discrimination check.
- A recomputed sample size and budget.
