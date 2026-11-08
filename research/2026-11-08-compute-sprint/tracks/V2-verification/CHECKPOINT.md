# V2-verification checkpoint

- Worker: V2-001 (independent verifier); parent RD-000; date 2026-11-08.
- Status: **all 13 claims judged**. 12 are VERIFIED and 1 (B-F-03) is PARTIALLY VERIFIED. See `verdicts.json`.
- Regenerate verdicts: `python3 -I scripts/build_verdicts.py > verdicts.json`.
- Tests: `cd scripts && python3 -m unittest test_v2 -v` (15 tests). The end-to-end fabrication test needs
  `/home/user/sprint-scratch/V2/indy-dae2347` and `/home/user/sprint-scratch/V2/indy-init-full`; it is skipped if they are absent.

## Scratch state (/home/user/sprint-scratch/V2)
- `praxis-12bf995/`: git-archive export of praxis v3.25.0, built Release (0 warnings, 0 errors).
- `indy-dae2347/`, `indy-459f65a/`: verifier exports. `indy-init-full/`: full-history clone of kemiller2002/Indy-init.
- `repro/`: Praxis fixtures (case-a, case-b). `fab*/`: fabricated acceptance bundles.

## Scripts -> claims
| Script | Claims |
|---|---|
| verdict_artifacts.py | 1 (B-F-02), 3 (B-F-01) |
| blob_compare.py | 2 (B-F-07) |
| actions_count.py | 5 (R10 gate) |
| release_inventory.py | 6 (C-F-01) |
| consumer_pins.py | 8 (C-F-08) |
| praxis_completion_repro.sh | 10 (E-F-01), 12 (E-F-03) |
| flag_survey.py | 10 (survey) |
| fabricate_acceptance.py | 11 (E-F-02) |
| Manual (commands recorded in verdicts.json `method`) | 4 (B-F-03), 7 (C-F-04), 9 (C-F-05), 13 (E-F-07) |

## Incident (self-reported)
The first run of `praxis_completion_repro.sh` had a bug: `cd` ran inside a command substitution, so it did not persist. As a result, `praxis` ran in the
`scripts/` directory of this worktree. That run:
- created `scripts/.ros/` (removed);
- created `/home/user/cohort-based-engineering/.git/praxis/`, which is the worktree's shared git-common-dir. The directory held one claim event for WI-V2B and an empty claims directory.

I confirmed that the directory held only my artifacts, and then removed it. No tracked file and no other track's data was touched. The script now `cd`s in the current shell and refuses to run unless the fixture is its own repository root with its own `.git`, under /home/user/sprint-scratch.
