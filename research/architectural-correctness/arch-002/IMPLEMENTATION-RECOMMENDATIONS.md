# ARCH-002 implementation recommendations

These are based on [REPORT.md](REPORT.md) and supersede ARCH-001's recommendations where they differ.

| Label | Meaning |
|---|---|
| **Finding** | Preregistered, Supported |
| **Exploratory** | Post hoc |
| **Gap** | Verified by inspection |
| **Not supported** | No benefit shown |

None of these changes a production policy. Each needs review by its owner before adoption.

## Recommendations

| # | Recommendation | Basis | Changes ARCH-001? | Intake |
|---|---|---|---|---|
| R1 | **Put the four-tier doctrine and the repository's tier map into agent briefs by default** wherever a repository declares a tier map. The document instance must add no new rules beyond the doctrine. | **Finding.** H1a and H1b Supported: new violations 29/68 trials → 0/71, acceptance +37 points. The cost is +22.5% raw model cost, but cost per accepted requirement falls from $0.556 to $0.437. | Yes. ARCH-001's R6 made guidance optional; it was tested only at a ceiling. | `praxis/.praxis/inbox/documents/2026-10-24-ARCH-002-01-architecture-guidance-in-briefs.md` |
| R2 | Keep architecture *verification* independent and out of the agent loop, as in ARCH-001 R1/R2: Dokimos compiler-derived rules, Praxis host-verifier validation. ARCH-002 confirms the deterministic rules fire on real agent output. | **Finding**, together with **Gap.** In-loop D adds +7.1% cost over C with no added violation benefit. The out-of-loop verifier caught all 29 violating arm-A trials. | Confirms. | ARCH-001-01 (Praxis) and ARCH-001-02 (Dokimos), already merged |
| R3 | Use Ordo decision contracts where work touches recorded decisions that may conflict. Do not mandate them for routine work. | **Exploratory.** Guidance-only B implemented a requirement conflicting with DEC-006 in 2/8 trials; contracts (C, D) refused it in 8/8. H2 (decision-test rate) is Not supported. | Refines ARCH-001 R4: "opt-in" now has a named use case. | none (evidence too thin for a requirement) |
| R4 | Do not mandate in-loop `archcheck` gating. | **Not supported.** H3 D − C = 0; D costs more than C. | Confirms. | none |
| R5 | Default to the cheaper model for guided architecture-sensitive work, after confirming locally. | **Exploratory.** Sonnet with guidance or contracts: $0.22–0.25 per accepted requirement, against $0.59–0.67 for Opus, with the same zero-violation pattern. Sonnet in B had more functional failures (60/70). | New. | none (an operational choice, not a tool requirement) |
| R6 | Next experiment: tasks hard enough to separate B, C and D (B, C and D all reached zero violations here), plus H7 (grouped execution × guidance) as its own factorial. | **Finding** (ties at zero). | New. | `cohort-based-engineering/.praxis/inbox/documents/2026-10-24-ARCH-002-02-separate-guidance-contracts-enforcement.md` |

## Infrastructure lessons (PROTOCOL §11)

1. **Session containers restart.** Four restarts happened, at least one while a tracked task was running.
   - Long trial queues need idempotent recovery (`harness/recover.sh`).
   - Replacement has to be decided by a rule that reads only harness state.
2. **Contamination scanners must parse paths, not use regex on raw text.** Two false-positive classes were found:
   - a failed glob `cd`;
   - trailing punctuation around a path to the agent's own build output.
3. **Never edit harness files while trials run.** The integrity check correctly flagged two trials after I did.
4. **Run descriptive models in the pilot too.** The lifecycle model's remediation table was never generated, and its
   per-finding count was wrong. Both would have shown up at the pilot.
