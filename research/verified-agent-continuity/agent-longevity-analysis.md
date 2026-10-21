# VAC-001: agent longevity, cost and reliability across successive changes

- **Status:** complete for runs P1, R1 and F1 (96 units), 2026-10-21.
- **Pre-specified tests:** CCR (H1) and lifetime-dependence (H2).
- **Descriptive only:** the other hypotheses. They could not be tested, because no failures occurred (see §3).
- **Sources:**
  - Per-run analyses: `research/experiments/VAC-001/results/{P1,R1,F1}/analysis.json` (`vac.fsx analyze`).
  - Pooled no-fault blocks: `results/pooled-P1-R1.json`.
  - Per unit: `results/<run>/<arm>/usage-N-A.json` and `verify-N-A.json`.
  - Cost is computed from REL-001 price table `2026-10-20.1`. It is a **lower bound** (amendment A4); a
    sensitivity estimate is given beside it.

## 1. What was executed

| Run | Arms | Units per arm | Order | Faults |
|---|---|---|---|---|
| P1 | A B C D | 8 | V7 V5 V1 V4 V8 V2 V6 V3 | none |
| R1 | A B C D | 8 | V7 V4 V1 V2 V6 V8 V3 V5 | none |
| F1 | A B D DR | 8 | V8 V4 V1 V6 V3 V7 V2 V5 | 5 |

- **Total.** 96 agent units, 0 exclusions. X2: every request was served by `claude-opus-5-5` at effort `medium`.
  X4: 0 contamination hits after the detector fix.
- **Tokens.** 65,089,713 across all trials.
- **Cost.** $23.61 as a lower bound, $31.18 with the visible-output estimate.
- **Orchestrator cost.** The harness session's own model cost cannot be separated from inside the session, so it is
  **unavailable**.

## 2. Cost per correct requirement (CCR)

### 2.1 Per arm and run

All 8 units were accepted in every arm and run, so CCR equals the cost per unit.

| Run | Arm | CCR lower bound | CCR with estimate | Tokens per accepted unit | Requests per unit | Cache-write tokens | Cache-read share |
|---|---|---|---|---|---|---|---|
| P1 | A | $0.309 | $0.387 | 671,865 | 10.8 | 284,068 | 94.7% |
| P1 | B | $0.187 | $0.253 | 605,092 | 6.6 | 106,522 | 97.8% |
| P1 | C | $0.204 | $0.283 | 674,435 | 6.8 | 111,158 | 97.9% |
| P1 | D | $0.217 | $0.298 | 716,837 | 6.9 | 119,714 | 97.9% |
| R1 | A | $0.317 | $0.406 | 644,850 | 10.1 | 307,058 | 94.0% |
| R1 | B | $0.183 | $0.250 | 617,011 | 6.8 | 96,425 | 98.0% |
| R1 | C | $0.219 | $0.295 | 717,481 | 7.0 | 121,507 | 97.9% |
| R1 | D | $0.215 | $0.296 | 671,923 | 6.4 | 130,716 | 97.6% |
| F1 | A | $0.280 | $0.356 | 553,762 | 9.1 | 275,268 | 93.8% |
| F1 | B | $0.173 | $0.244 | 571,878 | 6.4 | 94,940 | 97.9% |
| F1 | D | $0.227 | $0.314 | 760,195 | 7.2 | 120,718 | 98.0% |
| F1 | DR | $0.421 | $0.516 | 930,885 | 13.1 | 383,084 | 94.8% |

### 2.2 Paired contrasts

Method: blocks are (run, position), so every block compares the same task. Percentile bootstrap, 10,000 resamples,
seed 20261021. Values are relative differences in cost per accepted unit.

| Contrast | Blocks | Lower-bound cost: point | 95% CI | With visible-output estimate: point | 95% CI |
|---|---|---|---|---|---|
| **B vs A** (P1+R1) | 16 | **−40.9%** | −48.1% to −33.0% | −36.6% | −42.4% to −30.3% |
| B vs A (F1, replication) | 8 | −38.1% | −47.1% to −26.1% | −31.6% | −39.5% to −21.2% |
| C vs B (P1+R1) | 16 | +14.1% | +2.7% to +27.4% | +15.0% | +5.6% to +25.3% |
| D vs B (P1+R1) | 16 | +16.8% | +6.4% to +29.6% | +18.3% | +9.8% to +28.3% |
| D vs B (F1) | 8 | +31.0% | +21.4% to +43.0% | +28.7% | +21.4% to +37.6% |
| D vs A (P1+R1) | 16 | −31.0% | −38.2% to −23.3% | −25.0% | −30.8% to −18.8% |
| **DR vs A** (F1) | 8 | **+50.6%** | +36.8% to +62.0% | +44.9% | +32.8% to +54.6% |
| **D vs DR** (F1) | 8 | **−46.2%** | −56.6% to −32.4% | −39.2% | −49.1% to −26.9% |

### 2.3 Reading

- **H1 is supported in this fixture.** A long-lived agent cost about 40% less per independently accepted requirement
  than a fresh agent per unit with an agent-written handoff. The effect has the same sign and similar size in all
  three runs and under both cost measures.
- **Where the saving comes from.** Tokens per accepted unit are nearly equal for A and B (P1: 672k vs 605k; R1:
  645k vs 617k). The saving is in cache economics, not volume:
  - A fresh agent writes 2.7–3× more cache per chain.
  - It needs ~10 instead of ~6.6 model requests per unit, because it rediscovers the repository.
  - A token-count metric alone would have hidden most of the difference.
- **Echelon controls cost more.** C and D cost +14% to +31% more than B, with no measured correctness, drift or
  safety benefit, because correctness was at ceiling (§3). This agrees in sign with REL-001 run-02 (D vs A +35.5%
  on single tasks). Here, though, D with continuity is still cheaper than A without it (−31%).
- **DR is the most expensive configuration.** DR rebuilds context from verified state with a fresh agent per unit,
  under the full protocol. It costs +51% vs A and is 46% dearer than D. In this fixture, **verified state did not
  replace conversational continuity as a cost lever**: rebuilding context from the repository plus verified state
  cost more than either continuity (D) or a plain handoff (A). This agrees with praxis EX-ROS-2026-A024 (structured
  handoff +10.5% over code-only resets).

## 3. Reliability across successive changes

| Measure (all 96 units) | A (24) | B (24) | C (16) | D (24) | DR (8) |
|---|---|---|---|---|---|
| Final acceptance | 24/24 | 24/24 | 16/16 | 24/24 | 8/8 |
| First-pass acceptance | 24/24 | 24/24 | 16/16 | 24/24 | 8/8 |
| False completions (first pass) | 0/21 claimed | 0/21 | 0/14 | 0/21 | 0/7 |
| Regressions of accepted tasks | 0 | 0 | 0 | 0 | 0 |
| Architecture violations (VAC-RULES) | 0 | 0 | 0 | 0 | 0 |
| Decision reversals (DDR numerator) | 0 | 0 | 0 | 0 | 0 |
| Layer 1 unsupported decisions | 0/122 | 0/113 | 0/70 | 0/106 | 0/30 |
| Critical failures | 0 | 0 | 0 | 0 | 0 |

Claimed completions exclude the V7 stops, which are the correct outcome.

### 3.1 Longevity

No chain had a critical failure, so all 11 chains are **censored at 8 units**. The Kaplan–Meier survival estimate is
1.0 at unit 8 for every arm. The upper 95% bound on the per-unit critical-failure probability (zero events) is:

| Scope | Units | Upper 95% bound |
|---|---|---|
| Pooled | 96 | 3.1% |
| A, B or D | 24 each | 11.7% |
| C | 16 | 17.1% |
| DR | 8 | 31.2% |

Other longevity measures:

- **Recoverable failures:** 0.
- **Repair rounds:** 0. The D/DR gate never rejected a unit.
- **Unresolved defects carried forward:** 0.

### 3.2 What failure rate depends on

The preregistered logistic model regresses failure on unit index, context size, prior decisions, compactions,
completed requirements and verification frequency. It is **not estimable**: there are zero failure events. No claim
is made that reliability is independent of lifetime. What can be said is narrower: within 8 units, and up to
**167k prompt tokens**, no failure occurred in any arm.

**H2 (lifetime-dependence) is untested** at this chain length and difficulty.

### 3.3 Context growth and compaction

| Arms | Prompt size at the last request: unit 1 | Unit 8 | Growth per unit |
|---|---|---|---|
| Long-lived (B, C, D) | 57–74k | 131–167k | ≈ 11–15k |
| Fresh (A, DR) | 60–91k (fixed system and tool prefix, plus the repository read) | similar | none |

**Compactions: 0 in 96 units.** The chains never reached the compaction threshold, so compaction frequency and its
effect on reliability are **unmeasured**. Fixed-interval versus risk-based compaction cannot be answered from these
data.

### 3.4 Cost growth with unit index

| Arm | Slope (USD per unit index, lower bound) | Mean cost, units 1–2 | Mean cost, units 7–8 |
|---|---|---|---|
| A | +$0.016 | $0.247 | $0.351 |
| B | +$0.009 | $0.180 | $0.231 |
| C | +$0.018 | $0.192 | $0.306 |
| D | +$0.008 | $0.227 | $0.278 |
| DR | +$0.011 | $0.352 | $0.486 |

Index is confounded with task mix, since V7, a cheap stop, comes first in P1 and R1, and with codebase growth.
Long-lived B's per-unit cost grew no faster than A's, even though B carried 2× the prompt. Cache reads at $0.20/MTok
keep accumulated context cheap.

## 4. Limitations

- **Ceiling.** The Ledger tasks are small and well specified, with visible acceptance tests. The model solved all
  of them in every arm. Reliability differences, if any, need harder or underspecified work, or chains longer than
  8 units.
- **Sample.** Two no-fault chains per arm (one for DR), and a single fixture and task family. Bootstrap intervals
  over 8–16 blocks capture task-level variance, not chain-to-chain variance.
- **K0 cache condition.** The agents ran as sub-agents sharing a prompt-cache prefix with the orchestrator, as in
  REL-001 run-02. Isolated CLI processes (REL-001 run-03 K1) could change the cache-write share and the size of the
  A–B gap.
- **Output tokens are a lower bound** (amendment A4), and hidden thinking cannot be observed.
- **Concurrent arms.** Arms ran concurrently, so wall-clock time is not reported.
- **Scope violations.** Arm A agents moved files outside the workspace to take a baseline (scope scan: 9 hits
  in A, 2 in B, 1 in D and 1 in DR; the D hit is inside an inline Python edit script and is possibly a detector false
  positive). Most were moves to the session scratchpad, which the sub-agents' inherited system prompt suggests. No
  oracle contamination occurred.
- **No new evidence in the fixture.** DDR can only show unjustified reversals, and there were none.
