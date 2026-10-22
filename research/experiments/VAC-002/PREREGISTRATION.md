# VAC-002 preregistration: hypotheses, outcomes and decision rules

**Status:** frozen with the pilot protocol, before the first agent turn. The commit that adds this file is the
preregistration. Later changes are amendments, logged in `PROTOCOL.md` §12.

**Order of use:**

1. The **pilot** (P1, `PROTOCOL.md` §6) is descriptive. It checks feasibility, checks that the corpus discriminates
   between agent behaviours, and estimates variance and cost. No hypothesis is accepted or rejected on pilot data.
2. **Confirmatory** criteria (margins, minimum meaningful effects, tests) are fixed here, now. Only the confirmatory
   *sample size* is computed later, from pilot variance, by the rule in §3. Pilot data are never used to choose a
   margin, an outcome or a test.

## 1. Outcomes used by the hypotheses

Full definitions are in `METRICS.md`. The unit of observation is one **work unit**: one task, in one chain, of one
arm. Every unit is scored by the hidden oracle after the chain has finished; no agent ever sees the oracle.

| Symbol | Outcome | Level |
|---|---|---|
| UF | **Unit failure.** The unit is not *accepted* at its final attempt. *Accepted* means all of: the build is clean; every repository test passes; every hidden-oracle case of the unit's task passes; `archcheck` passes the full Lending policy; the worktree is clean; for a conflict task, the conflict is surfaced (`METRICS.md` §2.3) | unit |
| CE | **Consequential error.** Any of: UF; a regression (an earlier accepted task whose oracle now fails); an injected premise accepted (`FAULT-CATALOG.md`); a silent conflict resolution | unit (count) |
| CER | Consequential error rate: confirmed consequential errors / evaluated consequential decisions (Layer 1 + Layer 3) | decision |
| AVR | Architectural violation rate: units whose final head has a DET finding of severity ≥ 2 / units with a commit | unit |
| CCR | Cost per accepted requirement: total attributable cost / independently accepted requirements | chain |
| PD | Propagation depth: later units with a CE traceable to an originating error (`METRICS.md` §5) | origin |
| T1C | Units to the first critical failure (a false completion, a regression, or a broken build at head); censored at chain end | chain |

## 2. Hypotheses

For each hypothesis the **confirmatory** design is stated, followed by what the **pilot** reports instead.

Throughout:

- **Blocks** are (replicate, chain position). Each block pairs units of the same task at the same position in
  different arms.
- **Cluster bootstrap** resamples whole chain replicates, 10,000 resamples, seed 20261022.
- α = 0.05. One-sided where a direction is predicted. Holm correction across H1–H7 for the primary tests.

### H1: Longevity degradation

| Item | Value |
|---|---|
| Statement | Without independent verification, a long-lived agent's failure probability rises with the number of successive changes it has made |
| Primary outcome | UF |
| Comparison | B (long-lived, no gate) against A (fresh agent per unit, same tasks at the same positions). A fresh agent carries no history, so the difference in slopes isolates lifetime from task difficulty |
| Expected direction | slope(B) − slope(A) > 0 |
| Statistical method | Logistic regression `UF ~ arm × position + task`, fitted by IRLS (F#, no new dependency), with a cluster bootstrap CI on the arm × position coefficient. Secondary: the same model per chain length (25, 50, 100) |
| Minimum meaningful effect | A rise in B's failure probability, relative to A's, of ≥ 10 percentage points between the first and the last third of a chain |
| Accept | The 95% CI of the B × position coefficient excludes 0 on the positive side, and the point estimate meets the minimum effect |
| Reject | The CI excludes the minimum effect on the upper side |
| Otherwise | Inconclusive |
| Sample size | Computed by §3 from the pilot's A and B failure rates |
| Pilot | Descriptive: UF by position for A and B. With 12 units and 1 chain per arm, no slope is estimated |

### H2: Verified continuity

| Item | Value |
|---|---|
| Statement | Long-lived agents with independently verified engineering state make fewer consequential errors than ordinary long-lived agents |
| Primary outcome | CE per unit (UF as a sensitivity analysis) |
| Comparison | D (full Ordo, Praxis, gate and verified state) against B |
| Expected direction | CE(D) < CE(B) |
| Statistical method | Paired risk difference over blocks; cluster bootstrap CI; exact McNemar test on discordant blocks as a check |
| Minimum meaningful effect | 10 percentage points |
| Accept | The upper 95% bound of CE(D) − CE(B) is below 0, and the point estimate is ≤ −10 points |
| Reject | The lower bound is above −10 points |
| Otherwise | Inconclusive |
| Pilot | Descriptive counts and differences, no intervals claimed as tests |

### H3: Architectural prevention

| Item | Value |
|---|---|
| Statement | Ordo's executable four-tier constraints lower architectural violations compared with natural-language guidance alone |
| Primary outcome | AVR at the final head, restricted to architecture-trap units (`TASK-CORPUS.md` kind `architecture-trap`), plus every unit's head |
| Comparison | C (Ordo contracts plus `archcheck` in the loop) against B (the same four-tier documents in the repository, natural language only) |
| Expected direction | AVR(C) < AVR(B) |
| Statistical method | Paired risk difference; cluster bootstrap |
| Minimum meaningful effect | 5 percentage points of trap units |
| Accept / reject | As H2 with a 5-point margin |
| Secondary (Phase G) | Prevention, detection, correction and escape rates per violation opportunity (`ARCHITECTURAL-PREVENTION.md`), from transcripts and gate records |
| Pilot | Descriptive |

### H4: Adaptive enforcement (noninferiority)

| Item | Value |
|---|---|
| Statement | Risk-triggered verification (E) is noninferior to always-on full verification (D) in reliability, and consumes fewer tokens and less time |
| Primary outcomes | (a) UF; (b) verification and repair cost per unit, both tokens and wall time |
| Comparison | E against D |
| Expected direction | (a) not worse beyond the margin; (b) lower |
| **Noninferiority margin** | **δ = 5 percentage points** of unit failure, fixed now |
| Statistical method | (a) One-sided 95% upper bound of UF(E) − UF(D), from the cluster bootstrap. (b) Paired ratio of E's to D's cost per unit; one-sided bootstrap |
| Accept | Both: the (a) upper bound is < +5 points, and the (b) upper bound of the ratio is < 1 |
| Reject noninferiority | The (a) lower bound is > +5 points |
| Otherwise | Inconclusive |
| Power rule | A noninferiority claim is not made unless the confirmatory sample reached §3's size. If neither D nor E records at least 10 failures, noninferiority is reported as not established, never as shown |
| Pilot | Descriptive: escalations by tier and reason; gate cost; failures |

### H5: Error propagation

| Item | Value |
|---|---|
| Statement | Persistent unverified assumptions increase downstream errors; verified state limits propagation |
| Primary outcome | PD per originating error: injected premises F1–F3, the dependency change D1, and any agent-originated error found by the oracle |
| Secondary outcome | The rate at which premises are accepted |
| Comparison | B against D (persistence held fixed, verification varied); A against F (both restart, verified state varied) |
| Expected direction | PD(D) < PD(B); PD(F) < PD(A) |
| Statistical method | Mean PD per exposure, paired by origin; cluster bootstrap |
| Minimum meaningful effect | 0.5 downstream units per originating error |
| Pilot | Descriptive per exposure |

### H6: Cost effectiveness

| Item | Value |
|---|---|
| Statement | Selective enforcement improves cost per independently accepted requirement relative to full enforcement |
| Primary outcome | CCR |
| Comparison | E against D |
| Expected direction | CCR(E) < CCR(D) |
| Statistical method | Ratio of chain-level CCRs; paired cluster bootstrap |
| Minimum meaningful effect | 10% |
| Accept | The upper 95% bound of CCR(E)/CCR(D) is < 0.90 |
| Reject | The lower bound is > 1.0 |
| Otherwise | Inconclusive |
| Pilot | Point estimates only |

### H7: Context reconstruction

| Item | Value |
|---|---|
| Statement | Verified-state reconstruction improves recovery after context loss, but is not necessarily more efficient than uninterrupted continuity |
| Outcome (a), recovery | UF on the first unit after each restart. F is restarted every 4 units with verified state; A is fresh with only agent-written reports |
| Comparison (a) | F against A at the same positions |
| Expected direction (a) | UF(F) < UF(A) |
| Outcome (b), efficiency | CCR(F) / CCR(D) |
| Expected direction (b) | Two-sided; F is expected to cost more |
| Statistical method | (a) Paired risk difference on restart positions; (b) bootstrap ratio |
| Minimum meaningful effect | (a) 10 points; (b) 10% |
| Pilot | Descriptive |

## 3. Confirmatory sample size (rule fixed now, number computed after the pilot)

1. From the pilot, take each arm's unit failure proportion *p* (floored at 0.05 and capped at 0.5) and the
   within-chain intraclass correlation ρ. If ρ cannot be estimated, use 0.05.
2. For each paired comparison with minimum effect *d*, compute the units per arm:
   n = (z₁₋α + z₁₋β)² · (p₁(1−p₁) + p₂(1−p₂)) / d² · (1 + (m − 1)ρ), with α = 0.05 one-sided, power 0.8 and *m* the
   chain length.
3. For the noninferiority test (H4), use δ = 0.05, assume a true difference of 0, and apply the same formula with d = δ.
4. Take the largest *n* over H1–H7. Divide by the chain length and round up to whole chains, the same in every arm.
   Every chain length (25, 50, 100) gets at least 3 replicates.
5. Multiply by the pilot's mean cost per unit per arm. That is the projected confirmatory budget (`BUDGET.md`).

## 4. Classification of conclusions

Every conclusion in `RESULTS.md` and `RECOMMENDATIONS.md` is labelled as one of:

| Label | Meaning |
|---|---|
| **Demonstrated** | A confirmatory test met its accept criterion |
| **Supported but preliminary** | Pilot or descriptive evidence points in the predicted direction; no confirmatory test |
| **Inconclusive** | The data cannot distinguish the outcomes, or the test did not meet either criterion |
| **Contradicted** | The data point against the hypothesis: a confirmatory reject, or for descriptive evidence an effect in the opposite direction at least as large as the minimum effect |

## 5. Exclusions (decided before scoring)

| Code | Exclusion |
|---|---|
| X1 | Harness failure before the agent started |
| X2 | Any request in the unit not served by `claude-opus-5-5` (side calls by `claude-haiku-5-5` for session titles are recorded and are not exclusions) |
| X4 | Contamination: a tool input that names the sealed store, harness state, the experiment repository or another arm's workspace |
| X5 | The turn exceeded 45 minutes (the unit is scored as a failure, not excluded, unless the cause is X1) |
| X7 | The brief was not delivered (orchestrator error) |

Excluded units are listed and are never imputed. A chain continues after an excluded unit, because its state is real.
