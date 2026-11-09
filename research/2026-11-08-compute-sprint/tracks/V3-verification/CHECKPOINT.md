# V3-verification checkpoint

Worker V3-001 (independent verifier), parent RD-000, 2026-11-08. Status: **COMPLETE**. All 7 claim groups have a verdict.

| Claim | Verdict | Key recomputed value |
|---|---|---|
| A2-F-01/02 | VERIFIED | Seeded sample of 18 out of 58 R8 merges with `.ros` conflicts (seed 20261108). The SUT driver leaves 0 unmerged paths, loses 0 records, makes 0 duplicates, and the IDs and content equal the team merge in 36/36 files. |
| A2-F-03 | PARTIALLY VERIFIED | The drop, the active state and the `praxis validate` failure all reproduce. The brief says WI-0003 is "present in both parents", but it is present only in parent 2a4ae187 (SL-T12). |
| C2-F-07 | VERIFIED | 2 avoidable (v0.10.15, v0.10.17), 9 required (7 driven by Praxis/Ordo host tools), 2 with no catalog change. CON-343 is at ComponentDescriptors.fs:595-597. |
| C2-F-05 | VERIFIED | The signed statement is schema, systemId, version, releaseManifest.sha256 and the sorted contracts (ReleaseAttestation.fs:46-47, 149). |
| B4-F-05 | VERIFIED | No `--catalog` at dae2347:396-400. The jq gate checks blocked, blockingContradictions and transitions>0. The CI invocation hides the CommandEnvelope defect on R8. |
| B4-F-01 | VERIFIED | R8 v4.1.1 gives exit 3 (2 contradictions, 1 missing interface, 2 non-blocking missing decisions). v4.1.2 gives exit 0. |
| SPR-D2-01 | VERIFIED | My oracle agrees with D2's scores on 24/24 values. Token p = 2/70 = 0.0286, Holm 0.0857. |
| D2-F-05/06 | VERIFIED | p1, p2, q1 and q2 raise `NotSpecified` on every trap probe (13 and 7 probes). q1/q2 pass the D-001/D-002 controls and follow 0 planted values. |

## Where things are
- `verdicts.json`: one entry per claim, with every required field.
- `scripts/`: `v3guard.py` (refuses to run or mutate outside /home/user/sprint-scratch/V3), `conditor_releases.py`, `percepta_preflight.py`, `merge_replay.py`, `praxis_validate.py`, `d2_probes.py`, `ws_runner.py`, `d2_oracle.py`, `d2_stats.py`, `upsert_verdict.py`.
- `scripts/tests/`: 32 unittest tests, all passing (`raw/unittest.txt`). They include oracle validation against controls I wrote myself in `tests/controls/`.
- `raw/`: survey, replay and validate outputs, percepta reports, D2 scores and stats.
- Scratch, in /home/user/sprint-scratch/V3/: clones (r008, r010; unshallowed GitHub clones), percepta and praxis-src (my builds), pkgs, out, d2copies, controls, vt (validate worktrees).

## Reproduce (from /home/user/sprint-scratch/V3; S=<worktree>/scripts)
- `python3 -I $S/conditor_releases.py`
- `python3 -I $S/percepta_preflight.py` (needs percepta-bin/ built from /home/user/ext/percepta@4a53688)
- `python3 -I $S/merge_replay.py clones/r008 survey out/r008-survey.json`, then `sample ... 18 20261108`, then `replay ...`
- `python3 -I $S/praxis_validate.py clones/r010 d8447ed1... out/d8447ed1-driver/current.json vt validate`
- `python3 -I $S/d2_oracle.py orders out/d2-v3scores.json r1=/home/user/sprint-scratch/D2/ws/r1 ...`, then `d2_stats.py`
- `python3 -m unittest discover -s $S/tests -t $S/tests`

## Safety
I made no pushes, PRs or comments. Git mutation happened only in V3 scratch clones, guarded by `v3guard.mutating_git`, which checks the repo, its toplevel and its absolute git dir. No files under the D2/D2b/D2c workspaces changed during this session (find -newer check).
