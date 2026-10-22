# VAC-002-02: Session-aware cost telemetry for resumed agent sessions

Priority: P1
Owner system: Percepta (experiment telemetry) and Praxis telemetry; also every experiment harness in this
repository. Forward at triage.
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/PROTOCOL.md` amendment A1, `RESULTS.md` §4 I2,
`RECOMMENDATIONS.md` R-PERC-1.

## Finding

For a resumed Claude Code session, `total_cost_usd` (and `modelUsage`) in the CLI result is the session's
**cumulative** cost, while `usage` is per turn. VAC-002's frozen budget script summed `total_cost_usd` over every
turn. Partway through the pilot it reported $62.50 against a real $22.02, an over-count of 2.8×. Uncorrected, it
would have stopped the pilot at a third of its budget, and it would penalise long-lived agents in any cost comparison.

## Requirements (proposed)

- **VAC-002-02-R1.** Telemetry records per-turn cost as the difference from the previous turn's cumulative value in
  the same session. A session's total is its last cumulative value. Totals are sums over sessions, never over turns.
- **VAC-002-02-R2.** Each record carries the session id and turn index, so the rule in R1 can be audited.
- **VAC-002-02-R3.** A test with a synthetic three-turn resumed session asserts that the turn costs sum to the final
  cumulative cost.

## Acceptance evidence

- The R3 test, and VAC-002's `harness/budget.sh` and `analyze.fsx` reproducing the published P1 costs ($43.82 in
  total).
