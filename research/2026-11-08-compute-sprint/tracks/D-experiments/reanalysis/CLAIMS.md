# Published-claim recomputation table (SPR-D-01)

Source of every recomputed number: `outputs/reanalysis.json` (produced by `reanalyze.py`, seed 20261108,
10,000 bootstrap resamples). Raw inputs (read-only): cohort-based-engineering `research/experiments/VAC-001/results/*/*/{usage,verify}-N-K.json`,
`research/experiments/VAC-002/P3/results/S2/*/score-final.json` + `review/adjudicated.json`, praxis
`research/experiments/EX-ROS-2026-A021-harness/sessions.json`, `EX-ROS-2026-A024-run/{sessions.json,acceptance,evaluation,blinding}`.
research-documents@b372a7f was checked: it holds only narrative summaries of VAC-001/VAC-002, no additional raw data.

| Claim (as published) | Recomputed from raw | Classification |
|---|---|---|
| A021 grouped $9.48 vs independent $21.51 | $9.4768 vs $21.5148 (control includes $3.84 of two failed item-04 attempts; completed sessions only: $17.68) | VERIFIED (n = 1 per arm; no inference possible) |
| A021 61 vs 112 minutes | 61.2 vs 111.4 min (attempt-2 counted to its `blockedAt`) | VERIFIED (within rounding) |
| A024 $8.27 / $15.30 / $17.43 | $8.2725 / $15.3005 / $17.4306 (excl. pre-start launcher failures; incl. them B $15.69, C $18.24) | VERIFIED (n = 1 per arm) |
| A024 36/36 all arms; architecture 5, 10, 8 of 10 | 36/36 ×3; composites 5, 10, 8 (max 10) via reveal mapping P/K/W | VERIFIED |
| VAC-001 B vs A −40.9% (CI −48.1% to −33.0%) | −40.86% (CI −48.18% to −33.01%); costs recomputed from tokens × price table 2026-10-20.1 match recorded costs to ≤ $4e-7; 96/96 verdicts accepted, independent acceptance proxy agrees on 96/96 | VERIFIED (arithmetic); CI understates uncertainty, see note |
| VAC-001 F1 replication −38.1% | −38.06% (CI −46.96% to −26.37%) | VERIFIED |
| VAC-001 Ordo/full-Echelon controls +14% to +31% | C vs B +14.1% (CI +2.5% to +27.9%); D vs B +16.8% (+6.2% to +29.6%); D vs B F1 +31.0% (+21.3% to +43.3%) | VERIFIED |
| VAC-001 fresh-from-verified-state +86% | DR vs D +85.7% (CI +49.1% to +129.1%), 8 blocks, 1 chain | VERIFIED (preliminary, n = 1 chain) |
| VAC-002 P3 H1 3/18 vs 7/18, p = 0.125 | 3/18 vs 7/18 under oracle, review and oracle∧review rules; discordant 0:4; exact sign p = 0.125; cluster-bootstrap RD −0.222 [−0.556, 0] | VERIFIED |
| VAC-002 P3 H4 E 7/18 vs B 3/18, p = 0.125 | Confirmed (oracle∧review) 7/18, p = 0.125; oracle-only 8/18, p = 0.0625 | VERIFIED (confirmed rule) |

**Unit-of-independence note (VAC-001).** The published bootstrap resamples (run, position) blocks as if independent.
In arms B, C and D all 8 units of a run are one continuous agent, so units within a chain are correlated. At the chain
level there are 3 chains for B vs A (−39.5%, −42.2%, −38.1%: same sign, exact sign test p = 0.25) and 2 for C vs B.
The direction is consistent, but the 95% intervals should be read as within-fixture, within-chain precision, not as
replication-level uncertainty.
