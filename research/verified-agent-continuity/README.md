# Verified agent continuity (VAC-001)

**Question.** Can persistent, independently verified engineering state make agent reliability independent of
session length? And are long-lived agents cheaper per correctly completed requirement?

**Status (2026-10-21).** The baseline, protocol, pilot (P1), replication (R1) and fault injection (F1) are complete:
96 chained units in 5 arms. Correctness was at ceiling in every arm, so the reliability hypotheses are untested at
this difficulty. Cost results are firm within the stated scope.

## Results in one table

| Arm | Description | CCR (lower bound) | Accepted | Notes |
|---|---|---|---|---|
| A | Fresh agent per change, agent-written handoff | $0.28–0.32 | 24/24 | Baseline |
| B | One agent across the chain | $0.17–0.19 | 24/24 | **−40.9% vs A** (CI −48.1% to −33.0%) |
| C | B + Ordo admission, VAC-RULES, decision records | $0.20–0.22 | 16/16 | +14.1% vs B |
| D | C + Praxis protocol, independent gate, verified state | $0.21–0.23 | 24/24 | +16.8% vs B (no-fault), +31.0% (F1) |
| DR | D's controls, fresh agent per change, reconstructed from verified state | $0.42 | 8/8 | **+86% vs D**, +51% vs A |

Across all arms:

- **Integrity:** 0 regressions, 0 false completions, 0 architecture violations, 0 decision reversals.
- **Faults:** 0/20 injected false premises accepted.
- **Decisions:** 0 fabricated premises in 441 decisions.
- **Unsupported decisions:** 8/202 adjudicated decisions were unsupported scope additions presented as settled.

## Deliverables

| # | File | Contents |
|---|---|---|
| 1 | [`evidence-baseline.md`](evidence-baseline.md) | Prior Echelon evidence, classified; the verification gate's status |
| 2 | [`research-protocol.md`](research-protocol.md) | Preregistered protocol (commit `05b3cf2`) with amendments A1–A4 |
| 3 | [`metrics-schema.json`](metrics-schema.json) | `cbe.vac-001.metrics/1` (UDR, AVR, DDR, FCR, CCR, longevity) |
| 4 | [`experiment-manifest.json`](experiment-manifest.json) | Runs, unit orders, fault placement, controls, tool versions |
| 5 | [`pilot-results.json`](pilot-results.json) | P1, descriptive |
| 6 | [`hallucination-evaluation.md`](hallucination-evaluation.md) | Layers 1–3, reviewer agreement, detector accuracy, UDR and DDR |
| 7 | [`error-propagation-results.md`](error-propagation-results.md) | F1 fault injection |
| 8 | [`agent-longevity-analysis.md`](agent-longevity-analysis.md) | CCR contrasts, censored longevity, context growth |
| 9 | [`verified-continuity-design.md`](verified-continuity-design.md) | The prototype, its state model, the D vs DR comparison and the weaknesses found |
| 10 | [`engineering-recommendations.md`](engineering-recommendations.md) | Answers to the 10 questions; recommendations with evidence status |
| 11 | [`publication-readiness.md`](publication-readiness.md) | What can and cannot be claimed |
| 12 | [`r-exp-1-protocol.md`](r-exp-1-protocol.md) | R-EXP-1 (VAC-003) preregistered design: a fixture whose baseline fails; H3, H5, H6. Not run |
| 13 | [`r-exp-2-protocol.md`](r-exp-2-protocol.md) | R-EXP-2 (VAC-004) preregistered design: ≥ 24-unit K1 chains past compaction, cross-family Layer 3; H2. Not run |
| 14 | [`metrics-schema-2.json`](metrics-schema-2.json) | `cbe.vac.metrics/2`: /1 unchanged plus optional R-EXP fields (`analysis/derive-metrics-schema.py`) |
| 15 | [`analysis/r-exp-plan.json`](analysis/r-exp-plan.json) | Sample sizes and cost estimates for both protocols (`analysis/plan.py`) |

The experiment code and data are in [`../experiments/VAC-001/`](../experiments/VAC-001/).
