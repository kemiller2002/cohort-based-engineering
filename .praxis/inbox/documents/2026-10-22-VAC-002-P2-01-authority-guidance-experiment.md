# VAC-002-P2-01: Vary the authority guidance before testing authorization controls again (P3)

Priority: P1
Owner system: Cohort-Based Engineering (research methodology)
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/P2/` (`PILOT-RESULTS.md` §3–§5, `STATISTICAL-ANALYSIS.md` §7,
`RECOMMENDATIONS.md` R-EXP-1, R-EXP-2).

## Finding

- **No unauthorized decisions without controls.** VAC-002-P2 gave five arms (natural language, checklist, typed
  records, executable authorization, adaptive review) the same 12 scenarios. Each scenario was built to tempt an
  unauthorized business decision. Fresh agents with **no** controls made **0 unauthorized decisions in 48
  opportunities** (Wilson 95% upper bound 7.4%).
- **The L04 replication.** The replication of VAC-002's L04 error was correct in all five arms.
- **Every repository carried an explicit "Authority" section** in its README. It names the sources of business rules,
  how proposed and superseded records behave, approval scope, and what to do with gaps and conflicts.
- **The section is a candidate cause, unproven.** It was not varied, so it may be what prevented the errors. VAC-002
  P1's README had no rule for requirement-vs-requirement conflicts, and its uncontrolled long-lived arm made the L04
  error.
- **The prevention question is still open.** The pilot could not test prevention: there was nothing to prevent.

## Requirements (proposed)

- **VAC-002-P2-01-R1.** Run P3 as a 2 × 2 design:
  - the README authority section present / absent;
  - executable authorization off / on, using contract v0.2 (VAC-002-P2-02).

  Add a checklist arm without the section.
- **VAC-002-P2-01-R2.** Add scenarios where the sources are silent on precedence (as in L04 under P1), and a
  long-lived-session arm on the L04 replication, to separate continuity from guidance.
- **VAC-002-P2-01-R3.** Fix the S12 corpus defect: APR-C01's unrepresentable "diabetes review clinic" qualifier.
- **VAC-002-P2-01-R4.** Gate any confirmatory spend on a base rate ≥ 10% in some uncontrolled arm. Record a spending
  ceiling first. The P2 rate was about $0.30–0.96 per execution.

## Evidence class

The base rate with guidance is **Demonstrated** for this corpus (0 / 48 observed). Guidance as the cause is
**Inconclusive**.
