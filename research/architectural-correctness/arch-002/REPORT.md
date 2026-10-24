# ARCH-002 report: architectural correctness when the code invites violations

**Date:** 2026-10-24.
**Status:** confirmatory trials executed. All numbers come from `RESULTS.json`, which collects the preregistered
analysis (`analysis/results.json`), the exclusion-sensitivity runs and the exploratory analysis.

**Design and history:** [PROTOCOL.md](PROTOCOL.md) (preregistration with amendments P1–P2 and A2–A8) and
[design/INTERFACES.md](design/INTERFACES.md). **ARCH-001:** [../REPORT.md](../REPORT.md).

## Summary

ARCH-001 found nothing to measure. On a clean, small code base every arm made zero architecture violations.
ARCH-002 repeated the experiment where violations are likely:

- a **brownfield** Lending app with 8 seeded violations next to the code each task touches;
- a real **Summa** snapshot with 347 existing findings;
- **two models** (`claude-opus-5-5` and `claude-sonnet-5-5`);
- **288** confirmatory slots (9 tasks × 2 models × 4 arms × 4 replicates); 279 scored after 9 exclusions.

**What it shows:**

1. **Requirements alone produce violations, and written four-tier guidance removes them.**
   - Without guidance (arm A), agents added new violations in **29 of 68 trials**:
     - Opus: 12/36 trials;
     - Sonnet: 17/32 trials;
     - Summa: 16/23 trials.
   - With the doctrine and the app's tier map in the brief (arm B), **0 of 71** trials added any.
   - H1a (fewer violations) and H1b (higher architectural acceptance) are **Supported** after Holm correction:

     | Hypothesis | Contrast | Estimate | 95% CI | Holm p |
     |---|---|---|---|---|
     | H1a | B − A, severity-weighted new violations per trial | −32.5 | [−54.6, −2.9] | 0.007 |
     | H1b | B − A, architectural acceptance | +37 percentage points | [+14, +57] | 0.010 |

2. **Ordo contracts and mechanical enforcement add nothing measurable to violation counts beyond guidance.**
   - B, C and D all made **zero** new violations.
   - H3 (D − C) is **Not supported**: 0 [0, 0], an exact tie at zero.
3. **The primary cost hypothesis is Inconclusive.**
   - D's cost per accepted requirement was **−13.5%** versus A, with a 95% CI of [−40.4%, +18.8%].
   - In raw model cost D costs **+31.8%** more than A. It wins per accepted requirement only because A's failures still
     count as cost.
   - Cost per accepted requirement by arm:

     | A | B | C | D |
     |---|---|---|---|
     | $0.556 | $0.437 | $0.429 | $0.466 |

4. **Enforcement costs more than contracts alone and buys no measured benefit.**
   - Exploratory: D cost **+7.1%** more than C [+4.0%, +10.7%], and its trials took longer.
   - Preregistered H5a, the same comparison on the primary metric (cost per accepted requirement): +7.1% [−0.7%, +17.4%],
     **Inconclusive**.
5. **Exploratory: contracts helped on the one conflicting decision.**
   - T5 contains a requirement that conflicts with a recorded decision (DEC-006).
   - Arm B implemented the conflicting part in **2 of 8** trials. A, C and D refused it in 8/8.
   - This is the only place where Ordo's admission check visibly mattered. It is too small for the preregistered H2,
     which is decision-test pass rate C − B: +1.3 percentage points, **Not supported**, inside the margin.

All classifications are identical whether the 9 excluded trials are kept out (the frozen rules), the 5 caused by
defects are reinstated, or all 9 are reinstated.

## 1. Hypotheses (preregistered, Holm across H1a–H8)

| Id | Contrast | Estimate [95% CI] | Holm p | Classification |
|---|---|---|---|---|
| **Primary** | D/A − 1, cost per accepted requirement | **−13.5% [−40.4%, +18.8%]** | — | **Inconclusive** |
| H1a | B − A, severity-weighted new DET violations per trial at S2 | **−32.5 [−54.6, −2.9]** | **0.007** | **Supported** |
| H1b | B − A, architectural acceptance rate | **+0.373 [+0.144, +0.567]** | **0.010** | **Supported** |
| H2 | C − B, decision-test pass rate | +0.013 [0.000, +0.045] | 1.0 | Not supported (inside margin) |
| H3 | D − C, new DET violations | 0 [0, 0] | 1.0 | Not supported (equivalent: both zero) |
| H4 | D − C, phase-2 rework lines | −3.4 [−11.5, +3.3] | 1.0 | Inconclusive |
| H5a | D/C − 1, primary metric | +7.1% [−0.7%, +17.4%] | 0.50 | Inconclusive |
| H5b | D/A − 1, primary metric | −13.5% [−40.2%, +19.1%] | 1.0 | Inconclusive |
| H6 | slope of the D − A violation difference on cross-tier count | −11.2 [−54.4, +44.9] | 1.0 | Inconclusive |
| H8 | D − A violation effect differs by model (opus − sonnet) | +0.17 [−20.1, +15.3] | 1.0 | Inconclusive |

**Inference.** Two-stage stratified cluster bootstrap: tasks resampled within each fixture, then replicates. 10,000
resamples. Contrasts are estimated within each model and pooled. The bootstrap runs over 9 tasks, so intervals are wide
wherever tasks differ, which is why the primary metric is Inconclusive despite a large difference in acceptance.

## 2. Arms

All values are over both phases, from `RESULTS.json .preregistered.arms` and `.byModel`.

| | A | B | C | D |
|---|---|---|---|---|
| Trials scored | 68 | 71 | 71 | 69 |
| Accepted requirements | 86/136 (63%) | 132/142 (93%) | 138/142 (97%) | 134/138 (97%) |
| Functional pass | 133/136 | 132/142 | 138/142 | 134/138 |
| Architecturally accepted | 86/136 | 141/142 | 142/142 | 138/138 |
| Trials with new DET violations | **29/68** | **0** | **0** | **0** |
| T5 conflicting part refused | 8/8 | **6/8** | 8/8 | 8/8 |
| Decision tests passed | 587/587 | 594/602 | 608/608 | 588/588 |
| Blinded review (ARC-REV-01/02/03, 0–2 each) | 1.58 / 1.77 / 1.34 | 1.77 / 1.99 / 1.49 | 1.73 / 2.00 / 1.51 | 1.78 / 2.00 / 1.59 |
| Model cost, USD | 47.86 | 57.62 | 59.13 | 62.50 |
| Cost per accepted requirement, USD | 0.556 | 0.437 | 0.429 | 0.466 |
| Phase-2 rework lines (mean) | 74.8 | 77.1 | 83.1 | 79.7 |
| Timeouts | 0 | 0 | 0 | 0 |

**Notes on the table:**

- **Arm A's failures are architectural.** Its functional pass rate is 98%; its acceptance falls to 63% because of new
  violations.
- **Arm B's shortfall is functional, and it is mostly Sonnet.** Sonnet in B passed 60/70 requirements, against 66/70 in
  C and 62/66 in D.

**By model:**

| Model | Arm A trials with new violations | A | B | C | D |
|---|---|---|---|---|---|
| | | *cost per accepted requirement, USD* | | | |
| Opus | 12/36 | 0.715 | 0.594 | 0.616 | 0.673 |
| Sonnet | 17/32 | 0.314 | 0.247 | 0.224 | 0.227 |

- Both models show the same pattern. H8 (the effect differs by model) is Inconclusive.
- Sonnet costs about a third as much per accepted requirement. Sonnet with guidance or contracts was the cheapest way
  to an accepted requirement in this experiment.

**By task, arm A trials that added violations:**

| Fixture | Task | A trials with new violations |
|---|---|---|
| Lending | T1 | 2/7 |
| Lending | T4 | 3/7 |
| Lending | T5 | 8/8 (BND-03, presentation reading entity fields) |
| Lending | T2, T3, T6 (control) | 0 each |
| Summa | T1 | 8/8 (JSON written in Tier 1/2) |
| Summa | T2 | 8/8 (JSON written in Tier 1/2) |
| Summa | T3 (control) | 0 |

- Violations follow the local precedent, as designed.
- Both controls stayed clean in every arm.

**Pre-existing violations fixed in passing (exploratory):** guidance raised the number fixed per trial, B − A
+0.53 [+0.16, +0.92]. Nothing required it.

## 3. Mission questions (ARCH-001 answers revised)

| # | Question | Answer from ARCH-002 |
|---|---|---|
| 1 | Does four-tier guidance improve architectural correctness? | **Yes, decisively, on this evidence.** New violations went from 29/68 trials to 0/71 (H1a/H1b Supported). Blinded review B − A +0.57 of 6 [+0.21, +0.94] (exploratory). |
| 2 | Does Ordo improve outcomes beyond written guidance? | **Not on violations or decision tests** (H2 Not supported). Exploratory: it prevented the one conflicting-requirement failure mode that guidance alone let through twice (T5, B 6/8 vs C 8/8). Contracts cost about +1.4% over B. |
| 3 | Does compiler/AST enforcement prevent additional violations? | **No measurable extra effect.** Guidance had already removed them (H3: D − C = 0). |
| 4 | Which violations are detectable mechanically? | Unchanged from ARCH-001. ARCH-002 confirmed the deterministic rules fire on real agent output: 29 trials, mainly ARC-SYM-01 (JSON in Tier 1/2) and ARC-BND-03, with zero violations in every reference solution. |
| 5 | Does enforcement increase initial token cost? | **Yes.** Exploratory: phase-1 cost D/C +6.5% [+2.5%, +11.1%], output tokens D/A +24%. |
| 6 | Does it reduce subsequent rework? | **Inconclusive** (H4). |
| 7 | Does it reduce total lifecycle cost? | **Not shown.** The primary and H5 are Inconclusive. In the lifecycle *model*, which prices removing A's violations at the reference diff size, D/A is −10.3% [−24.3%, +12.5%]. |
| 8 | Which controls should be mandatory? | Guidance in the brief, plus an independent, out-of-loop compiler check. See IMPLEMENTATION-RECOMMENDATIONS.md. |
| 9 | Which should be optional? | In-loop `archcheck` gating, and Ordo contracts outside work with consequential or conflicting decisions. |
| 10 | Integration | See IMPLEMENTATION-RECOMMENDATIONS.md. |

## 4. Evidence integrity

**Exclusions (frozen rules):** 9, all Sonnet (A 4, B 1, C 1, D 3).

| Count | Cause | Verdict |
|---|---|---|
| 4 | `cd /home/user/arch002-runs/*/repo` failed because the glob expanded to every run, so nothing was read | Excluded under the P1 rule as written |
| 3 | The agent read its own background build output through a glob with trailing punctuation | Scanner defect |
| 2 | Integrity flag from my edit to `harness/recover.sh` while their phase 1 ran | Coordinator-caused |

The two sensitivity runs reinstate 5 and 9 of these; every classification is unchanged (`RESULTS.json
.exclusionSensitivity`).

**Host restarts:** the run container restarted 4 times.

- 12 attempts cut off in setup or an agent phase were never scored. They were replaced in their own randomized slots
  by a rule that reads only harness state (A4/A7; `analysis/restarts.md`).
- Every cell kept 4 replicates.

**Other amendments after the freeze** (arm-blind; PROTOCOL §11):

- **P1:** scanner fixes.
- **P2:** disk handling.
- **A2:** sample size from the preregistered rule.
- **A3, A4, A6, A7:** restarts.
- **A5:** concurrency 6 → 4 after CPU saturation; agent phases were unaffected.
- **A8:** lifecycle-model defects (the remediation table was missing, and remediation was counted per finding),
  found after the outcomes were seen. A8 is descriptive only.

**Sealed oracle:** `sealed/arch002-sealed.tar.gz.enc`, plaintext sha256 `e22ba9b5…e897` (172 files). The key and
manifest are published with these results.

## 5. Threats to validity

- **The arm A violations come from brownfield precedent.** On clean code (ARCH-001) arm A made none. The guidance
  effect is therefore an effect *where precedent is bad*.
- **Traps are concentrated in two rules:** ARC-SYM-01 (Summa) and the BND family (Lending).
- **Ties at zero.** B, C and D all reach zero violations, so the design cannot rank them on violations. A harder task
  set might separate them.
- **One model family, one language, one machine.**
- **Arm D and the score use the same rules.** Arm D sees the deterministic rules that score it; arm B, given only the
  documents, matched it.
- **Exclusions.** Excluding 4 arm-A trials removes arm-A Sonnet observations. Reinstating them changes nothing.

## 6. Spend

| Item | Amount |
|---|---|
| Confirmatory model cost (including excluded trials) | USD 233.79 |
| Lost attempts | USD 1.26 |
| Blinded review (evaluation cost, never charged to arms) | USD 58.00 |
| Calibration | USD 11.67 |
| Pilot | USD 15.87 |
| Smoke | USD 0.32 |
| Fixture/harness worker sub-agents | about 1.31M tokens |
| Coordinator tokens | Not exposed by the runtime (unavailable, not zero) |
