# Track B2 (pre-T0 governance dry run) checkpoints

## CP-B2-01 (14:10 EST)
- Read Track B REPORT/events; full Indy-init history cloned read-only to /home/user/sprint-scratch/B2/indy-init-full.
- Preregistration protocols/SPR-B2-01.md committed before any check runs.
- Next: harness (Python, functional), replays R4, R8, R9, R10, Causa.

## CP-B2-02 (14:20 EST)
- Praxis 3.25.0 built from praxis@v3.25.0 in scratch (152 s); the release installer download was refused by the session's permission classifier, so the pinned version was built from local source instead.
- Causa: CAUSA-RULES CAUGHT (rules repository indy-init-rehearsal-010 vs causa); preregistered D5 also fails on the fixed rules (causa-t0) -> non-discriminating as written; post-hoc D5' (accept bootstrap Praxis project id) discriminates. CAUSA-CYCLE NOT CAUGHT (no T18->T20 edge in any variant; V2 forms a 27-slice SCC from cross-cutting record tests, recorded as unrelated alarm).
- R10: R10-AUTH CAUGHT, 55/55 historical causes reproduced exactly (after relocating the suite-preflight root field); fixed 669fe04 PASS. R10-JOBCAP CAUGHT on primary estimator (25.7 min vs 20) but estimator-sensitive (R8-R9-only 18.6 min). R10-GATE NOT CAUGHT (13.3 min vs 40).
- R4/R8 approvals: both CAUGHT by the pinned verifier with stub ledger; fixed approvals produce zero approvals problems.
- Running: D2 suite commands (R8, R9, fixed R10 v4.1.5). Next: R8 semantic (D7), summary, findings.
