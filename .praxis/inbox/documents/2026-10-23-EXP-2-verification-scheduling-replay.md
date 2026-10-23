# EXP-2: Verification scheduling, offline replay first

Priority: P2
Owner system: Cohort-Based Engineering (research methodology)
Target repositories: cohort-based-engineering (protocol and analysis). It reads praxis and dokimos CI history; it changes
nothing there.
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Program: `program/EXPERIMENTS.md` §3, `program/IMPLEMENTATION-PLAN.md` A1/C5, `program/CONTRACTS.md` C5.

## Finding

- **CI runs too often to be the bottleneck it is.** Praxis CI runs on every push and takes about 23–29 minutes; Praxis
  main stayed red for days because of runner drift. The R001 integration and verification phase took about 150 min
  against a 90 min budget.
- **No dependency-aware selection exists** (`program/CURRENT-STATE.md` A1, status 5). Debounced CI exists in Dokimos;
  praxis#122 proposes it for Praxis.
- **Prior adaptive-verification evidence saved nothing,** at the agent-control level: VAC-002 arm E, P2 arm E, REL-001 F4.
  It has never been measured at the CI-scheduling level.

## Requirements (proposed)

- **EXP-2-R1.** Before looking at outcomes, preregister: the `praxis.verification-map/0.1` used, the commit range (≥ 50
  consecutive main commits each from praxis and dokimos), the metrics, and H1/H2 as stated in EXPERIMENTS.md §3.
- **EXP-2-R2.** Phase 1 is an offline replay at $0 provider cost. Use GitHub Actions history to compute CI executions
  and minutes avoided, and failures escaped or delayed under (a) A1 shadow selection and (b) checkpoint-only full CI.
  List every escaped failure individually; classify flaky failures rather than discarding them.
- **EXP-2-R3.** Phase 2 is a two-week prospective shadow of A1 on program work. Phase 3 reads Rehearsal 3's ledgers
  observationally and never modifies Rehearsal 3.
- **EXP-2-R4.** Promotion of selection or checkpoint CI to enforcing mode follows EXPERIMENTS.md §6 only. The never-deferred
  gates (RELEASE-GATES.md §2) are excluded from any selection.

## Acceptance evidence

Frozen protocol committed before the replay; replay scripts and raw CI data committed under
`research/experiments/EXP-2/`; a report that states limitations, including defects historical CI also missed.
