# VAC-002-P3 budget

**Ceiling: $150** in measured model and review expenditure, for the whole of P3. That includes the orchestrator's
model smoke tests (`budget-ledger.jsonl`), every agent execution and every review session.

**Cost basis.** The CLI-reported list-price estimate (`total_cost_usd`). It is cumulative per session, so each
session is counted once, at its last value (VAC-002 amendment A1; `p3.sh cost`, `p3.sh spent`). It is not
provider-billed. The orchestrating agent's own session is not part of the experiment's measured spend, as in P2.

**Hard stop.** `p3.sh exec` refuses to start an execution once cumulative spend reaches **$140** (`P3_STOP_USD`). That
keeps $10 for review and analysis.

## Estimates before each stage

| Stage | Executions | Estimate per execution | Estimate | Basis |
|---|---|---|---|---|
| Orchestrator smoke tests | — | — | $0.24 (spent) | `budget-ledger.jsonl` |
| Stage 1: arm A, 16 scenarios × 2 | 32 | $0.30 | ~$9.60 | P2 arm A, $0.297 |
| Stage 1 review: 32 items × 2 reviewers, plus R3 on disagreements | 64 item-reviews | $0.21 | ~$14 | P2 review: $25.17 for 120 item-reviews |
| Sizing run: arm B, 16 × 1 (only if Stage 1 qualifies) | 16 | $0.32 | ~$5.10 | P2 arm B, $0.319 |
| **Through the sizing run** | | | **~$29** | |
| Stage 2 | set by CR-1 | A $0.30, B $0.31, C $0.33, D $0.36, E $0.55 | ~$1.85 per 5-arm block, plus review | P2 per-arm costs (P2 C ≈ P3 D, P2 D ≈ P3 E) |

Stage 2's affordable size, from the start of Stage 2, is (remaining − $10 reserve) / (block cost + block review).
A five-arm block costs about $1.85 to execute and about $2.10 to review twice in full (5 items × $0.42), so about
$3.95. With $110 left that allows about 28 blocks; reviewing every item once, with a second review only of
oracle-flagged items and disagreements, allows about 40. The choice is made in CR-1.

## Actual spend

Filled in as each stage ends.
