# VAC-002 budget and stopping rules

**Status.** Written and frozen before the pilot. §5 (projected confirmatory budget) is filled in after the pilot by
the rule in `PREREGISTRATION.md` §3. That is the only section that may change, and the change is logged.

**No spending ceiling was given for VAC-002.** The mission says that without an explicit ceiling the harness and a
*bounded pilot* are run, and the work stops before significant confirmatory spending, reporting the projected
cost. This file bounds the pilot accordingly. **The confirmatory run is not authorized** by this file.

## 1. Cost basis

| Item | Basis |
|---|---|
| Agent turns | Claude Code's `total_cost_usd` per turn (`cli-estimate`: list price, final output tokens, every model including small side calls). For the K1 smoke call it matched the committed price table `2026-10-20.1` to the cent ($0.01564 vs $0.01564) |
| Gate and scoring | Host CPU; not model cost. Reported as milliseconds |
| Layer 3 reviewers | `cli-estimate` of the reviewer turns |
| Orchestrator (this session) | **Unavailable**: the runtime does not expose the session's own usage. As in VAC-001 and ARCH-001 |
| Provider-billed cost | **Unavailable** |

## 2. Prior estimates (before the pilot)

| Source | Cost per unit (model) |
|---|---|
| ARCH-001, K1, Lending, one requirement phase, about 6 min | $0.33–0.48 (arm means $0.36–0.45 per accepted requirement) |
| VAC-001, K0 sub-agents, Ledger, chained | $0.17–0.42 (lower bound) |

**VAC-002 estimate.** VAC-002 units are larger, and K1 fresh sessions pay 1-hour cache writes ($8/MTok). The prior
estimate is therefore **$0.40–0.80 per unit**, with gated arms at the upper end, before repairs.

## 3. Pilot budget (P1)

| Item | Units | Estimate |
|---|---|---|
| Agent turns: 6 arms × 12 units | 72 | $29–58 |
| Repair turns (D, E, F; assume a third of gated units) | ~12 | $3–8 |
| Layer 3 review (two reviewers plus adjudication, seeded sample) | — | $8–15 |
| **Total estimate** | | **$40–81** |
| **Pilot ceiling (hard)** | | **$120** (`cli-estimate`, all agent and reviewer turns) |

### Stopping rules (pilot)

1. **Unit boundaries.** The orchestrator totals `cli-estimate` cost across every `turn-*.json` after each unit
   boundary of the slowest arm.
2. **Stop file.** If the agent-turn total reaches **$95**, it creates `$VAC2_STATE/P1/STOP`. Every chain then stops
   before its next unit. Units in flight finish, so the margin to $120 covers them and Layer 3.
3. **Balanced truncation.** A stopped pilot is truncated to the last position that every arm completed. Any extra
   units are reported separately, never pooled.
4. **Runaway turn.** A turn that exceeds 45 minutes is ended by `timeout` (X5).
5. **Per-arm alarm.** If an arm's mean cost per unit after 3 units exceeds 3× the prior upper estimate ($2.40), the
   orchestrator stops that arm and records why, since it signals a harness defect rather than the agent.

## 4. Confirmatory construction cost (not model cost)

The 25-change chain needs L13–L25 built. The 50- and 100-change chains need about 75 more tasks. Every task needs a
requirement, visible tests, a sealed oracle, a cumulative reference, traps and a self-check, as L01–L12 had. This is
engineering time, not agent-trial spend, but it is the gating cost of Phase E.

## 5. Projected confirmatory budget (filled after the pilot; see `PILOT-RESULTS.md`)

Computed by `PREREGISTRATION.md` §3 from the pilot's failure proportions, ICC and mean cost per unit per arm.
Reported in `PILOT-RESULTS.md` §8 and copied here.

**Pilot spend (measured).**

| Item | Cost |
|---|---|
| Agent model cost, 72 units (cli-estimate, A1) | $43.82 |
| Layer 3 reviewers | see `results/P1/layer3/summary.json` |

The pilot stayed under the $95 stop and the $120 ceiling.

**Inputs.** All pilot failure proportions were 0, floored to p = 0.05. ρ could not be estimated, so the default 0.05
is used.

**Units per arm required:**

| Hypothesis and effect | 25-unit chains | 50-unit chains | 100-unit chains |
|---|---|---|---|
| H1 / H2 / H7 (d = 0.10) | 129 | 203 | 349 |
| **H3 and H4 (d = δ = 0.05)** | **517** | 811 | 1,398 |

**Design.** 21 chains of 25 per arm, plus 3 replicates each of the 50- and 100-unit chains. That is **975 units per
arm, 5,850 in all**.

**Projected cost.**

| Component | Estimate |
|---|---|
| Model cost: 975 × $3.65 (the sum of the six arms' pilot cost per unit) | **≈ $3,560** |
| Plus Layer 3 (about +15%) and per-unit cost growth on long chains | **≈ $4,000–4,500 in all** |

**Decision: not run.** No confirmatory spending ceiling was given. The discrimination check also failed: every arm
was at ceiling, so the run is futile on this corpus. The next spend is a second pilot of about $45 on a harder corpus
(`RECOMMENDATIONS.md` R-EXP-4).
