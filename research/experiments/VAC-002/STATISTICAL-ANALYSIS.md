# VAC-002: statistical analysis (Phase I)

**Scope.** The analysis that was run on pilot P1, how it handles the structure of the data, which preregistered
analyses could not be run, and the eight required figures.

**Evidence class.** Pilot only, so everything here is descriptive or exploratory. No preregistered test was run
(`PREREGISTRATION.md` §2, "Pilot" rows).

**Code.** `harness/analyze.fsx` (units, summary, contrasts, phaseg, dataset, blind) and `harness/plots.fsx`. Both are
F#, with no dependency beyond the .NET SDK.

**Outputs:** `results/P1/analysis.json`, `contrasts.json`, `phase-g.json`, `decision-dataset.jsonl` and `figures/`.

## 1. Data structure and how it is handled

| Feature the analysis must account for | Pilot design | How the pilot analysis handles it | Confirmatory plan (`PREREGISTRATION.md`) |
|---|---|---|---|
| Paired tasks | Every arm works the same 12 tasks in the same order | Contrasts are paired by position (block = task) | Blocks = (replicate, position) |
| Repeated measurements | 12 units per chain; up to 74 decisions per chain | Units are never pooled across arms as independent. Decisions are analysed per chain (Layer 3), and no test is run over decisions | Cluster bootstrap over whole chains |
| Chain length | 12 only | Not estimable | Separate models at 25, 50 and 100 |
| Task difficulty | Fixed effect of task | Paired design removes it from contrasts | `task` term in the logistic model |
| Model variation | One model and effort setting | Not estimable; stated as a limitation | Not in scope of VAC-002 |
| Failure clustering (ICC) | 0 failures | ρ cannot be estimated; the preregistered default ρ = 0.05 is used for sizing | Estimated from the confirmatory chains |
| Censored lifetimes | No chain failed | Every chain is right-censored at 12 (Kaplan–Meier) | Kaplan–Meier per arm, log-rank against B |

## 2. What was computed

1. **Per-arm outcomes** (`analysis.json`): UF, CE and its components, regressions, false completions, AVR, the fault
   exposures, CCR, tokens, tool uses, wall time, gate runs, compactions and contamination.
   - All reliability counts are 0 (`RESULTS.md` §1).
   - **Interval for a zero count.** The exact one-sided 95% upper bound for 0 events in n units is 1 − 0.05^(1/n):
     22.1% for one arm (n = 12) and 4.1% pooled (n = 72).
2. **Exploratory cost contrasts** (`contrasts.json`).
   - **Statistic.** The relative difference in total model cost over the 12 positions.
   - **Interval.** Percentile bootstrap resampling positions with replacement: 10,000 resamples, seed 20261022.
   - **Per-turn cost.** The difference of the cumulative session cost (amendment A1).
   - **Limit.** The interval reflects task-to-task variance within one chain. It says nothing about chain-to-chain
     variance, which needs replicates, so it is **not** a test of H6 or H7(b).
3. **Effect sizes**, as point estimates with exploratory intervals:

   | Contrast | Point | Interval |
   |---|---|---|
   | B vs A | −32.0% | [−41.8, −22.9] |
   | D vs B | +12.9% | [−3.7, +34.1] |
   | E vs D | +3.8% | [−17.6, +24.1] |
   | F vs D | +16.2% | [−8.9, +39.5] |

   Full table: `RESULTS.md` §2.
4. **Survival** (`analysis.json` `kaplanMeier`). Time to the first critical failure, with failure defined as a
   consequential error. Every arm's curve is flat at 1.0 and censored at position 12.
5. **Error as a function of cumulative work.** Every unit at every position was accepted (figure 2). No trend can be
   fitted to a constant.
6. **Sample size** (`PREREGISTRATION.md` §3), applied to the pilot: 975 units per arm. Computation:
   `PILOT-RESULTS.md` §8.

## 3. Preregistered analyses not run, and why

| Analysis | Hypothesis | Why not run |
|---|---|---|
| Logistic regression `UF ~ arm × position + task` (IRLS) with a cluster bootstrap | H1 | 0 events; the likelihood has no finite maximum. Also, one chain per arm gives no clusters. **The IRLS fitter is not implemented**: it is specified, and must be built and tested on simulated data before a confirmatory run |
| Paired risk difference and exact McNemar test | H2, H3, H7(a) | 0 discordant blocks. McNemar's p = 1 by construction, so it is uninformative and not reported as a result |
| One-sided noninferiority bound | H4(a) | The power rule (≥ 10 failures in D or E) is not met. Reported as "not established" |
| Mean PD per exposure | H5 | 0 premises accepted. The computed PD is 1 in three of 24 exposures, all lexical false matches on inspection (`RESULTS.md` I6), so 0 after inspection. Reported descriptively |
| Chain-level CCR ratio with a cluster bootstrap | H6, H7(b) | One chain per arm. Reported as an exploratory ratio with the position bootstrap |
| Holm correction | H1–H7 | No primary test, so nothing to correct |
| Log-rank test | survival | No events |

## 4. Figures

All 8 required figures are produced by `harness/plots.fsx` from `analysis.json` alone. **No point is invented.**
Missing or inconclusive data is written on the figure as text. Each figure is an SVG with a light and a dark variant
(`prefers-color-scheme`), fixed arm colours (A–F, never by rank), a legend and direct labels.

| # | File (`results/P1/figures/`) | Shows | Inconclusive or missing data, as marked on the figure |
|---|---|---|---|
| 1 | `1-cost-per-accepted-requirement.svg` | CCR by arm (bars) | None; this is the one outcome that varies |
| 2 | `2-error-by-chain-position.svg` | Accepted or not, per arm and position (a dot grid) | All accepted; "no failures observed" |
| 3 | `3-architectural-violations.svg` | Violations at a scored head, by arm | All 0; "rates undefined (no proposals)" |
| 4 | `4-error-propagation-depth.svg` | PD per fault origin and arm (a grid of numbers) | Three cells show "1 → 0*": computed by lexical match, 0 after inspection (I6) |
| 5 | `5-verification-cost-vs-escape.svg` | Gate host CPU per arm (bars), with escaped units written beside each | Escape rate 0 for every arm: no trade-off exists, so no scatter is drawn |
| 6 | `6-survival-by-arm.svg` | Kaplan–Meier step curves | Flat at 1.0, all censored at 12 |
| 7 | `7-context-size-vs-error.svg` | Peak prompt tokens per unit against acceptance | No failures, so no relationship can be estimated |
| 8 | `8-adaptive-escalation.svg` | E's tier per position, with model cost per unit | Low tier never used (S8) |

## 5. Reading the uncertainty correctly

- **Zero events are not proof of safety.** "0 of 12" is compatible with a per-unit failure probability up to 22% in
  any one arm. Two arms both at 0/12 could differ by up to about 22 points, which is far above the preregistered 5-
  and 10-point effects.
- **The cost intervals are optimistic.** They omit chain-to-chain variance, which one chain per arm cannot measure.
  The true intervals are wider by an unknown amount.
- **Continuity's saving has now been seen in three runs:**
  - VAC-001 P1+R1, at K0 (shared prompt cache with the orchestrator): −40.9%;
  - VAC-001 F1, at K0: −38.1%;
  - VAC-002 P1, at K1 (isolated CLI processes, with no shared cache): −32.0%.

  The direction is stable. The smaller size at K1 fits VAC-001's caveat that K0 cache sharing could distort the gap,
  but one K1 chain cannot separate that from the fixture difference.
