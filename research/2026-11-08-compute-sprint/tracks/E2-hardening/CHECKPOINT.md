# E2-hardening checkpoint (final)

Status: COMPLETE (all three experiments run; final patched suite run). EXPERIMENTAL; nothing pushed/applied.

- Scratch: /home/user/sprint-scratch/E2/praxis (clean 12bf995, baseline build + suite), /home/user/sprint-scratch/E2/praxis-e2
  (branch e2-patch: 9d5209b claim guard + queue integrity; 946bb44 evidence path + ratchet-compliant CLI wiring), tac/ (SPR-E2-03 simulation).
- Builds: 5 Release builds of Praxis.slnx, all 0 warnings / 0 errors, 3m–4m10s each (raw/test-suite/build-*.txt).
- Baseline suite 2513 tests: 2511 pass / 2 fail (real-Dokimos attested e2e), 2035 s.
- Final patched suite (build 5) 2522 tests: 2513 pass / 9 fail, 1647 s; 7 newly failing, all assert a clean
  `git status` right after `work claim` (invariant I8); the 2 baseline failures persist; 9 new E2 tests pass.
- SPR-E2-01 VERIFIED (A1/A1b refused CLAIM_RECORD_MISSING; A2 UNRECORDED_COMPLETION; controls pass; FP 0/43 repos).
  Deviations: DIRTY_WORKTREE fix in verification cleanliness; CLI ratchet forced moving code out of Program.fs.
- SPR-E2-02 VERIFIED (B1–B4 refused OUTSIDE_REPOSITORY; P1/P1b/P2/P3 as predicted). Deviation: bindings path moved
  to .ros/work/evidence-bindings.jsonl (attribution finding at .ros/evidence/).
- SPR-E2-03 VERIFIED locally (T1–T8 refused/EACCES/ignored; P1 ACCEPTED; N1/N2 FAILED); GitHub-side NOT TESTED.
- Reproduce: harness/spr-e2-0{1,2,3}.sh; python3 -I harness/build_reports.py . regenerates experiments/findings.
