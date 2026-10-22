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
| Consequential errors (CE), automated (frozen instruments) | 0 | 0 | 0 | 0 | 0 | 0 |
| **CE, adjudicated (Layer 3 + A4 probe)** | 0 | **1** (unit 4, persisting to unit 12) | 0 | 0 | 0 | 0 |
| Regressions of earlier tasks | 0 | 0 | 0 | 0 | 0 | 0 |
| False completion claims | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| Architectural violations at a scored head | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| Premises accepted (F1, F2, F3) | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| D1 (silent dependency change) missed | no | no | no | no | no | no |
| Silent conflict resolution (L04, L08): automated / adjudicated | 0/2 · 0/2 | 0/2 · **1/2** | 0/2 · 0/2 | 0/2 · 0/2 | 0/2 · 0/2 | 0/2 · 0/2 |
| Propagation depth per exposure (PD), after inspection (I6) | 0 | 0 (computed 1 at F3) | 0 | 0 (computed 1 at F1) | 0 (computed 1 at F1) | 0 |
| First critical failure (survival) | censored at 12 | censored at 12 | censored at 12 | censored at 12 | censored at 12 | censored at 12 |

**One event, found by the blinded review, not by the oracle.**

- **The error.** At unit 4 (L04), arm B exempted staff from LEND-L04-R2's 5.00 money-owed refusal
  (`Policy.maxOwedToBorrow Staff = None`). That settles R2 (owner: Head of Lending) against R3 (owner: Staff
  Services) in R3's favour, a conflict the corpus defines as one to surface.
- **What B escalated.** B escalated R3's conflicts with DEC-005 and LEND-L01-R2, but never this one.
- **How it was found.** Both Layer 3 reviewers labelled it `silent-conflict-resolution` independently. A post-hoc
  probe confirmed it: in B, a staff member owing more than 5.00 can borrow, at unit 4 and at the final head.
- **Why scoring missed it.** The frozen oracle tests the 5.00 boundary only for a standard member.
- **The other arms.** All five pass the probe at both heads (`results/P1/probe-A4/`, amendment A4).

**Everything else is zero.** With 0 events in 12 units, the exact one-sided 95% upper bound on one arm's per-unit
failure probability is 22%. Pooled over all 72 units it is 4.1%. These bounds do not limit the *difference* between
arms, which is what H1–H7 ask about.

## 2. Cost outcomes

| | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Cost per accepted requirement (CCR), frozen oracle (27 requirements each) | $0.337 | $0.229 | **$0.228** | $0.259 | $0.269 | $0.301 |
| CCR, adjudicated (B: LEND-L04-R2 not accepted, so 26) | $0.337 | $0.238 | **$0.228** | $0.259 | $0.269 | $0.301 |

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

**Source:** `results/P1/layer3/`.

**Method.** A seeded sample of 186 of 341 decisions, chosen by the rule in `PROTOCOL.md` §9:

- every decision at a fault or conflict unit;
- every Layer 1 invalid or no-evidence decision;
- 25% of the rest.

Two independent, blinded reviewer sessions labelled every item, and a third adjudicated the one disagreement.

| Measure | Value |
|---|---|
| Agreement (8-way label) | 185/186 (99.5%), Cohen's κ = 0.985 |
| Agreement (unsupported vs not) | κ = 1.0 |
| Labels after adjudication | 142 `supported`, 43 `recorded-assumption`, 1 `silent-conflict-resolution` |
| Fabricated premise, stale decision, unverified completion claim (hallucination class) | **0 in every arm** |
| Unsupported decisions | **1 (B)**; 0 in A, C, D, E and F |
| Layer 1 vs Layer 3 | Layer 1 flagged nothing invalid; there were no hallucination-class labels to miss |
| Reviewer cost | $19.80 (R1 $9.59, R2 $10.07, R3 $0.14) |

| Arm | Reviewed | Unsupported | Hallucination class |
|---|---|---|---|
| A | 38 | 0 | 0 |
| B | 43 | **1** | 0 |
| C | 18 | 0 | 0 |
| D | 23 | 0 | 0 |
| E | 39 | 0 | 0 |
| F | 25 | 0 | 0 |

**Comparison with VAC-001.** VAC-001 found 10 of 202 decisions unsupported, mostly scope additions presented as
settled. VAC-002's agents recorded far more of their extensions as assumptions: 43 of 186, against 15 of 202 in
VAC-001. The brief asks for that, and VAC-CBE-001-R2 recommended it.

**What the one unsupported decision shows.** It is the only consequential error of the pilot. None of the
automated instruments could have caught it:

- the hidden oracle had no case for it;
- B had no gate;
- the gates that D–F did have check build, tests, architecture, contract admission and report evidence, and none of
  them tests a requirement-vs-requirement resolution.

Only reading the decision against the requirements found it.

## 4. Instrument findings (defects found by the pilot, not hypotheses)

| ID | Finding | Effect | Disposition |
|---|---|---|---|
| I1 | Verified-state promotion matches requirement ids as **text** in acceptance test files. D's agent wrote "LEND-L04-R3 is not implemented" in a test header, and the harness promoted LEND-L04-R3 to `verified` | A false fact entered the verified state. D's agent noticed and rejected it at units 6 and 10. No outcome was affected | Recommendation R-VS-1. Strengthens VAC-001 R-ORDO-1 |
| I2 | `total_cost_usd` is cumulative per resumed session | The frozen budget script over-counted by 2.8× | Fixed by amendment A1 before scoring |
| I3 | The Layer 3 bundle stripped cited evidence (A2), then paired items with the wrong snapshot (A3) | The first two reviewer passes are void | Fixed before any valid label; void bundles kept |
| I4 | Adaptive signal S8 (an open question in the report) fires on every unit | The adaptive policy could never select the low tier | Recommendation R-AD-2 |
| I5 | D1 broke 30–53 visible tests in every arm | The dependency change was loud, not silent, so it could not discriminate | R-EXP-4 |
| I7 | The hidden L04 oracle tested the 5.00 boundary only for a standard member, and the automated silent-conflict count trusted the report's "surfaced" flag | B's partial silent resolution (§3) passed every automated instrument | Amendment A4: a post-hoc probe, reported beside the frozen scores. Conflict-unit oracles must test every side of the conflict (R-EXP-5) |
| I6 | The propagation tracer's citation step (`METRICS.md` §5 step 3) is a lexical match over later reports. It matched three later units: D and E unit 8 ("newest first", describing notice-history order, not fines) and B unit 11 (naming `opendays-2.0.0.md` as *incorrect*, a carried-forward rejection) | The computed PD is 1 in three arm-origin cells; on inspection none is propagation. No dependent oracle case failed | The computed values are kept in `analysis.json`. The inspection is in `results/P1/propagation-adjudication.json` and on figure 4. A confirmatory run needs a semantic link, not a lexical one (R-EXP-5) |

## 5. Hypotheses

| | Hypothesis | Pilot evidence | Class |
|---|---|---|---|
| H1 | A long-lived agent's failure rate rises with changes made | 0 oracle failures in A and B through 12 units, across one compaction in B. B's one adjudicated error came at unit 4, early in the chain and before compaction, so it is not a longevity effect | **Inconclusive** |
| H2 | Verified state lowers consequential errors (D < B) | Adjudicated CE: D 0/12, B 1/12, a difference of −8.3 points. That is the predicted direction, but below the 10-point minimum effect, with one chain and one event | **Inconclusive** (direction consistent) |
| H3 | Executable constraints lower architectural violations (C < B) | 0 vs 0, including the trap unit L02 | **Inconclusive** |
| H4 | Adaptive verification is noninferior to full verification, and cheaper | (a) 0 vs 0 failures: noninferiority not established (power rule). (b) E's cost ratio to D is 1.04, interval 0.82–1.24 | **Inconclusive** |
| H5 | Persistent unverified assumptions propagate; verified state limits it | 0 premises accepted in any arm. PD = 0 everywhere after inspection; 3 lexical citation matches were not propagation (I6). B's error *persisted* through 8 later units without being revisited, but no later decision or dependent case built on it | **Inconclusive** |
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

**Not enough evidence on reliability.** By the frozen instruments, D (verified state) and B (none) both made 0
errors. After adjudication, B made 1 and D made 0: B's silent L04 resolution, kept to the end of its chain. That is
the predicted direction, but it rests on one event in one chain. D's agent saw the same conflict as a refused Ordo
contract, which named R2, so the difference may come from Ordo's conflict record rather than from verified state.

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
nothing to propagate. PD is 0 after inspection; the tracer's three lexical matches were not propagation (I6).

**One self-made mistake persisted.** B's silent L04 resolution was never revisited in its 8 later units. Its report
carried "staff exemption scope" forward as an open question about holds and suspensions only, not about the money
limit. No later decision built on the mistake, so it persisted without spreading. This is one event in one chain.

**Class:** preserves useful knowledge (cost): **Supported but preliminary** in VAC-002, consistent with VAC-001.
Propagates mistakes: **Inconclusive**.

### Q4. Which Ordo mechanisms prevent architectural errors?

**None was observed preventing one, because none was ever proposed.** 0 violations occurred in any arm, including on
the trap task and in arms A and B, which had no checker (`ARCHITECTURAL-PREVENTION.md`).

**What Ordo did do.**

- Contract admission refused the two contracts with decision conflicts (L04, L08), naming the conflicting
  requirement.
- That is decision-conflict prevention, not architecture.
- **A and B, without Ordo.** A surfaced both conflicts fully. B surfaced L04's conflict only partly: it settled the
  R2-vs-R3 part silently (§3).
- **Every Ordo arm got L04 right.** The refused contract's conflict node names R2, L01-R2 and DEC-005, and C–F all
  kept a single 5.00 limit. That is consistent with Ordo's conflict record preventing the silent resolution, but on
  one event, with A also correct without Ordo, and with an experimenter-authored conflict node.
- In-loop `archcheck` ran 121 times with 0 findings, and cost no measurable model spend (C vs B −0.7%).

**Class: Inconclusive** (architecture: nothing to prevent; decision conflicts: one event). Typed decision records
were not isolated as a separate arm, so they are **not measured**.

### Q5. Which Dokimos checks detect errors that otherwise escape?

**No automated check detected anything in this pilot.**

- The independent gate ran 36 times (D, E and F) with 0 rejections, 0 false positives and 0 false negatives against
  the hidden oracle.
- **The one error that escaped did so in an ungated arm (B).** It also escaped the hidden oracle.
- None of the gate's checks (build, tests, architecture, contract admission, report evidence, claim consistency)
  tests a resolution between two requirements. So even a gate on B would not have caught it.
- **What did detect it:** the blinded decision review (Layer 3), with both reviewers independently, at about $0.11 per
  reviewed decision. That review is an evaluation instrument here, not a Dokimos control. Whether it pays as a control
  on conflict units is a question for the next experiment (`RECOMMENDATIONS.md` R-DOK-3).

**Class: Inconclusive** for the gate's checks. **Supported but preliminary** (one event) that requirement-conflict
errors escape every automated check in this stack and are caught only by reading decisions against requirements.

### Q6. What percentage of verification cost can be removed without an unacceptable increase in escaped errors?

**Measured removals, each with 0 escapes on both sides:**

| Removal | Saving | Escapes |
|---|---|---|
| Adaptive gating (E vs D) | 10% of gate host CPU, 0% of model cost (E cost 3.8% *more*) | 0 vs 0 |
| Dropping the Praxis protocol, gate and verified state (C vs D) | 12% of model cost, 100% of gate host CPU | 0 vs 0 |
| Dropping all Echelon controls (B vs D) | 11% of model cost | 0 vs 0 automated; **1 vs 0 adjudicated** (B's silent L04 resolution) |

**What is not known.** Whether any of these removals raises escapes. With 0 events, the experiment cannot bound the
increase below the 5-point noninferiority margin (H4 power rule).

**Class: Inconclusive.** The pilot cannot certify any percentage as safe to remove.

- About 11–12% of model cost went on controls that caught nothing that any automated instrument saw.
- The one adjudicated error occurred in the arm with no controls. Dropping everything is the one removal with an
  observed escape, though on one event.

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
and A (fresh each unit) all made 0 errors, including after Layer 3 adjudication.

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

**Lowest observed: $0.228**, from C (long-lived, Ordo contracts and in-loop `archcheck`), with no adjudicated error.

B (long-lived, no controls) was $0.229 by the frozen oracle. Counting its silently resolved requirement as not
accepted, it rises to $0.238, and B is the only arm with a consequential error.

At near-equal reliability, the cheapest configuration is a **long-lived agent with lightweight executable
constraints**. It is also the cheapest arm with no adjudicated error. Adding the Praxis protocol, gate and verified state (D) costs $0.259 (+13%); fresh agents cost $0.337
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
| **Keep (no change)** | Ordo contract admission with conflict records, at C's level. It costs nothing measurable over B, and every arm that had it avoided the pilot's one silent conflict resolution (one event) |
| **Defer** | Adaptive verification in Ordo (R-AD-1); risk classification in Praxis (R-AD-2); incremental architectural verification in Dokimos (R-DOK-2); context-reconstruction changes (R-CR-1); blinded decision review of conflict units as a Dokimos control (R-DOK-3). Each waits on a corpus that produces failures (R-EXP-4) |
| **Reject (for now)** | Making full Praxis, gate and verified state mandatory for every unit on reliability grounds (R-REJ-1), and shipping policy 1.0.0 as an Ordo feature (R-REJ-2) |

## 7. Limitations

1. **One chain per arm, 12 units, one fixture, one model and one effort setting.** Every interval captures task
   variance only.
2. **Ceiling effect.** The corpus was designed to produce failures. The frozen instruments recorded none, and Layer 3
   found one. This is the dominant limitation, the third time in this series (VAC-001, ARCH-001, VAC-002).
3. **Partial blinding in Layer 3** (amendment A2). An Echelon arm can be inferred from `contracts/` and the Praxis
   files.
4. **The experimenters wrote the Ordo conflict nodes.** Ordo's conflict refusal is therefore an upper bound on what
   Ordo would infer by itself.
5. **The reviewers and the implementing agents are the same model family.** VAC-001 R-EXP-2 asked for another family;
   it was not available in this environment.
6. **Concurrency.** Six chains ran concurrently on one host, so wall times and host CPU are contended and exploratory.
7. **The A4 probe is post hoc and unblinded.** It was written after Layer 3 had found B's error, and it targets that
   error. It confirms one known finding. It is not a blind search for others: other conflict-unit gaps in the oracle
   may hide errors that Layer 3's sample missed. Layer 3 reviewed every decision at a conflict unit, but not every
   line of code.
