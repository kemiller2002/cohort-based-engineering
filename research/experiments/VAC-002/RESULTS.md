# VAC-002: results

**Status: checkpoint, not complete.**

| Done | Not done |
|---|---|
| Harness (six arms, gate, adaptive policy, verified state, sealed oracle, Layer 3) | Confirmatory 25-, 50- and 100-unit chains |
| Bounded pilot P1: 6 arms × 12 units, scored by the hidden oracle | Any confirmatory test of H1–H7 |
| Layer 3 blinded decision review of the pilot | |

**Why the confirmatory run was not done.** No spending ceiling was given for it (`BUDGET.md`). The preregistered
discrimination check (`PROTOCOL.md` §7) also failed: every arm reached the ceiling, so a confirmatory run on this
corpus could not establish any reliability claim at any spend (`PILOT-RESULTS.md` §8).

**Classification.** Every conclusion is labelled as `PREREGISTRATION.md` §4 defines. No conclusion here is
**Demonstrated**, because no confirmatory test was run. Figures from VAC-001 and ARCH-001 that *were* demonstrated
there are marked as such and cited from `BASELINE.md`.

**Sources:** `PILOT-RESULTS.md` and `results/P1/` (`analysis.json`, `contrasts.json`, `phase-g.json`, `layer3/`).

## 1. Reliability outcomes, all arms

| Outcome (`METRICS.md`) | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Unit failure (UF) | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| Consequential errors (CE) | 0 | 0 | 0 | 0 | 0 | 0 |
| Regressions of earlier tasks | 0 | 0 | 0 | 0 | 0 | 0 |
| False completion claims | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| Architectural violations at a scored head | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| Premises accepted (F1, F2, F3) | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| D1 (silent dependency change) missed | no | no | no | no | no | no |
| Silent conflict resolution (L04, L08) | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| Propagation depth per exposure (PD), after inspection (I6) | 0 | 0 (computed 1 at F3) | 0 | 0 (computed 1 at F1) | 0 (computed 1 at F1) | 0 |
| First critical failure (survival) | censored at 12 | censored at 12 | censored at 12 | censored at 12 | censored at 12 | censored at 12 |

**Zero events everywhere.** With 0 events in 12 units, the exact one-sided 95% upper bound on one arm's per-unit
failure probability is 22%. Pooled over all 72 units it is 4.1%. These bounds do not limit the *difference* between
arms, which is what H1–H7 ask about.

## 2. Cost outcomes

| | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Cost per accepted requirement (CCR) | $0.337 | $0.229 | **$0.228** | $0.259 | $0.269 | $0.301 |

Exploratory paired contrasts, with a bootstrap over positions (task variance only; one chain per arm):

| Contrast | Point | 95% interval |
|---|---|---|
| B vs A | −32.0% | −41.8% to −22.9% |
| C vs B | −0.7% | −12.1% to +10.4% |
| D vs B | +12.9% | −3.7% to +34.1% |
| E vs D | +3.8% | −17.6% to +24.1% |
| F vs D | +16.2% | −8.9% to +39.5% |
| F vs A | −10.7% | −28.7% to +8.5% |

## 3. Hallucinations and unsupported decisions (Layer 3)

*(Filled from `results/P1/layer3/` once the blinded review completes; see §3 below as updated.)*

## 4. Instrument findings (defects found by the pilot, not hypotheses)

| ID | Finding | Effect | Disposition |
|---|---|---|---|
| I1 | Verified-state promotion matches requirement ids as **text** in acceptance test files. D's agent wrote "LEND-L04-R3 is not implemented" in a test header, and the harness promoted LEND-L04-R3 to `verified` | A false fact entered the verified state. D's agent noticed and rejected it at units 6 and 10. No outcome was affected | Recommendation R-VS-1. Strengthens VAC-001 R-ORDO-1 |
| I2 | `total_cost_usd` is cumulative per resumed session | The frozen budget script over-counted by 2.8× | Fixed by amendment A1 before scoring |
| I3 | The Layer 3 bundle stripped cited evidence (A2), then paired items with the wrong snapshot (A3) | The first two reviewer passes are void | Fixed before any valid label; void bundles kept |
| I4 | Adaptive signal S8 (an open question in the report) fires on every unit | The adaptive policy could never select the low tier | Recommendation R-AD-2 |
| I5 | D1 broke 30–53 visible tests in every arm | The dependency change was loud, not silent, so it could not discriminate | R-EXP-4 |
| I6 | The propagation tracer's citation step (`METRICS.md` §5 step 3) is a lexical match over later reports. It matched three later units: D and E unit 8 ("newest first", describing notice-history order, not fines) and B unit 11 (naming `opendays-2.0.0.md` as *incorrect*, a carried-forward rejection) | The computed PD is 1 in three arm-origin cells; on inspection none is propagation. No dependent oracle case failed | The computed values are kept in `analysis.json`. The inspection is in `results/P1/propagation-adjudication.json` and on figure 4. A confirmatory run needs a semantic link, not a lexical one (R-EXP-5) |

## 5. Hypotheses

| | Hypothesis | Pilot evidence | Class |
|---|---|---|---|
| H1 | A long-lived agent's failure rate rises with changes made | 0 failures in A and B through 12 units, across one compaction in B | **Inconclusive** |
| H2 | Verified state lowers consequential errors (D < B) | 0 vs 0 | **Inconclusive** |
| H3 | Executable constraints lower architectural violations (C < B) | 0 vs 0, including the trap unit L02 | **Inconclusive** |
| H4 | Adaptive verification is noninferior to full verification, and cheaper | (a) 0 vs 0 failures: noninferiority not established (power rule). (b) E's cost ratio to D is 1.04, interval 0.82–1.24 | **Inconclusive** |
| H5 | Persistent unverified assumptions propagate; verified state limits it | 0 premises accepted in any arm. PD = 0 everywhere after inspection; 3 lexical citation matches were not propagation (I6) | **Inconclusive** |
| H6 | Selective enforcement improves CCR (E < D by ≥ 10%) | E/D = 1.04, opposite in direction to the hypothesis but smaller than the 10% minimum effect | **Inconclusive** (not Contradicted: the effect is below the minimum) |
| H7(a) | Verified-state reconstruction improves recovery after a restart (F < A) | 0 vs 0 at restart positions | **Inconclusive** |
| H7(b) | Reconstruction is not necessarily more efficient than continuity | F/D = 1.16, interval 0.91–1.40, in the predicted direction | **Supported but preliminary** |

## 6. The ten final questions

### Q1. How long can an agent work before reliability begins to degrade?

**Not found within 12 changes.** No arm failed. That includes the long-lived arms B–E, each of which crossed one
automatic compaction (at 149–156k prompt tokens, units 8–10) and passed every later unit with no regressions.
VAC-001 (24 units, K0) and ARCH-001 (64 single-task trials) also never observed degradation. The onset, if any, lies
beyond 12 chained units for this task class, or the corpus is too easy to reveal it.

**Class: Inconclusive.** The point at which degradation begins was not observed. The 25-, 50- and 100-unit chains
that could show it were not run.

### Q2. Does an agent become more reliable as verified engineering knowledge accumulates?

**No evidence either way on reliability.** D (verified state) and B (none) both made 0 errors.

**Evidence against the mechanism as built.** The verified state admitted a false entry (I1), which the agent itself had
to correct. Verified knowledge is only as reliable as its promotion rule.

**Class: Inconclusive** (reliability). **Supported but preliminary** that text-matched promotion is unsafe (one
observed instance).

### Q3. Does persistent context preserve useful knowledge or propagate mistakes?

**Preserves knowledge, in the sense of cost.**

- The long-lived arm was 32% cheaper than fresh agents (B vs A). VAC-001 found −40.9% [−48.1, −33.0] at K0;
  this is the first measurement at K1, where isolated processes share no prompt cache.
- The saving comes from cache economics: A wrote 2.7× more cache and made 1.7× more tool calls.

**Propagation was not observed.** Every injected premise was rejected at its first exposure in every arm, so there was
nothing to propagate. PD is 0 after inspection; the tracer's three lexical matches were not propagation (I6). No evidence that persistence spreads mistakes. Also no evidence that it does not, for
mistakes that get past the first check.

**Class:** preserves useful knowledge (cost): **Supported but preliminary** in VAC-002, consistent with VAC-001.
Propagates mistakes: **Inconclusive**.

### Q4. Which Ordo mechanisms prevent architectural errors?

**None was observed preventing one, because none was ever proposed.** 0 violations occurred in any arm, including on
the trap task and in arms A and B, which had no checker (`ARCHITECTURAL-PREVENTION.md`).

**What Ordo did do.**

- Contract admission refused the two contracts with decision conflicts (L04, L08), naming the conflicting
  requirement.
- That is decision-conflict prevention, not architecture. A and B surfaced the same conflicts without Ordo.
- In-loop `archcheck` ran 121 times with 0 findings, and cost no measurable model spend (C vs B −0.7%).

**Class: Inconclusive.** Typed decision records were not isolated as a separate arm, so they are **not measured**.

### Q5. Which Dokimos checks detect errors that otherwise escape?

**None in this pilot.**

- The independent gate ran 36 times (D, E and F) with 0 rejections, 0 false positives and 0 false negatives against
  the hidden oracle.
- No error escaped in the ungated arms A–C either, so no check had anything to detect.
- The gate's value is the counterfactual "what would have escaped", and that was 0 everywhere.

**Class: Inconclusive.**

### Q6. What percentage of verification cost can be removed without an unacceptable increase in escaped errors?

**Measured removals, each with 0 escapes on both sides:**

| Removal | Saving | Escapes |
|---|---|---|
| Adaptive gating (E vs D) | 10% of gate host CPU, 0% of model cost (E cost 3.8% *more*) | 0 vs 0 |
| Dropping the Praxis protocol, gate and verified state (C vs D) | 12% of model cost, 100% of gate host CPU | 0 vs 0 |
| Dropping all Echelon controls (B vs D) | 11% of model cost | 0 vs 0 |

**What is not known.** Whether any of these removals raises escapes. With 0 events, the experiment cannot bound the
increase below the 5-point noninferiority margin (H4 power rule).

**Class: Inconclusive.** The pilot cannot certify any percentage as safe to remove. It shows only that at the
correctness ceiling, about 11–12% of model cost is spent on verification controls that caught nothing.

### Q7. Is adaptive enforcement better than always-on enforcement?

**No, in this pilot.**

- **Reliability.** Equal: 0 vs 0. Noninferiority is not established.
- **Cost.** E was not cheaper: +3.8% model cost, −10% gate host CPU.
- **Why.** The policy's only lever was host-side gating, and gating is not where the cost is. S8 also prevented any
  low-tier unit.
- **What worked.** The policy did escalate exactly the three hardest units, hindsight-free.

**Class: Inconclusive.** It leans toward *contradicted* on cost for policy 1.0.0, but the effect (+3.8%) is below the
10% minimum, so it is not classed as Contradicted. Hindsight-free and auditable: **Demonstrated** as a design
property, by inspection rather than by test.

### Q8. Does restarting an agent provide any reliability benefit?

**No reliability benefit observed.** F (restarted every 4 units with verified-state reconstruction), D (continuous)
and A (fresh each unit) all made 0 errors.

**The cost of restarting.**

- **F vs D.** F cost 16% more than D. Each restart costs about +$0.38.
- **F vs A.** F cost 11% less than A. Restarting every 4 units is cheaper than every unit, consistent with VAC-001,
  where a restart every unit cost +86% over D.
- **Compaction.** The long-lived arms compacted once each with no harm, so restarting to avoid compaction bought
  nothing here.

**Class:**

| Claim | Class |
|---|---|
| Reliability benefit | **Inconclusive** |
| Restarting costs more than continuity (H7b) | **Supported but preliminary** |

### Q9. What is the optimal cost per independently accepted requirement?

**Lowest observed: $0.228**, from C (long-lived, Ordo contracts and in-loop `archcheck`). B (long-lived, no
controls) was effectively the same at $0.229.

At equal (ceiling) reliability, the cheapest configuration is a **long-lived agent with lightweight executable
constraints**. Adding the Praxis protocol, gate and verified state (D) costs $0.259 (+13%); fresh agents cost $0.337
(+47%).

**Caveats:** one chain per arm, a 12-unit chain and one fixture. Per-unit cost grows with chain length, and no
optimum over chain length was estimated.

**Class: Supported but preliminary.** Two findings carry this class:

- continuity is cheaper than fresh agents (B vs A), now seen in three runs, two at K0 in VAC-001 and one at K1 here;
- C ≈ B.

### Q10. Which Echelon engineering changes should be implemented immediately, deferred, or rejected?

See `RECOMMENDATIONS.md`. In summary:

| Disposition | Changes |
|---|---|
| **Implement** | R-VS-1 (bind verified-state promotion to executed checks, not text); R-PERC-1 (per-session cumulative cost accounting) |
| **Defer** | Adaptive verification in Ordo (R-AD-1); risk classification in Praxis (R-AD-2); incremental architectural verification in Dokimos (R-DOK-2); context-reconstruction changes (R-CR-1). Each waits on a corpus that produces failures (R-EXP-4) |
| **Reject (for now)** | Making full Praxis, gate and verified state mandatory for every unit on reliability grounds (R-REJ-1), and shipping policy 1.0.0 as an Ordo feature (R-REJ-2) |

## 7. Limitations

1. **One chain per arm, 12 units, one fixture, one model and one effort setting.** Every interval captures task
   variance only.
2. **Ceiling effect.** The corpus was designed to produce failures and produced none. This is the dominant limitation,
   the third time in this series (VAC-001, ARCH-001, VAC-002).
3. **Partial blinding in Layer 3** (amendment A2). An Echelon arm can be inferred from `contracts/` and the Praxis
   files.
4. **The experimenters wrote the Ordo conflict nodes.** Ordo's conflict refusal is therefore an upper bound on what
   Ordo would infer by itself.
5. **The reviewers and the implementing agents are the same model family.** VAC-001 R-EXP-2 asked for another family;
   it was not available in this environment.
6. **Concurrency.** Six chains ran concurrently on one host, so wall times and host CPU are contended and exploratory.
