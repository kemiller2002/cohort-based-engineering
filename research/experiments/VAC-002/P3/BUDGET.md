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

| Item | Executions | Agent cost | Review cost | Total |
|---|---|---|---|---|
| Orchestrator smoke tests and amendment A1 check (`budget-ledger.jsonl`) | — | — | — | $0.26 |
| Run S1, void (amendment A1: no turn reached the model) | 0 | $0.00 | — | $0.00 |
| Stage 1 round 1 (`S1A1`, arm A, D01–D16 × 2) | 32 | $9.02 | $11.23 | $20.24 |
| Stage 1 round 2 (`S1R2`, arm A, D17–D21 × 3) | 15 | $3.81 | $4.87 | $8.68 |
| Sizing run (`S1B`, arm B, D17–D21 × 3) | 15 | $4.06 | $4.80 | $8.86 |
| Stage 2 (`S2`, arms A–E, C01–C06 × 3) | 90 | $27.40 | $26.86 | $54.27 |
| **Total** | **152** | **$44.29** | **$47.76** | **$92.31** |

**Against the estimates.**

- **Stage 1 round 1** came in at $20.24 against about $24 estimated.
- **Stage 2** came in at $54.27 against about $60 estimated.
- **Arm E** averaged $0.439 per execution against $0.55 estimated.
- **Review** averaged $0.30 per item for two reviewers, against $0.32–0.42 estimated.

**Headroom.** The ceiling was never approached: the hard stop at $140 did not fire. $57.69 of the $150 remains.
