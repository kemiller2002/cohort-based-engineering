# VAC-002-P3-02: Executable authorization (contract v0.2) prevented nothing and rejected authorized decisions

Priority: P1
Owner system: Ordo (decision admission); Cohort-Based Engineering (contract)
Target repositories: ordo, cohort-based-engineering
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/P3/` (`CONFIRMATORY-RESULTS.md` §5, `results/S2/e-rejections.json`,
`RECOMMENDATIONS.md` candidate D).

## Finding

- **Unauthorized decisions.** Arm E (contract + typed records + plan, admission, implement, gate with contract
  v0.2) made **7 / 18**, the same as no controls, against 3 / 18 for the contract alone. E was worse in all 4
  discordant blocks (p = 0.125, Holm 0.5).
- **What the controls achieved.** Admission and the gate prevented, detected or corrected **0** unauthorized
  decisions.
- **What they rejected.** **10 decisions in 10 of 18 executions, every one authorized or harmless:**
  - a tie-break for output order (3);
  - keeping accepted behaviour unchanged (2);
  - recorded "unresolved question" entries (4);
  - a correct refusal of an uncovered case (1, at the gate).
- **Four of the rejections caused harm.**
  - **Three unauthorized defaults.** The agent built no refusal for the uncovered case, and the existing code's 0.00
    default reached the output.
  - **One crash.** C03-E-r3's correct refusal was rejected under rule A5 (it cited the agent's own question record),
    and the repair turn replaced it with an exception.
- **Why the checker missed the errors that remained.** They lived in undeclared reused code (C06, 3) or arose from
  the rejections themselves (4).
- **Cost and time.** +67% per execution over the contract alone; median wall time 2×.

## Requirements (proposed)

- **VAC-002-P3-02-R1.** "Refuse the uncovered case and record the question" is an authorized outcome that needs no
  authority source. Admission never rejects a recorded question.
- **VAC-002-P3-02-R2.** Rule A5 (self-citation) does not reject a refusal or deferral that cites the agent's own
  unresolved question.
- **VAC-002-P3-02-R3.** Rule A6 does not apply to presentation choices (ordering, wording) or to keeping accepted
  behaviour unchanged.
- **VAC-002-P3-02-R4.** Remove executable authorization from any default path. Reconsider only after R1–R3 and a test
  that shows prevented errors, not passing checker tests.

## Evidence class

- **Control-induced harm:** Demonstrated as a mechanism (every rejection and its effect is listed); Preliminary as a
  rate (the experimenter's unblinded classification).
- **Prevention:** Contradicted in direction, not significant.
- **Cost:** Demonstrated.
