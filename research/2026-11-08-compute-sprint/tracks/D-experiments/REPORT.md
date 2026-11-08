# Track D — Controlled AI Development Experiments (D-001)

> Committed by RD-000 from D-001's final hand-back text. The harness refuses subagent report-file writes (D-010).
> Worker final commit: `0f8705c`. Commits: 20afc87; ff9e73d (protocols, committed before the runs); 2f0932b; 0f8705c.

## Summary
- **Re-analysis.** Every published number checked (10) recomputes from the raw records. None is CONTRADICTED and none is INCONCLUSIVE.
- **Where the raw data is.** The raw data lives in cohort-based-engineering and praxis. research-documents@b372a7f holds only narrative summaries of VAC-001 and VAC-002, with no additional raw data.
- **Agent experiments blocked.** The worker had no Agent or subagent tool, so the matched-task agent experiments were not run (SPR-D-08, NOT TESTED).
  - The only remaining route was remote `create_session`. It would have needed the fixture pushed, which is not permitted, and would have exceeded the concurrency cap.
  - The worker did not use it without authorization.
  - The Director has since taken this experiment up as track D2 (DECISION-LOG D-020).
- **What was run instead.** Three confirmatory and two exploratory experiments on verification cost, on indy-init-rehearsal-010@95b3ed4.

## Published claims (`reanalysis/CLAIMS.md`, `outputs/reanalysis.json`)

| Claim | Recomputed | Class |
|---|---|---|
| A021: $9.48 vs $21.51; 61 vs 112 min | $9.477 vs $21.515; 61.2 vs 111.4 min. Two failed attempts account for $3.84 of the control cost; counting completed sessions only gives $17.68 | VERIFIED (n=1 per arm) |
| A024: $8.27 / $15.30 / $17.43; 36/36; architecture 5/10/8 | Exact match | VERIFIED (n=1) |
| VAC-001: B vs A −40.9% [−48.1, −33.0] | −40.9% [−48.2, −33.0]. Cost recomputed as tokens × prices matches to within $4e-7 | VERIFIED |
| VAC-001: controls +14% to +31% | +14.1% / +16.8% / +31.0% | VERIFIED |
| VAC-001: fresh from verified state +86% | +85.7% [+49, +129], 1 chain | VERIFIED (preliminary) |
| VAC-002 P3: 3/18 vs 7/18, p=0.125 | Same result under all three outcome rules; discordant blocks 0:4 | VERIFIED |

### Caveats
- **VAC-001 confidence intervals look tighter than they are.** The bootstrap treats units inside one continuous chain as independent. Counted by chain instead, all 3 chains favour B (sign test p=0.25).
- **VAC-002 P3 was badly underpowered.** It had 0.19–0.21 power for the observed effect. Reaching 80% power needs about 52–72 blocks; the preregistered sizing assumed 17.
- **Replicates needed (ESTIMATE):**

  | Comparison | Replicates |
  |---|---|
  | VAC-001 B vs A | 5 blocks |
  | VAC-001 D vs B | 14 blocks |
  | VAC-001 C vs B | 24 blocks |
  | A021 and A024 continuous vs reset | about 4 runs per arm |
  | A024 handoff vs reset | about 39 runs per arm |

## Experiments
The host was heavily loaded (load average 9–24), so CPU time is the primary measure.

### Confirmatory
Preregistered and committed before running; n=6 per arm, in alternating order. All three met their decision rule: SUPPORTED, p=0.0022.

| ID | Result |
|---|---|
| SPR-D-03 | A no-op build costs 0.044× the CPU of a clean build (CI 0.038–0.104) |
| SPR-D-04 | An edit that changes the root project's public surface costs 5.7× one that doesn't (CI 4.9–11.5), about the cost of a full clean build |
| SPR-D-05 | One test project costs 0.037× the full offline suite (CI 0.033–0.048) |

### Exploratory
n=4 per arm.

| ID | Result |
|---|---|
| SPR-D-07 | Scoped build-and-test costs 0.14× the CPU of the full step. This measures cost only; whether skipping the other tests is safe was not tested |
| SPR-D-06 | Warm build servers made no measurable wall-time difference (INCONCLUSIVE) |

## Gaps
- SDE-Engineering-Trial-1/2 are unreadable.
- The original analysis oracles were not re-run.
- Live GitHub tests and npm-dependent tests could not run here; they were filtered out or held constant.

## Files (`tracks/D-experiments/`)
- `protocols/`: COMMON, SPR-D-03/04/05, EXPLORATORY-06-07
- `plans/`
- `raw/SPR-D-02..07.jsonl`
- `reanalysis/`: stats.py, reanalyze.py, test_stats.py (18 tests passing), CLAIMS.md, outputs/
- `tooling/`: bench.py, analyze_bench.py (10 tests passing)
- `experiments.json`: SPR-D-01..08
- `findings.json`: D-F-01..13
- `CHECKPOINT.md`
