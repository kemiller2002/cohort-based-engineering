# VAC-002: long-horizon agent reliability and adaptive verification

**What it asks.** Do long-lived agents accumulate errors? Do Ordo constraints, Dokimos-style independent verification
and verified state prevent consequential errors? Can risk-triggered verification match always-on verification at
lower cost?

**What it inherits.** VAC-001 and ARCH-001 found every arm at the correctness ceiling, so their reliability
hypotheses are untested. VAC-002 builds a corpus designed to produce failures and runs six arms over a cumulative
chain.

**Status: checkpoint, not complete.**

| Done | Not run |
|---|---|
| The harness, the pilot corpus (12 units) and the bounded pilot P1 (6 arms × 12 units), scored by the sealed hidden oracle and reviewed blind in Layer 3 | The 25-, 50- and 100-change confirmatory runs |

**Why the confirmatory runs were not done.** They need a spending ceiling that was not given (`BUDGET.md`, projected
at about $4,000–4,500). The pilot also failed the discrimination check: all 72 units were accepted in every arm.

**Pilot findings** (details and classifications in [`RESULTS.md`](RESULTS.md)):

- **Reliability.** No reliability difference between arms could be observed.
- **Cost.** Continuity was 32% cheaper than fresh agents. Full Echelon controls cost +13% over continuity, with no
  error prevented. Adaptive enforcement saved nothing.

**Next step.** A second pilot on a harder corpus (`RECOMMENDATIONS.md` R-EXP-4).

**Seal.** The sealed oracle's key is published at `sealed/vac002-sealed.key`. The pilot is over, and its corpus will
not be reused for trials.

## Documents

| File | Contents |
|---|---|
| [`BASELINE.md`](BASELINE.md) | VAC-001, ARCH-001 and earlier figures, verified against their records |
| [`PROTOCOL.md`](PROTOCOL.md) | The frozen protocol, deviations and amendments |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | H1–H7: outcomes, comparisons, tests, minimum effects, the noninferiority margin, the sample-size rule |
| [`ARMS.md`](ARMS.md) | The six arms, the gate, the adaptive policy, the five-way mapping for Phase G |
| [`TASK-CORPUS.md`](TASK-CORPUS.md) | The pilot chain L01–L12 and the confirmatory chain design |
| [`FAULT-CATALOG.md`](FAULT-CATALOG.md) | F1–F3 and the dependency change D1 |
| [`METRICS.md`](METRICS.md) | Metric definitions and observation files |
| [`BUDGET.md`](BUDGET.md) | The pilot ceiling, the stopping rules and the projected confirmatory budget |
| [`PILOT-RESULTS.md`](PILOT-RESULTS.md) | P1, descriptive |
| [`RESULTS.md`](RESULTS.md) | Results and answers to the ten final questions |
| [`STATISTICAL-ANALYSIS.md`](STATISTICAL-ANALYSIS.md) | The analysis as run, uncertainty, plots |
| [`ARCHITECTURAL-PREVENTION.md`](ARCHITECTURAL-PREVENTION.md) | Prevention, detection, correction and escape (Phase G) |
| [`ADAPTIVE-ENFORCEMENT.md`](ADAPTIVE-ENFORCEMENT.md) | Arm E's escalations, cost and reliability against D (Phase H) |
| [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) | Engineering changes: implement, defer or reject, each traced to evidence |
| [`REPRODUCTION.md`](REPRODUCTION.md) | How to rebuild the tools, re-run the self-check, the pilot and the analysis |

## Layout

| Path | Contents |
|---|---|
| `fixture/repo` | The starting repository (identical in every arm) |
| `fixture/tasks/Lnn/` | `requirement.md`, `acceptance/`, `stage/`, `before/`, `contract.json` and `task.json` |
| `fixture/tasks-meta.json`, `fixture/make-contracts.py` | Task metadata; the contract and `task.json` generator |
| `fixture/check.sh`, `fixture/check-output.txt` | The corpus self-check and its output |
| `faults/faults.json` | Injected premises and the dependency change |
| `harness/vac2.sh` | Unit lifecycle: `setup`, `stage`, `turn`, `gate`, `state`, `unit`, `chain`, `score` |
| `harness/vac2.fsx` | F# functions: `render`, `repair`, `evidence`, `observe`, `gate`, `policy`, `state` and `stream` |
| `harness/analyze.fsx` | F# analysis: metrics, contrasts, survival, propagation and plot data |
| `harness/policy/adaptive-policy.json` | Arm E's frozen policy (1.0.0) |
| `harness/agent-config.json` | The K1 agent configuration |
| `harness/briefs/brief.md` | The single brief template |
| `harness/smoke/` | The stand-in agent and the end-to-end harness smoke |
| `sealed/` | The encrypted hidden material (oracle, references, traps), its manifest and seal record |
| `results/RUN/ARM/` | Observations (`METRICS.md` §1) |

**Reused, not copied.** VAC-001's directives pack, `vac.fsx usage` (transcript analysis) and Layer 3 rubric;
ARCH-001's Lending fixture, `archcheck` verifier and policy, K1 launcher design and `make-contracts.py`; the REL-001
price table.
