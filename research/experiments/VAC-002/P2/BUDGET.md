# VAC-002-P2 budget and stopping rules

**Ceiling: $150** for everything measurable: pilot agent turns, arm E's reviewer calls, the smoke test, and the
blinded review. Written and frozen before the smoke test.

## 1. Cost basis

| Item | Basis |
|---|---|
| Agent and reviewer turns | The CLI's `total_cost_usd` (list price, every model, `cli-estimate`). It is cumulative per session, so each session is counted once, at its last value (VAC-002 A1) |
| Cached tokens | Priced at the CLI's cache rates, not counted as free |
| Gate, admission, scoring | Host CPU; reported as milliseconds, not dollars |
| This orchestrating session | **Unavailable** (not exposed by the runtime). One check call made while setting up cost $0.087 and is counted |
| Provider-billed cost | **Unavailable** |

## 2. Prior estimate

VAC-002 P1: $43.82 for 72 Lending units ($0.61 per unit; long-lived sessions, medium effort). P2 executions are fresh
agents, which pay more cache writes, but they work on smaller repositories (Billing and Clinic).

| Item | Count | Per item | Estimate |
|---|---|---|---|
| A, B, C (1 turn each) | 36 | $0.40–0.90 | $14–32 |
| D (2–3 turns) | 12 | $0.80–1.60 | $10–19 |
| E (2–3 turns + 0–3 reviewer calls) | 12 | $1.00–2.40 | $12–29 |
| **Pilot agent total** | 60 | | **$36–80** |
| Smoke (model) | 2 executions | | $2–5 |
| Blinded review (2 reviewers + adjudication) | ~250 decisions | | $15–30 |
| **Total** | | | **$53–115** |

## 3. Stopping rules

1. **Stop file.** Before each execution starts, `p2.sh exec` totals the run's cost. At **$110** it records the
   execution as `not-run (budget)` and does not start it. Executions in flight finish; the margin to $150 covers them,
   the smoke test and the review (capped at $30).
2. **Pre-execution reduction rule** (applied once, after the smoke test, before the pilot). Projected pilot cost =
   36 × (mean A–C smoke cost) + 12 × (D smoke-scaled) + 12 × (E smoke cost) + $30 review. If the projection plus the
   amount spent so far exceeds $150, the pilot runs the first 8 scenarios of this priority list (all five arms each):
   S01, S09, S05, S07, S10, S12, S04, S08, then S06, S02, S11, S03. If 8 still exceeds the ceiling, it runs the first
   6. The list is fixed now. It puts the L04 replication first, then the high-severity scenarios, then one per
   remaining family.
3. **Balanced truncation.** If the stop file fires mid-run, only scenarios that every arm completed are analysed. The
   others are reported separately, never pooled. Executions are queued in a seeded random order (seed 20261023), so a
   stop does not systematically favour any arm.
4. **Runaway turn.** A turn is ended after 30 minutes (`timeout`); a reviewer call after 20.
5. **Per-arm alarm.** If an arm's mean cost per execution after 3 executions exceeds $4, it is a harness defect
   signal: stop that arm and record why.
6. **Review cap.** The blinded review stops at $30. Items not labelled are reported as unlabelled.

## 4. Spend (filled in after the pilot)

See `PILOT-RESULTS.md` §2.
