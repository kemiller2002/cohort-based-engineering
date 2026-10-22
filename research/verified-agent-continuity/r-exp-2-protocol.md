# R-EXP-2 protocol: long chains past compaction, K1 isolation, cross-family review (H2 and compaction)

- **Status:** preregistered design, 2026-10-22. **No trial has run.** The commit that adds this file is the
  preregistration. Any later change is an amendment logged at the end, with its date and what data, if any, existed
  when it was made.
- **Experiment ID:** VAC-004 (reserved). Its code and data will go in `../experiments/VAC-004/`, which does not exist
  yet.
- **Origin:** VAC-001 recommendation R-EXP-2 ([`engineering-recommendations.md`](engineering-recommendations.md) Q2,
  Q3) and input VAC-CBE-001-R4 (claim `INPUT-29db4a38cf86a56b`; record
  [`../../requirements/VAC-CBE-001.md`](../../requirements/VAC-CBE-001.md)). It also covers VAC-002 R-EXP-6
  (other-family reviewers).
- **Inherits:**
  - H2 and the metric definitions of VAC-001 ([`research-protocol.md`](research-protocol.md),
    [`metrics-schema.json`](metrics-schema.json));
  - from VAC-002 ([`../experiments/VAC-002/`](../experiments/VAC-002/)): the K1 harness, the sealing, the
    discrimination rule and the sample-size rule.
- **Planning numbers:** [`analysis/r-exp-plan.json`](analysis/r-exp-plan.json), from
  [`analysis/plan.py`](analysis/plan.py).

## 1. Why this experiment

VAC-001's continuity result holds within **8 units and 167k prompt tokens, with 0 compactions**, under K0: sub-agents
that shared the orchestrator's prompt-cache prefix. Three things were never tested:

- **H2 (lifetime-dependence).** No chain failed, so H2 is untested (`agent-longevity-analysis.md` §3.2).
- **Compaction.** It never happened, so compaction's effect on reliability is unmeasured, and so is the choice
  between compacting and restarting (§3.3; recommendations Q2, Q3).
- **K0.** The cache condition may have shaped the size of the A–B gap (§4).

The VAC-002 pilot (K1, 12 units) compacted once in each long-lived arm, at 149–156k prompt tokens (units 8–10), with
no harm. That is one compaction per chain and one chain per arm, which is descriptive only.

Layer 3 has so far used reviewers of the same model family as the implementers, which limits independence
(`hallucination-evaluation.md` §1).

## 2. Hypotheses and questions

| ID | Statement | Primary outcome | Primary contrast | Direction |
|---|---|---|---|---|
| **H2a** | A long-lived agent's failure rate rises with unit index (VAC-001 H2, arm B part) | CE per unit | (B: last third − first third) − (A: last third − first third) | > 0 |
| **H2b** | With verified state (D), it does not rise as much (VAC-001 H2, arm D part) | CE per unit | (D: last third − first third) − (B: last third − first third) | < 0 |
| **Q-C2** | Restarting on a context-pressure signal (BX) and letting the provider compact (B) give the same consequential-error rate | CE per unit, positions 9–24 | CE(BX) − CE(B) | two-sided |

**Why A is the control in H2a.** Every chain uses a fresh random task order (§4), so position is not confounded with
task. The codebase, however, grows with position in every arm. A fresh agent carries no history, so A's change across
the chain absorbs codebase growth. The difference isolates agent lifetime.

**VAC-001's refutation, kept:** H2 is refuted if D's failure rate rises as much as B's or more, or if B's does not
rise.

**Decision rules.** These are the same as VAC-002's H1 and H2 (`PREREGISTRATION.md` §2).

- **Minimum meaningful effect:** 10 percentage points.
- **Correction:** Holm across the 3 contrasts, family α = 0.05.

| Classification | Rule, per contrast |
|---|---|
| **Supported** | The Holm-adjusted test rejects 0 in the stated direction, and the point estimate meets the 10-point minimum |
| **Refuted** | The 95% interval excludes the 10-point minimum on the far side |
| **Inconclusive** | Anything else |

For Q-C2, "equivalent" is claimed only if the 90% interval lies within ±10 points (TOST).

**Compaction questions (secondary, preregistered, not in the Holm family):**

| ID | Question | Measure | Design |
|---|---|---|---|
| Q-C1 | Does failure rise after a compaction? | CE in the 4 units after each compaction vs the 4 units before, within B and D | Observational: compaction timing is endogenous. Reported as an estimate with interval, not as a causal effect |
| Q-C3 | Are established decisions kept across compaction? | DDR, and R-units (below) after vs before the first compaction | Observational |
| Q-C4 | What does compaction cost compared with restarting? | CCR of B vs BX; cost of the unit containing a compaction vs its neighbours | Randomized (B vs BX) and observational |
| Q-C5 | When does compaction occur? | Prompt tokens before and after each event; compactions per chain; unit index of the first | Descriptive |

**Out of scope, stated so no one reads it in:** *fixed-interval versus risk-based compaction.* No validated risk
signal exists: VAC-002's S8 fired on every unit. Recommendation Q3 therefore stays **not supported by evidence
yet**, whatever this experiment finds.

## 3. Arms

The common material, model, effort, tools, turn budget and directives are as in VAC-002 (`ARMS.md`, "Common to all
six arms").

**Cache condition K1 in every arm.** One isolated `claude -p` process per turn, with a fresh `CLAUDE_CONFIG_DIR` and
`HOME` per session. This uses VAC-002's launcher, `harness/agent-config.json`. Long-lived sessions continue with
`--resume`. No session shares a cache prefix with the orchestrator or with another arm.

**Compaction.** The provider's automatic compaction, with VAC-002's window (200,000 tokens; the setting under which
compaction was observed). It is never triggered manually.

| Arm | Lifetime | Controls |
|---|---|---|
| A | Fresh agent per unit; handoff is the earlier agents' reports | none |
| B | One session for the whole chain; compacts automatically | none |
| D | One session; compacts automatically | Ordo admission, in-loop `archcheck`, Praxis protocol, independent gate with one repair round, verified state (promotion bound to executed checks, VAC-002 R-VS-1) |
| **BX** | As B, but **restarted on context pressure**: a fresh session starts at the next unit boundary once the last request's prompt exceeds **140,000 tokens**. That is below the 149–156k range at which VAC-002 compacted, so BX restarts instead of compacting. The new session gets the repository and the reports, as A does | none |

**What BX tests.** BX is the operating model's restart rule (R1: restart on context pressure) made concrete. It adds
no verified state, so B vs BX varies only compaction versus restart.

If a BX session compacts anyway, that is recorded as a protocol deviation for the unit. The unit stays in the
analysis (intention to treat).

## 4. Corpus and chains

- **Fixture.** The ARCH-001 Lending application, as in VAC-002.
- **Tasks.** **32 new tasks, N01–N32**, each with a requirement, visible tests, a sealed hidden oracle, a cumulative
  reference, traps, an Ordo contract and a self-check, following VAC-002's construction rules.
- **Chain length.** Chains are **24 units** (N01–N24 drawn in random order). N25–N32 are used only under the
  extension rule in §5.
- **Composition.**
  - At least a third of the tasks are of R-EXP-1 kinds (K-PREM, K-DEC, K-UNDER, K-INV), so failures are possible.
  - If R-EXP-1 has qualified by the time N-tasks are frozen, its qualifying kinds are preferred.
  - **4 R-units** are included. These are K-DEC tasks whose correct behaviour depends on an owner decision made at
    least 8 positions earlier and not encoded in any test. Q-C3 needs them.
- **Conflict units.** These test every side of each conflict, after VAC-002 I7.
- **Order.** `random.Random(20261024)` gives one permutation per replicate chain. The constraint is that each R-unit
  and K-DEC unit follows its decision by at least 8 positions. Every arm uses the same order within a replicate.

## 5. Pilot and discrimination gate

1. **Pilot P.** One 24-unit chain per arm (96 units).
2. **Compaction check.** B and D must each compact at least once by unit 24.
   - If either does not, chains become 32 units (N01–N32) for every arm. This is recorded as an amendment before any
     confirmatory trial.
   - If no compaction occurs at 32 units, the compaction questions are reported as **not reachable** under this
     window. They are not tested by forcing compaction.
3. **Discrimination check.** This is VAC-002 `PROTOCOL.md` §7: at least two arms have a CE, and the arms' CE counts
   are not all equal.
   - If it fails, no confirmatory run starts. The corpus is hardened, re-sealed and piloted again, at most twice.
   - If it still fails, H2 is reported as **untestable on this corpus**.
4. The pilot is descriptive. Its chains are excluded from confirmatory tests.

## 6. Outcomes, metrics and review

**Schema.** Observations use **`cbe.vac.metrics/2`** ([`metrics-schema-2.json`](metrics-schema-2.json)). It is
`cbe.vac-001.metrics/1` unchanged, plus optional fields, including `compactionEvents`, `unitsSinceCompaction`,
`restart`, `cacheCondition` and `reviewerFamilies`. All VAC-001 metrics use their VAC-001 definitions.

**CE (consequential error),** per unit, means any of:

- not accepted at the final attempt;
- a regression of an earlier accepted task, from the cumulative oracle;
- an injected premise accepted;
- a silent conflict resolution;
- a silent extension confirmed by Layer 3.

UF, VAC-002's oracle-only failure, is a sensitivity analysis.

**Compaction instrumentation.** Each unit's turn record must carry, from the K1 stream:

- `compact_boundary` events;
- prompt tokens before and after each event;
- the restart trigger.

A unit whose compaction data are missing is reported as `unavailable`, never as 0. This is the measurement VAC-001
R-PRAXIS-1 asks Praxis to provide natively.

**Layer 3: reviewers from another model family.**

- **Sample.** Every decision of the 2 units after each compaction or restart, every decision of R-, K- and conflict
  units, and a seeded 25% of the rest (seed 20261024).
- **Reviewers.**
  - R1 and R2 are from **two model families other than the implementer's**, or one other family twice if only one
    is available. They must not be the implementer's family.
  - R3 adjudicates disagreements and may be from any family.
  - Families are recorded in `reviewerFamilies`. Model identifiers are recorded in the run data, as VAC-001 and
    VAC-002 record theirs.
- **Calibration, before use.** Each reviewer labels VAC-001's 202 adjudicated items (`../experiments/VAC-001/results/layer3-adjudicated.jsonl`)
  under the same blinding. A reviewer is used only if its κ against the adjudicated binary call (unsupported vs not)
  is ≥ 0.60. Calibration results are reported whatever they are.
- **Blinding.** The bundle carries commit history (VAC-001 §3.2). Echelon artefacts are removed and supplied as
  evidence (VAC-002 R-EXP-6). Agent lifetime and arm are stripped.

## 7. Sample size and power

**The binding test** is H2a and H2b: a difference between arms in the change from the first to the last third. That is
four independent proportions. Each third has 8 units per chain.

**Formula:** VAC-002 `PREREGISTRATION.md` §3, generalised to four proportions:
`n = (z₁₋α + z₁₋β)² · Σ p(1−p) / d² · (1 + (m − 1)ρ)`.

**Planning inputs:**

- p = 0.05 in A's two thirds and in B's first third, and 0.15 in B's last third (the 10-point minimum);
- α = 0.05 / 3, one-sided (Holm's worst case);
- power 0.80;
- ρ = 0.05;
- m = 8.

| Planning failure rate | Units per third per arm | Chains of 24 per arm |
|---|---|---|
| **5%** (VAC-002's floor) | **322** | **41** |
| 10% | — | 64 |
| 20% | — | 103 |

**Final number.** The chain count is recomputed by this rule from the pilot's failure proportions, floored at 0.05 and
capped at 0.5, with the pilot ICC if estimable. It is committed as an amendment before any confirmatory trial. Q-C2,
over 16 units per chain, needs fewer chains, so it does not bind.

**Analysis prerequisite (VAC-002 R-EXP-5).** The IRLS logistic model and the cluster bootstrap must first be
validated on simulated chains with known effects. Both pass and fail cases must be shown before any confirmatory
trial. The model is `CE ~ arm × position + task`, secondary.

## 8. Analysis plan

- **H2a and H2b.**
  - Risk differences of thirds, combined as stated in §2.
  - The interval is a cluster bootstrap over whole replicate chains: 10,000 resamples, seed 20261024.
  - Holm across H2a, H2b and Q-C2.
  - Secondary: the logistic model above, with the arm × position coefficient and its bootstrap interval.
  - The model is reported as an estimate, never read off a plot.
- **Q-C2.** A paired risk difference by block over positions 9–24. It gets the Holm-family test, and TOST for
  equivalence.
- **Q-C1 and Q-C3.** Within-chain before/after differences around each compaction, with a cluster bootstrap. These
  are labelled observational. A difference is not attributed to compaction unless it also appears in the randomized
  B vs BX contrast.
- **Cost.**
  - CCR per arm, and paired relative differences as in VAC-001 §2.2.
  - The K1 B − A contrast is compared with VAC-001's K0 −40.9%. This is the cache-condition question.
  - Tokens are never used as a cost proxy (VAC-001 R-EXP-3).
- **Survival.** Units to the first critical failure, with Kaplan–Meier per arm, censored at chain end.
- **Exclusions:** X1, X2, X4, X5 and X7, as in VAC-001 and VAC-002. They are listed, not imputed. A replicate with an
  excluded chain in any arm is dropped from paired contrasts.

## 9. Stopping rules and budget

| Phase | Ceiling | Rule |
|---|---|---|
| Reviewer calibration | $60 hard | — |
| Pilot P | **$110 hard** (estimate ≈ $69; margin for repairs and the 32-unit extension) | Stop file at $90. Units in flight finish |
| Confirmatory | **Requires an explicit spending ceiling from the repository owner before it starts.** This protocol does not authorize it | If the recomputed cost exceeds the ceiling, the run does not start |

**During the confirmatory run:**

- **Stop file** at 85% of the ceiling. Data are truncated to the last replicate every arm completed.
- **Per-arm alarm:** if an arm's mean cost per unit after 3 units exceeds 3× its estimate, that arm stops.
- **Runaway turn:** 45 minutes (X5).
- **No interim efficacy analysis.**

**Order with R-EXP-1.** The R-EXP-2 pilot may run independently. The confirmatory run is planned only after R-EXP-1's
qualification has a result, because the corpus composition (§4) depends on it.

## 10. Cost estimate (from VAC-001 and VAC-002 data)

**Per-unit cost, from VAC-002's measured K1 costs:**

| Arm | Basis | Estimate per unit, 24 units |
|---|---|---|
| A | No growth assumed (fresh agents) | $0.759 |
| B | Extrapolated linearly from VAC-002's per-position slope ($0.029 per position) to a 24-unit mean | $0.691 |
| D | Same method, slope $0.006 | $0.621 |
| BX | VAC-002 arm F (restarted every 4 units) as the upper bound, extrapolated the same way | $0.816 |

Linear extrapolation is conservative. Compaction shrinks the prompt, so growth should be sub-linear.

| Item | Estimate |
|---|---|
| Reviewer calibration (2 reviewers × 202 items at the same-family rate of $0.106; placeholder) | ≈ $43 |
| Pilot P (4 arms × 24 units) | ≈ $69 |
| Confirmatory model cost (41 chains × 24 units × 4 arms = 3,936 units) | ≈ **$2,840** |
| Layer 3 (≈ 35% of decisions; 4.7 decisions per unit; placeholder rate) | ≈ $700 |
| **Confirmatory total at the 5% planning rate** | ≈ **$3,600** (64 chains at 10%: ≈ $5,600) |

Other-family reviewer prices are not yet measured. That figure is a placeholder, and it is re-estimated after
calibration.

## Amendments

None.
