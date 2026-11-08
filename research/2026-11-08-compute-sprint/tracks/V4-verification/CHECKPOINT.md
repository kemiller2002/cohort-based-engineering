# V4-verification checkpoint

- 15:58 EST start. Scratch copies made at /home/user/sprint-scratch/V4/ws (28 workspaces; __pycache__ removed in copies only).
- Step 1 (oracle from SPEC.md) in progress.
- 16:25 Oracle written from SPEC.md + D2-03 workspace files (scripts/oracle.py, probe_runner.py, controls/). Validated on 11 controls (reference, naive, planted-follower, refuser, empty, impostor-NotSpecified): all as expected (raw/test_oracle-output.txt).
- Next: score 28 runs.
- 16:35 Re-scored 28 runs: 28/28 run-level, 112/112 trap-level, 42/42 followed-planted cells agree with committed scores (raw/agreement.json).
- Stats: primary 13/6, p=5/17787 reproduced exactly; Holm secondaries reproduced (raw/v4-stats.json).
- Arm check: 0 mismatches. Confounds: none found (raw/confounds.json). Documentation rule: G 0 / M 21 (QUESTIONS rule), M 20 (anywhere rule).
- Discrepancies are in REPORT text: fp means (M 1.0 / G 0.17, not 0.83 / 0), T4 "planted note" mischaracterised, wall +40% not +38%, per_trap_violations label, prompt placement deviation not in spr-x-02/REPORT.
- verdicts.json written (7 entries). Tests: scripts/test_oracle.py, test_stats.py, test_documentation.py all pass.
