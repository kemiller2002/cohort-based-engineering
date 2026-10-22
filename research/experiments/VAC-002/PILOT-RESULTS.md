# VAC-002 pilot P1: results (descriptive)

**What ran.** 6 arms, each working one chain of the 12 pilot units (L01–L12), concurrently, from 15:47 to 17:09 UTC on
2026-10-22. The run used the frozen protocol (commit `0011132`), with amendments A1 (cost measurement) and A2 (Layer 3
bundle).

**Scope.** Every number below comes from `results/P1/`:

| File | Contents |
|---|---|
| `analysis.json` | Per-arm and per-unit metrics |
| `contrasts.json` | Exploratory paired cost contrasts |
| `phase-g.json` | Architectural prevention |
| `score-*.json` | Hidden-oracle observations |
| `turn-*.json`, `gate-*.json`, `policy-*.json`, `verified-state-*.json` | Run records |
| `layer3/` | Blinded decision review |

**Status.** The pilot is descriptive. With one chain per arm, **no hypothesis is tested**, and no interval below is a
test.

## 1. Headline

**Every arm reached the ceiling again.**

- **Units.** All 72 units were accepted at first pass by the hidden oracle, and none needed a repair.
- **Oracle cases.** 63 cumulative cases per arm at unit 12, all passing.
- **Errors.** 0 false completions, 0 regressions, 0 architecture violations.
- **Conflicts.** Every conflict was surfaced: 12/12 conflict units.
- **Premises.** Every injected premise was rejected and D1 was detected: 24/24 exposures.

By the preregistered discrimination check (`PROTOCOL.md` §7), **the corpus does not discriminate between arms**.
Reliability hypotheses H1–H5 and H7(a) cannot be tested on it at any sample size: the expected failure count is
about 0.

**Cost did differ.** The cost picture repeats VAC-001 and ARCH-001:

- continuity is cheaper than fresh agents (B vs A −32%);
- Echelon's full controls cost more than continuity alone (D vs B +13%);
- the adaptive policy saved nothing (E vs D +4%);
- restarting every 4 units cost more than continuity (F vs D +16%).

## 2. Per arm

| | A fresh | B long-lived | C + Ordo | D full | E adaptive | F restarted |
|---|---|---|---|---|---|---|
| Units accepted / first pass | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 |
| Consequential errors | 0 | 0 | 0 | 0 | 0 | 0 |
| Conflicts surfaced (L04, L08) | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Premises rejected / D1 detected | 3/3 · yes | 3/3 · yes | 3/3 · yes | 3/3 · yes | 3/3 · yes | 3/3 · yes |
| Agent cost (cli-estimate, A1) | $9.10 | $6.19 | $6.15 | $6.99 | $7.26 | $8.13 |
| Cost per unit | $0.758 | $0.516 | $0.512 | $0.583 | $0.605 | $0.677 |
| **Cost per accepted requirement** (27 requirements) | **$0.337** | **$0.229** | **$0.228** | **$0.259** | **$0.269** | **$0.301** |
| Output tokens | 155,346 | 127,324 | 122,462 | 138,114 | 146,792 | 149,853 |
| Cache-read tokens | 5.76 M | 8.57 M | 8.41 M | 9.77 M | 10.14 M | 11.40 M |
| Cache-write tokens | 604,896 | 222,346 | 225,798 | 266,892 | 265,036 | 355,822 |
| Tool calls | 178 | 105 | 103 | 107 | 123 | 147 |
| Agent wall time (concurrent; exploratory) | 53 min | 43 min | 50 min | 49 min | 51 min | 56 min |
| Gate runs / rejections / host CPU | — | — | — | 12 / 0 / 1,313 s | 12 / 0 / 1,185 s | 12 / 0 / 1,070 s |
| Compactions | 0 (fresh) | 1 (unit 10) | 1 (unit 10) | 1 (unit 8) | 1 (unit 9) | 0 (restarts at 5, 9) |
| Peak prompt before compaction | ≈ 81k | 150k | 153k | 149k | 156k | 144k |
| X4 contamination | 0 | 0 | 0 | 0 | 0 | 0 (2 detector false positives) |

**The 27 requirements** are the requirement ids of L01–L12 minus the two conflicting ones (LEND-L04-R3,
LEND-L08-R2), whose correct disposition is "surfaced, not implemented".

### 2.1 Exploratory cost contrasts

Source: `contrasts.json`. These are relative differences in total agent cost over the 12 positions. The interval is a
percentile bootstrap over positions, 10,000 resamples, seed 20261022. **It captures task-to-task variance only,
because there is one chain per arm.**

| Contrast | Point | 95% interval (exploratory) | VAC-001 / ARCH-001 comparison |
|---|---|---|---|
| B vs A (continuity) | **−32.0%** | −41.8% to −22.9% | VAC-001 −40.9% (K0, Ledger) |
| C vs B (Ordo contracts plus in-loop `archcheck`) | −0.7% | −12.1% to +10.4% | VAC-001 C vs B +14.1%; ARCH-001 D/C +4% |
| D vs B (full controls) | +12.9% | −3.7% to +34.1% | VAC-001 +16.8% |
| E vs B (adaptive) | +17.2% | +0.2% to +37.3% | — |
| **E vs D (adaptive vs full)** | **+3.8%** | −17.6% to +24.1% | — |
| F vs D (restart every 4 units) | +16.2% | −8.9% to +39.5% | VAC-001 DR (restart every unit) vs D +86% |
| F vs A | −10.7% | −28.7% to +8.5% | VAC-001 DR vs A +50.6% |
| D vs A | −23.2% | −34.1% to −9.1% | VAC-001 −31.0% |

### 2.2 Where the cost went

Continuity's saving is again in cache economics, not in tokens:

- **Cache writes.** A wrote 2.7× more cache than B (605k vs 222k tokens) and made 1.7× more tool calls.
- **Output and reads.** A's output was only 22% higher than B's. A *read* fewer cached tokens (5.8M vs 8.6M), because
  each fresh session starts small.

The Echelon controls (C–F) added no measurable cost at the C level:

- In-loop `archcheck` (about 2.5 runs per unit, 20–30 s each) and Ordo admission (2 runs per unit) cost C nothing
  detectable over B.
- The Praxis protocol and the verified state (D) cost about +13%, mostly in cache reads. D's context carries the Praxis
  scaffold, the `CLAUDE.md` contract and the protocol commands.
- **F's restarts** (units 5 and 9) cost **$1.08 and $0.99**, against D's $0.74 and $0.56 for the same units. That is
  about +$0.38 per restart.

## 3. Adaptive policy (Arm E)

Source: `policy-*.json`; full account in `ADAPTIVE-ENFORCEMENT.md`.

| Tier | Units | Positions | Signals that set the tier |
|---|---|---|---|
| low | **0** | — | — |
| medium | 9 | 1–3, 5–7, 9, 11, 12 | S8 (an assumption or open question in the report) at every unit; S4, S6 and S2 often |
| high | 3 | 4 (L04), 8 (L08), 10 (L10) | S1 contract conflict (4, 8); S3 external `src/` change (10) |

**S8 fired on every unit.** Every agent recorded open questions or assumptions, as the brief asks. Under the frozen
policy no unit could be low tier, so E's gate differed from D's only by skipping report-evidence and
claim-consistency on 9 units. Those are cheap host-side checks: E's gate CPU was 10% below D's. Nothing in E's agent
turns got cheaper.

The policy escalated exactly the three units the corpus marks hardest. It was never tested, because no gate
rejected anything in any arm.

## 4. Architectural prevention (Phase G)

Source: `phase-g.json`; full account in `ARCHITECTURAL-PREVENTION.md`.

| | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| In-loop `archcheck` runs | — | — | 27 | 30 | 30 | 34 |
| ... that reported a violation | — | — | 0 | 0 | 0 | 0 |
| Ordo admission runs; refusals | — | — | 24; 2 | 25; 3 | 24; 2 | 24; 2 |
| Violation at any scored head | 0 | 0 | 0 | 0 | 0 | 0 |
| Gate architecture rejections | — | — | — | 0 | 0 | 0 |

**No agent in any arm ever produced a boundary violation**, including on L02, the trap task, and including A and B,
which had no checker. The only things to report are:

- 0 invalid implementations were proposed, so the prevention, detection and correction rates are all undefined;
- 0 violations escaped.

## 5. Notable observations (qualitative, recorded for the record)

1. **Verified-state false positive (D).** The promotion rule marks a requirement `verified` when a repository
   acceptance test file mentions its id.
   - At unit 4, D's agent wrote a test-file header comment: "LEND-L04-R3 is not implemented (Ordo conflict)". The
     harness then promoted LEND-L04-R3 to `verified`.
   - D's agent caught the false entry and reported it at units 6 and 10 (`rejectedAssumptions`). It did not rely on it.
   - The finding generalizes. Verified state must bind to what a check *executes*, not to text that names a
     requirement. This strengthens VAC-001's R-ORDO-1. It is recorded as an instrument defect in `RESULTS.md` §4.
2. **D1 was too loud to discriminate.** The OpenDays 2.0.0 update broke 30–53 repository tests in every arm, because
   every arm's L09 used `Calendar.nextOpen`. Every agent saw the failures, read the changelog and switched to
   `onOrAfter`. The silent path (an agent relying on remembered 1.x semantics for the new L10 deadline) never
   occurred.
3. **Conflict handling did not need Ordo.** A and B, with no contract, surfaced both conflicts as reliably as C–F,
   where Ordo refused the contract. This repeats ARCH-001 T5 and VAC-001 V7.
4. **Compaction did not hurt.** The long-lived arms each compacted once, at 149–156k prompt tokens (units 8–10). Every
   unit after a compaction was accepted, and none regressed an earlier task.

## 6. Layer 3: unsupported decisions

See `results/P1/layer3/` and `RESULTS.md` §3 for the adjudicated labels and reviewer agreement.

## 7. What the pilot establishes

| Purpose (`PROTOCOL.md` §6) | Outcome |
|---|---|
| Feasibility | **Yes.** Six concurrent K1 chains with gates, verified state, a policy, post-hoc sealed scoring and Layer 3 all ran end to end. Two measurement defects were found and fixed by amendment (A1 cost, A2 Layer 3 bundle). One instrument defect (verified-state promotion by text match) is recorded |
| Discrimination | **No.** All arms are at ceiling (§1). By §7, the confirmatory corpus must be amended for difficulty before any confirmatory run |
| Variance | Failure variance is 0, so the failure ICC cannot be estimated. Cost per unit by arm: SD across positions $0.23–0.32 |
| Cost | Measured: $43.82 agent cost for 72 units ($0.61 per unit average), plus Layer 3. Projection in §8 |

## 8. Projected confirmatory budget (`PREREGISTRATION.md` §3; copied to `BUDGET.md` §5)

**Inputs.** Pilot failure proportions are all 0, floored to p = 0.05. ρ is not estimable, so the default 0.05 is
used.

**Units per arm:**

| Hypothesis and effect | 25-unit chains | 50-unit chains | 100-unit chains |
|---|---|---|---|
| H1 / H2 / H7 (d = 0.10) | 129 | 203 | 349 |
| **H3 and H4 (d = δ = 0.05)** | **517** | 811 | 1,398 |

**Design implied by the rule.** 21 chains of 25 per arm (525 units), plus 3 replicates each of the 50- and 100-unit
chains. That is **975 units per arm, 5,850 units in all**.

**Model cost.** 975 × (sum of the six arms' pilot cost per unit, $3.65) ≈ **$3,560**. That is before Layer 3 review
(about +15%) and before the growth in per-unit cost on longer chains. **Estimate: about $4,000–4,500.**

**Construction cost.** L13–L25 plus about 75 tasks for the 50- and 100-change chains (`TASK-CORPUS.md` §4), each
with sealed oracles, references, traps and a self-check.

**Futility.** On the pilot corpus, the expected number of failures in a confirmatory run is about 0. Under the
preregistered power rule (H4: "if neither D nor E records at least 10 failures, noninferiority is reported as not
established"), **such a run could not establish any reliability claim at any spend.** Spending it on this corpus
is not recommended. The corpus must first be shown to produce failures, in a second pilot (`RECOMMENDATIONS.md`,
R-EXP-4).
