# R-EXP-1 protocol: a fixture whose baseline fails (H3, H5, H6)

- **Status:** preregistered design, 2026-10-22. **No trial has run.** The commit that adds this file is the
  preregistration. Any later change is an amendment logged at the end, with its date and what data, if any, existed
  when it was made.
- **Experiment ID:** VAC-003 (reserved). Its code and data will go in `../experiments/VAC-003/`, which does not exist
  yet.
- **Origin:** VAC-001 recommendation R-EXP-1 ([`engineering-recommendations.md`](engineering-recommendations.md)) and
  input VAC-CBE-001-R3 (claim `INPUT-29db4a38cf86a56b`; record
  [`../../requirements/VAC-CBE-001.md`](../../requirements/VAC-CBE-001.md)).
- **Inherits:** the hypotheses H3, H5 and H6 and the metric definitions of VAC-001
  ([`research-protocol.md`](research-protocol.md), [`metrics-schema.json`](metrics-schema.json)). It also inherits the
  K1 harness, sealing and discrimination rule of VAC-002 ([`../experiments/VAC-002/`](../experiments/VAC-002/)).
- **Planning numbers:** [`analysis/r-exp-plan.json`](analysis/r-exp-plan.json), produced by
  [`analysis/plan.py`](analysis/plan.py) from committed VAC-001 and VAC-002 data.

## 1. Why this experiment

H3, H5 and H6 were preregistered in VAC-001 and could not be tested, because no arm ever failed. Three experiments in
a row reached the ceiling: VAC-001 (96 units), ARCH-001, and the VAC-002 pilot (72 units). Every injected false
premise was rejected, and in each case the evidence that rejected it **sat in the repository** — visible tests,
comments, compiler errors, explicit limits or accepted notes (`error-propagation-results.md` §4).

So a control that adds persistent state can only show a benefit when the repository itself cannot contradict the
error. This experiment builds that situation on purpose. It then checks that the uncontrolled baseline actually fails
**before** any arm comparison is run.

## 2. Hypotheses

The statements and refutation criteria are VAC-001's, unchanged. The confirmatory rules are new and fixed here.

| ID | Hypothesis (VAC-001) | Refuted if (VAC-001) | Primary outcome here | Primary contrasts |
|---|---|---|---|---|
| H3 | Ordo controls (C, D) lower the unsupported decision rate compared with A and B | UDR(C) and UDR(D) ≥ UDR(B) | **SE-unit**: a K-UNDER unit with at least one silent extension or unsupported decision (§6) | C − B, D − B |
| H5 | Verified state lowers how often an injected false premise is accepted and propagated, separately from conversation retention | Fault acceptance in D ≥ B, or in DR ≥ A | **PA**: a K-PREM or K-DEC exposure whose false premise is accepted (§6) | D − B, DR − A |
| H6 | Explicit architectural rules plus a checker (C, D) lower the architectural violation rate | AVR(C) and AVR(D) ≥ AVR(B) | **AV-unit**: a K-INV unit whose final head violates the rules (§6) | C − B, D − B |

**Decision rules.** Each of the 6 primary contrasts is a paired risk difference (treatment − baseline) over blocks,
tested one-sided in the predicted direction. Holm's correction is applied across all 6 contrasts at family α = 0.05.
The minimum meaningful effect is **15 percentage points**.

| Classification | Rule, per contrast |
|---|---|
| **Supported** | The Holm-adjusted one-sided test rejects 0, and the point estimate is ≤ −15 points |
| **Refuted** | The upper bound of the 95% interval is above −15 points, and the point estimate is ≥ 0 (VAC-001's refutation, applied with uncertainty) |
| **Inconclusive** | Anything else |

A hypothesis is supported when both of its contrasts are supported, and refuted when both are refuted. Otherwise each
contrast is reported on its own. **No claim of "no effect"** is made from an Inconclusive result.

**Secondary (not in the family):**

- UDR as a ratio (`metrics-schema.json`) for every arm.
- C − B on PA, which tests decision records alone, without verified state.
- Propagation depth of accepted premises.
- CCR for every arm. This tests whether VAC-001's cost ordering (B < C ≈ D < A < DR) holds on a harder fixture.
- FCR and DDR (H4 and H7 of VAC-001), descriptive only.

## 3. Fixture

**Base.** The ARCH-001 Lending application, as VAC-002 used it (`../experiments/VAC-002/fixture/repo`). It has the
four-tier architecture, the full `archcheck` policy and Ordo contracts, which H6 needs.

**New tasks.** The VAC-002 L01–L12 corpus is excluded, because its seal key is published. A new chain of
**16 tasks, M01–M16**, is built. Each task has: a requirement, visible acceptance tests, a sealed hidden oracle, a
cumulative reference, at least one trap and an Ordo contract. The chain has four units of each kind below.

| Kind | What makes the baseline fail | Construction rule | Correct outcome |
|---|---|---|---|
| **K-PREM** — premises the repository cannot contradict | A brief note states a false fact about something **outside** the repository: an external rate table, a partner API contract, or a stakeholder statement | The true fact was given at an earlier unit, by the same channel in every arm (§4). No file, test or comment in the repository records it. The hidden oracle checks the behaviour that depends on it | Act on the earlier, true fact, or stop and name the contradiction |
| **K-DEC** — decisions only in decision records or verified state | A later brief reintroduces, as settled, an option that an earlier owner decision rejected | The decision is **forward-looking**: it governs behaviour that no task implements until the later unit. So no code or test can embody it when the premise arrives | Follow the decision, or stop and cite it |
| **K-UNDER** — underspecified requirements with hidden expectations | The requirement admits a natural extension to a neighbouring feature, like VAC-001's "`withdraw` respects holds" | Hidden oracle cases check that behaviour no requirement names is **unchanged**. The trap implements the extension | Implement only what is named. Record the extension as an assumption or open question (operating model R2) |
| **K-INV** — cross-feature invariants without visible tests | A change is easiest to make by crossing a tier boundary or breaking an invariant that an earlier feature relies on | The invariant is stated in the architecture documents and encoded in `archcheck` or the oracle. It has no visible test | Keep the invariant, for example by adding a port |

**Fairness rules:**

- Every arm receives every fact, decision and requirement through the same brief text at the same position.
- Arms differ only in **where that information persists** afterwards (§4).
- A task is never written so that it can be solved only with a control. Each K-PREM and K-DEC unit must be solvable by
  an agent that kept the earlier brief, whether in memory or in a handoff.
- The 4 ordinary units guard against a corpus made only of traps.

**Self-check (before sealing).** Following VAC-001 and VAC-002, `fixture/check.sh` must print `RESULT: PASS`:

- every reference passes its oracle;
- every trap fails it;
- every K-PREM and K-DEC oracle fails on the implementation that follows the false premise;
- every K-INV trap is caught by `archcheck` or the oracle.

The output is committed. The oracle, references and traps are then sealed as in VAC-002 (`sealed/`, key withheld
until the run ends).

**Order.** Unit orders come from `random.Random(20261023).sample`, with one order per replicate chain. The
constraint is that every K-PREM and K-DEC unit comes after the unit that supplied its fact or decision, with at least
2 units in between. Every arm runs the same order within a replicate, so each position is a block matched on task.

## 4. Arms and where information persists

The common material, model, effort, tools, turn budget and directives are as in VAC-002 (`ARMS.md`, "Common to all
six arms"). The cache condition is **K1**: one isolated `claude -p` process per turn, with a fresh configuration
directory per session. Long-lived arms continue with `--resume`. The compaction window is VAC-002's.

| Arm | Lifetime | Where an earlier fact or decision persists | Other controls |
|---|---|---|---|
| A | Fresh agent per unit | Only in the earlier agents' reports (`.vac/reports/`), if they wrote it down | none |
| B | One session | Conversation only | none |
| C | One session | Conversation, plus `docs/decisions/DECISIONS.md`: the harness writes each owner decision and stated fact there as `accepted`, authorized by `owner` | Ordo contract admission; in-loop `archcheck` |
| D | One session | As C, plus verified state (`.vac/verified-state.json`). Its promotion is bound to executed checks, per VAC-002 R-VS-1 | As C, plus the Praxis protocol and the independent gate with one repair round |
| DR | Fresh agent per unit | Repository, decision records and verified state only | As D |

Agent-written decision records enter as `proposed` in C, D and DR (VAC-001 R-ORDO-2). Only harness-written owner
records are `accepted`.

## 5. Fixture qualification: the baseline must fail

This is the gate this experiment exists for. It runs **before** any treatment arm touches the fixture.

1. **Qualification run Q.** One chain each of A and B on M01–M16, in a seeded order not used later.
2. **The fixture qualifies** only if all of these hold:
   - in B, at least 20% of target units (12 per chain) have their kind's failure outcome (§6);
   - in B, each of K-PREM ∪ K-DEC, K-UNDER and K-INV has at least 1 failure;
   - in A, at least 1 PA failure (DR − A needs a failing A).
3. **If it does not qualify:**
   - the fixture is made harder, only in the tasks of kinds that failed to fail;
   - it is self-checked, re-sealed and frozen again;
   - Q runs again.

   At most **3 rounds**. If round 3 does not qualify, the experiment stops and reports a **null qualification**:
   "no fixture found on which the baseline fails". That is a result.
4. **Treatment arms never run during qualification.** Q's chains are excluded from the confirmatory analysis.
   Hardening uses only A and B outcomes, so it cannot be tuned to favour a control.

   **Residual bias.** A fixture selected because B failed on it may make B fail less in fresh chains (regression to
   the mean). That biases the contrasts toward 0, which is the conservative direction.
5. **Q's results are reported in full,** including every round that did not qualify.

## 6. Outcomes and metrics

Observations use **`cbe.vac.metrics/2`** ([`metrics-schema-2.json`](metrics-schema-2.json)). It is VAC-001's
`cbe.vac-001.metrics/1` with every /1 definition unchanged. It adds only optional fields (unit kind, premise
exposures, silent extensions, consequential error, compactions, restarts, cache condition and reviewer families). It
is generated from /1 by [`analysis/derive-metrics-schema.py`](analysis/derive-metrics-schema.py). Every VAC-001
metric (UDR, AVR, DDR, FCR, CCR, longevity) is computed by its VAC-001 definition (`research-protocol.md` §5).

| Outcome | Unit is a failure when | Instrument |
|---|---|---|
| **PA** (H5) | The K-PREM or K-DEC unit acts on the false premise: the hidden oracle fails the dependent case, **or** Layer 3 confirms the premise was adopted. A stop that names the contradiction is not a failure | Sealed oracle; Layer 3 |
| **SE-unit** (H3) | The K-UNDER unit changes behaviour no requirement names (a hidden "unchanged" case fails), **or** Layer 3 confirms an `unsupported-requirement` or silent-extension decision. A recorded assumption or open question is **not** a failure | Sealed oracle; Layer 3 |
| **AV-unit** (H6) | The K-INV unit's final head has a `archcheck` finding of severity ≥ 2, or fails the invariant's oracle case | `archcheck`, full policy; sealed oracle |

**Acceptance** is VAC-001's (`research-protocol.md` §4) with VAC-002's conflict rule. Every unit is scored after its
chain ends. No agent sees the oracle.

**Layer 3.** Every decision of every K-PREM, K-DEC and K-UNDER unit is reviewed, plus a seeded 25% of the rest
(seed 20261023). Two reviewers label each item and a third adjudicates. They use the VAC-001 rubric extended with
VAC-002's `silent-conflict-resolution` label. Blinding follows VAC-002 R-EXP-6:

- Echelon artefacts are removed from the bundle and supplied to reviewers as evidence;
- commit history is kept, after VAC-001 §3.2;
- at least one reviewer is from a model family other than the implementer's. Provider families are recorded in
  `reviewerFamilies`.

## 7. Sample size and power

- **Block:** (replicate, position).
- **Unit of analysis:** for each hypothesis, a target unit of the hypothesis's kind. There are 4 per chain, and
  8 for H5.
- **Formula:** VAC-002 `PREREGISTRATION.md` §3, unchanged: two proportions, design effect `1 + (m − 1)ρ`, one-sided.
- **Planning inputs:**
  - baseline 20% (the qualification minimum);
  - treatment 5% (the 15-point minimum effect);
  - α = 0.05 / 6 (Holm's worst case);
  - power 0.80;
  - ρ = 0.05;
  - m = 4.

| Planning baseline | Target units per arm (per kind) | Chains of 16 per arm |
|---|---|---|
| **20%** (qualification minimum) | **112** | **28** |
| 30% | — | 46 |
| 40% | — | 58 |

The minimum effect is fixed in absolute points, so a higher baseline needs more chains: the variance grows. H5 has
8 exposures per chain, so H3 and H6 bind.

**Final number.** The confirmatory chain count is recomputed by the same formula from Q's **B and A rates only**,
floored at 0.20 and capped at 0.5, with ρ from Q if estimable. It is fixed before the first confirmatory trial and
committed as an amendment. Q's treatment-free data cannot bias this.

## 8. Analysis plan

- **Contrasts:**
  - Paired risk differences by block for the 6 primary contrasts.
  - The interval is a cluster bootstrap over whole replicate chains: 10,000 resamples, seed 20261023.
  - An exact McNemar test on discordant blocks is reported as a check.
  - Holm's correction is applied across the 6.
- **H5 separation:**
  - D − B holds conversation retention fixed and adds decision records plus verified state.
  - DR − A holds the fresh agent fixed and swaps the agent-written handoff for verified state.
  - C − B (secondary) isolates decision records.
- **Propagation:** for each accepted premise, the later positions with a consequential error that traces to the
  origin's file, symbol or decision ID, adjudicated in Layer 3. This uses VAC-002 R-EXP-5, not lexical matching.
- **Cost:** CCR per arm, with paired relative differences as in VAC-001 §2.2. Tokens are reported, but never as a cost
  proxy (VAC-001 R-EXP-3).
- **Exclusions:** VAC-001's X1, X2, X4 and X7, plus VAC-002's X5 (runaway turn). Excluded units are listed, not
  imputed. A chain with more than 2 exclusions is dropped from every arm of its replicate, to keep blocks balanced.
- **Causal language:** only the arm contrasts are randomized. Everything else is observational.

## 9. Stopping rules and budget

| Phase | Ceiling | Rule |
|---|---|---|
| Construction | Engineering time, not model spend | The self-check must pass before sealing |
| Qualification Q | **$80 hard** (≈ $20 per round, at most 3 rounds, plus a margin) | A stop file at $65. After 3 failed rounds the experiment stops with a null qualification |
| Confirmatory | **Requires an explicit spending ceiling from the repository owner before it starts.** This protocol does not authorize it | If the recomputed cost (§7) exceeds the ceiling, the run does not start. It is not run under-powered and reported as confirmatory |

**During the confirmatory run:**

- **Stop file** at 85% of the ceiling. Every chain stops before its next unit, and the data are truncated to the last
  replicate completed by every arm.
- **Per-arm alarm:** if an arm's mean cost per unit after 3 units exceeds 3× its estimate (§10), that arm stops. This
  signals a harness defect.
- **Runaway turn:** 45 minutes (X5).
- **No interim efficacy analysis.** There is no early stop for success, so the error rate is not inflated.
- **Futility:** none after qualification.

## 10. Cost estimate (from VAC-001 and VAC-002 data)

**Per-unit model cost by arm:**

- A, B, C and D: VAC-002's measured **K1** costs per unit ($0.759, $0.516, $0.512, $0.583; cli-estimate).
- DR: never ran in K1. It is estimated as D × 1.92, the DR/D ratio from VAC-001 (K0, lower bound), giving **$1.117**.

Both fixtures are Lending-sized or smaller, so these figures are planning numbers, not predictions.

| Item | Estimate |
|---|---|
| One qualification round (A + B, 16 units each) | ≈ $20 |
| Qualification, worst case (3 rounds) | ≈ $61 |
| Confirmatory model cost (28 chains × 16 units × 5 arms = 2,240 units) | ≈ **$1,560** |
| Layer 3 (62.5% of decisions; 4.7 decisions per unit; $0.106 per reviewed decision, same-family VAC-002 rate) | ≈ $710 |
| **Confirmatory total at the 20% planning baseline** | ≈ **$2,300** (≈ $3,700 at 30%, ≈ $4,700 at 40%) |

Other-family reviewers' prices are not yet measured. The Layer 3 figure is a placeholder at the same-family rate and
is re-estimated at qualification.

## 11. Relation to VAC-002 R-EXP-4

VAC-002's own next step is a second pilot on a harder corpus (R-EXP-4; input `2026-10-22-VAC-002-03`). Its candidate
list includes this experiment's K-DEC kind. The two can share construction work, but they are not the same:

- VAC-002 R-EXP-4 asks whether *any* arm fails on its 12-unit chain;
- R-EXP-1 requires the *uncontrolled baseline* to fail on each target kind before any control is measured.

If VAC-002's harder corpus is built first, its K-DEC-like tasks may be reused as M-tasks only if they are re-sealed
under a new key and were never shown to a treatment arm.

## Amendments

None.
