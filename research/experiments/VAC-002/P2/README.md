# VAC-002-P2: unauthorized decision prevention and verified decision authority

**What it asks.** Can Echelon's decision architecture stop an agent from making consequential business decisions
nobody authorized, *before* the decision reaches code? What does each mechanism cost?

**Why.** In VAC-002 pilot P1, a long-lived agent with no controls exempted staff from L04's money-owed limit. The
hidden oracle accepted the change; the blinded review found it. Five other arms passed. `ROOT-CAUSE.md` shows that
those arms were handed the answer: an experimenter-written Ordo conflict node and an instruction not to implement
R3. So P1 cannot say whether controls prevented the error.

**Status: in progress.** See the table below for each phase.

| Phase | Status | Document |
|---|---|---|
| A. Root cause | done | [`ROOT-CAUSE.md`](ROOT-CAUSE.md) |
| B. Decision authorization contract | done | [`DECISION-AUTHORITY.md`](DECISION-AUTHORITY.md) |
| C. Discriminating corpus (12 scenarios, 3 domains) | done | [`TASK-CORPUS.md`](TASK-CORPUS.md) |
| D. Two-dimensional oracle, validated | done | [`ORACLE-SPEC.md`](ORACLE-SPEC.md) |
| E. Five arms | done | [`ARMS.md`](ARMS.md) |
| Protocol, preregistration, metrics, budget | frozen | [`PROTOCOL.md`](PROTOCOL.md), [`PREREGISTRATION.md`](PREREGISTRATION.md), [`METRICS.md`](METRICS.md), [`BUDGET.md`](BUDGET.md) |
| F. Smoke test and bounded pilot | pending | [`PILOT-RESULTS.md`](PILOT-RESULTS.md) |
| G. Blinded review | pending | [`REVIEW.md`](REVIEW.md) |
| H–I. Measurement and statistics | pending | [`STATISTICAL-ANALYSIS.md`](STATISTICAL-ANALYSIS.md) |
| J. Recommendations and Praxis intake | pending | [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) |
| Reproduction | pending | [`REPRODUCTION.md`](REPRODUCTION.md) |

## Layout

| Path | Contents |
|---|---|
| `fixture/{lending,billing,clinic}/repo` | The three starting repositories; `fixture/authority-section.md` is the README section common to all three |
| `scenarios/Sxx/` | `scenario.json` and `overlay/` (requirement, visible tests, notes, records) |
| `harness/p2.sh` | Execution lifecycle: setup, K1 turns, admission, risk policy, independent reviewer, gate, scoring, budget, queue |
| `harness/p2.fsx` | F# functions: `trx`, `records` (RC1–RC3), `admit` (A1–A9), `policy`, `stream`, `render`, `score` |
| `harness/corpus.sh` | Tree materialisation, hidden-oracle runner, corpus self-check |
| `harness/tests/authz-cases.sh` | Unit cases for the admission and authority-record rules |
| `harness/smoke/fake-claude.sh` | The model-free stand-in agent for harness smoke tests |
| `harness/briefs/` | The arm brief template and the reviewer brief |
| `harness/policy/risk-policy.json` | Arm E's frozen policy 1.0.0 |
| `harness/review/` | The blinded review: rubric, bundle builder, reviewer runner |
| `sealed/` | The encrypted hidden material, its manifest and seal record |
| `results/RUN/SCEN-ARM/` | Observations (`METRICS.md` §5) |

**Reused from VAC-002 and earlier:**

- the Lending fixture and its sealed reference chain (`ref-L03`, `ref-L04`, arm B's defect);
- the oracle support module and the seal script;
- the K1 launcher design and the per-session cost rule (A1);
- the evidence classes.
