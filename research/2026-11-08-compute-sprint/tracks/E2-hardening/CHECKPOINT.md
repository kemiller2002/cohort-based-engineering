# E2-hardening checkpoint

- 14:17 start. Scratch clone /home/user/sprint-scratch/E2/praxis @12bf995 (baseline build + full baseline test run);
  patched worktree /home/user/sprint-scratch/E2/praxis-e2 (branch e2-patch).
- Baseline Release build: 4m10s, 0 warnings / 0 errors.
- SPR-E2-01: protocol committed; patch built (3m20s); 7 new unit tests pass; harness run on both builds
  (raw/spr-e2-01-{baseline,patched}.jsonl): A1/A1b refused CLAIM_RECORD_MISSING, A2 flagged UNRECORDED_COMPLETION,
  A1c (uncommitted marker) still bypasses as predicted; controls C1–C3 pass; C4 FP scan 0 flagged.
- SPR-E2-03 prototype: all T1–T8 refused as preregistered, P1 ACCEPTED, N1/N2 FAILED (raw/spr-e2-03.jsonl); 5 unittest pass.
- SPR-E2-01 deviation: subset "claim" showed 4 attested-completion tests failing with PRX.VALIDATION.DIRTY_WORKTREE (the uncommitted tracked marker); fix in progress (verification cleanliness tolerates a marker-only log diff).
- Next: rebuild with SPR-E2-01 fix + SPR-E2-02, full patched suite, SPR-E2-02 harness.
