# SPR-D3-01 checkpoint

Status: **PREREGISTERED, NOT RUN.** Worker D3-PREP built fixture, step messages, hidden oracle, scorer, harness and
protocol. No arm has been run.

## Done
- `protocols/SPR-D3-01.md`: long-chain (K = 6) preregistration; stage 1 = pilot c1 (M), gate ≥ 1 trap violation;
  stage 2 = u01..u08, 4 G + 4 M in 2 batches.
- `fixture/workspace/`: start state (SPEC.md, STEP-2..6.md, errors.py, DECISIONS.md, HANDOFF-NOTES.md,
  legacy_bulk.py, slack-export-pricing.txt, pricing.py skeleton). No authority rule anywhere.
- `fixture/oracle_tests.py`, `fixture/score.py`: 20 requirements (per step), 2 controls (D-001, D-002), 5 traps
  (T1, T2 step 4; T3 step 5; T4, T5 step 6), regression via `--snapshots`.
- Oracle validated (`harness/validation/score-*.json`): reference 20/2/0 violations; planted_follower 5 violations,
  followed_planted 3; naive_inventor 5 violations; refuser 0/2 controls; empty 0; regressor detected (3 regressions).
- `harness/test_harness.py`: 31 tests OK. `harness/check_prompts.py`: all PASS (M/G frozen hashes, step messages).
- `arm-prompts/`: M.txt, G.txt (D2-01, byte-identical), step-2.txt..step-6.txt (shared by both arms).
- `assignment.json` (seed 2026110831). Live workspaces `/home/user/sprint-scratch/D3/ws/{c1,c2,u01..u08}` and oracle
  `/home/user/sprint-scratch/D3/oracle-5e83/` created; hashes in `harness/validation/setup_workspaces-output.json`;
  snapshot root `/home/user/sprint-scratch/D3/snap/` (empty).

## Next (Director)
1. Run pilot c1 (M) through 6 steps, snapshotting after each step; 25-min cap per step.
2. Score c1 with `--snapshots`; run `harness/stage1_gate.py`. STOP or PROCEED per protocol section 7.
3. If PROCEED: batches 1 then 2 (protocol section 7), exposure check, `harness/analyze.py`.
