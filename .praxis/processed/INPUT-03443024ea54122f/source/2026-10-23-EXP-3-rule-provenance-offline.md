# EXP-3: Rule provenance before implementation, offline accuracy first

Priority: P1
Owner system: Cohort-Based Engineering (research methodology); Dokimos supplies the audit (VC-004, VAC-002-P3-03)
Target repositories: cohort-based-engineering
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Program: `program/EXPERIMENTS.md` §4. Extends VAC-002-P3-03-R3 and VAC-002-P3-01-R2 (both in this inbox); not a duplicate:
it adds the zero-cost accuracy phase and the pre-implementation arm.

## Finding

- **Every error came from reused code.** All 36/36 confirmed unauthorized decisions in P3 reused a rule embedded in
  existing code: a superseded rate, an unrecorded exemption, or a silent default.
- **Only post-hoc review caught C06.** It beat every control (15/15) and was flagged only by post-hoc blinded review.
- **The audit's accuracy is unmeasured.** The proposed Dokimos provenance audit (VC-004) has no measured precision or
  recall. Showing its findings to agents before measuring them risks P3's control-induced harm.

## Requirements (proposed)

- **EXP-3-R1.** Phase 1, at $0: run the Dokimos rule-provenance audit
  (`dokimos/experiments/rule-provenance/`) over the P3 corpus, C01–C06 plus the discovery scenarios. Compare it
  against the sealed labels of which code-embedded rules are unauthorized, with the label mapping preregistered.
  Report precision, recall and the false owner-question rate.
- **EXP-3-R2.** Phase 2 runs only if R1 meets recall ≥ 90% and false-question rate ≤ 10%, and only under an
  owner-authorized ceiling (proposed $60 hard, stop at $48). It is a paired experiment: no contract, contract, and
  contract plus the audit's owner questions shown before implementation (non-blocking). It covers the P3 mechanisms:
  - C01/C02 superseded values;
  - C05/C06 exemptions, including the "operational fact" framing;
  - C03/C04/D19 silent defaults;
  - D19/D21 implementer tests that lock errors in.
- **EXP-3-R3.** Report false rejections and harm as P3 did (`results/S2/e-rejections.json` format). An audit finding
  never blocks in this experiment.

## Acceptance evidence

Frozen protocol before any run; phase 1 data and scripts; a budget ledger if phase 2 runs; evidence classes per hypothesis.
