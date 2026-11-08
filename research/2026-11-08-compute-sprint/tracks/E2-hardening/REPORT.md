# E2-hardening report (E2-001, 2026-11-08)

> Committed by RD-000 from E2-001's final hand-back text (D-010).
> - **Worker final commit:** `811d8d9`.
> - **Status:** EXPERIMENTAL. Patches exist only as files and in scratch clones. Nothing was pushed or applied, and no PR, issue, comment or workflow trigger was created.
> - **Repository check:** `/home/user/praxis` was confirmed clean at 12bf995 afterwards.

**Summary.** All three prototypes met their preregistered criteria. However, the Praxis claim-guard fix conflicts with a deliberate Praxis invariant: claiming must not change the tracked tree. Seven existing tests encode that invariant.

## Setup
- **Scratch clones:**
  - `/home/user/sprint-scratch/E2/praxis`: clean 12bf995, used for the baseline build and suite.
  - `/home/user/sprint-scratch/E2/praxis-e2`: branch `e2-patch` (`9d5209b`, `946bb44`).
- **Builds:** `dotnet build Praxis.slnx -c Release` ×5, run serially. Each finished with 0 warnings and 0 errors, in 3:01–4:10.
- **Supporting tools:**
  - Dokimos 0.11.1 (fecbe0c) and Ordo (db6d39e), binaries copied from Track E's scratch build.
  - Indy-init dae2347, cloned from V2's full-history clone, because `/home/user/Indy-init` is shallow.
- **Fixture isolation:** every Praxis command ran under `/home/user/sprint-scratch/E2/fixtures/`, and each fixture has its own `.git`. The `harness/lib.sh` functions `px` and `assert_fixture` refuse to run anywhere else, and the check is repeated after `cd` in the same subshell.

## Existing test suite (Praxis.Tests, full run, real Dokimos enabled)

| Build | Tests | Passed | Failed | Wall time |
|---|---|---|---|---|
| Baseline | 2513 | 2511 | 2 | 2035 s |
| Final patched (build 5) | 2522 (9 new) | 2513 | 9 | 1647 s |

- **Still failing from baseline (2):** two real-Dokimos attested end-to-end tests.
- **Newly failing (7):** every one asserts `git status --porcelain == ""` immediately after `work claim`, which is invariant I8. They are:
  - six attested-completion tests: C3b, genuine passing receipt, UDS verifier, fails closed without attest, F4 e2e, REL-GATE-003;
  - one validation-evidence CLI test.

  The full list is in `raw/test-suite/comparison.json`.
- **Not affected:** no failure relates to the evidence-path fix, and no test is newly passing.
- **Passing:** the 9 new E2 tests and the 9 CLI-ratchet tests.
- **Timings:** indicative only, on a 4-vCPU shared host.

## SPR-E2-01: claim guard and queue integrity (E-F-03, E-F-11). F#. VERIFIED

The fix is in `patches/praxis-claim-guard-queue-integrity.patch`. `praxis-e2-combined.patch` is the full, ratchet-compliant diff.

**What it changes:**
- **Tracked claim marker.** `work claim` also appends a `work.claim.recorded` marker to the tracked `.ros/events/events.jsonl`. The marker contains no token. Previously a claim left no tracked trace.
- **Guard on plain completion.** `work complete` reads the tracked log from both the working tree and the HEAD blob. If the log shows a claim with no `work.completion.verified`, it refuses with `PRX.COMPLETION.CLAIM_RECORD_MISSING`, whatever the claim store says.
- **Queue cross-check.** `work validate`, `backlog-validate` and `validate` flag a queue row marked `complete` that has no tracked `work.completed` or `work.completion.verified`, reporting `PRX.QUEUE.UNRECORDED_COMPLETION`.
- **Cleanliness rule.** A tracked log that differs from HEAD only by markers counts as clean for verification. The verified-completion metadata commit records the marker.

**Attacks** (`raw/spr-e2-01-{baseline,patched}.jsonl`):

| Case | Baseline | Patched |
|---|---|---|
| A1: E NX-2b / V2 case B (delete the claim dir, then plain complete) | exit 0 | exit 3, CLAIM_RECORD_MISSING |
| A1b: claim committed; claim store and working-tree marker deleted | exit 0 | exit 3, CLAIM_RECORD_MISSING |
| A2: E NX-9 (hand-edited `queue.json`) | valid, exit 0 on all three commands | exit 1, UNRECORDED_COMPLETION on `work validate`, `backlog-validate` and `validate` |

**Controls:**
- **C1:** claim → validate-run → complete-verified with real Dokimos works.
- **C1b:** the same flow with no commit after the claim works, and the marker lands in the metadata commit.
- **C2:** an unclaimed item completes normally.
- **C3:** a legitimately completed item produces no finding.
- **C4:** a read-only scan of 43 local repositories (1,881 rows marked complete) flags 0 of them.

**Residual risk:**
- **A1c is still open.** A marker that was never committed can be deleted together with the claim store, and plain completion then succeeds (exit 0, as predicted).
- **Coordinated forgery passes.** A forged `work.completed` line or a history rewrite is not caught. The fix moves the bypass into reviewable tracked state; it does not create a trust root.
- `praxis verify` is unchanged.
- Backlog `abandoned` writes no event in 3.25.0, so abandoned rows cannot be cross-checked.

**Deviations from the protocol:**
- The first build broke attested completion (`PRX.VALIDATION.DIRTY_WORKTREE`). Fixed by the cleanliness rule above.
- The CLI boundary ratchet forced the wiring out of `Program.fs`, which now has zero net lines added.

**Owner decision needed:** choose one.
- Accept a tracked claim marker and update the 7 I8 tests.
- Commit the marker at claim time. This would also close A1c.

## SPR-E2-02: evidence-path hardening (E-F-01). F#. VERIFIED

The fix is in `patches/praxis-evidence-path.patch`.

**What it changes:**
- **Default on.** Plain `work complete` resolves each evidence path, including `..` and every symlinked component. Paths outside the repository root are refused with `PRX.EVIDENCE.OUTSIDE_REPOSITORY` (exit 1), before any gate, lock or state change.
- **Opt-out.** Explicit `workProtocol.allowExternalEvidence: true`.
- **Bindings.** Each evidence file gets a record in `.ros/work/evidence-bindings.jsonl` with its sha256, the HEAD commit, and whether the file is committed at HEAD.

**Attacks:** all refused. Baseline accepted all four.

| Case | Attack |
|---|---|
| B1 | `/etc/hostname` |
| B2 | `../` ×12 traversal |
| B3 | In-repo file symlink to `/etc/hostname` |
| B4 | In-repo directory symlink to `/etc` |

**Controls:**
- **P1:** a real unittest log is accepted. Its sha256 equals `sha256sum`, its commit equals HEAD, and it is marked not committed at HEAD, because `praxis init` git-ignores `logs/`.
- **P1b:** a committed log is accepted and marked committed.
- **P2:** with the opt-out, `/etc/hostname` is accepted and still recorded, marked outside the repository.
- **P3:** a missing path gives the old message.

**Existing-test impact:** none.

**Residual risk:**
- The binding proves which bytes were cited at which commit, not that the tests ran. A fabricated in-repo log is still accepted.
- The opt-out lives in an agent-editable `ros.json` (E-F-04 class).
- The binding is written just before the completion transaction, not inside it.

**Deviation from the protocol:** the bindings path moved from `.ros/evidence/` to `.ros/work/` to avoid an attribution finding.

## SPR-E2-03: trusted acceptance design (E-F-02). Python. VERIFIED for the local mechanism only

The design is in `harness/trusted_acceptance/` and `harness/spr-e2-03.sh`.

**How it works:**
- **Separation.** The verifier repo is owned by root, with an Ed25519 key in a 0700 directory. The candidate repo is owned by uid 65534 (nobody).
- **Verifier job.** It clones the candidate at the commit the operator pins and runs black-box checks from its own plan. It calls the candidate as uid 65534 via `setpriv`, judges the output itself, signs every evidence entry, then computes and signs the manifest digest.
- **Verdict.** Only evidence signed with the pinned key is accepted. The verifier recomputes the digest itself; a digest supplied by the caller is ignored.

**Attacks** (`raw/spr-e2-03.jsonl`):

| Case | Result |
|---|---|
| T1, T2: E's and V2's own fabrication scripts (Indy's verifier still returns ACCEPTED for both) | REFUSED (no verifier signature) |
| T3: bundle forged and signed by the candidate | REFUSED (bad signature) |
| T4: candidate reads the key or writes the verifier's output | EACCES on both |
| T5: replay to another commit | REFUSED |
| T6a, T6b: tampered entry, with and without a re-hashed manifest | REFUSED |
| T7: caller-supplied digest | Ignored; verdict unchanged |
| T8: dropped entry | REFUSED |

**Controls:**
- **P1:** a correct candidate is ACCEPTED.
- **N1:** a buggy candidate is FAILED.
- **N2:** a candidate that prints "PASS" and tries to read the key is FAILED.
- 5 unittest tests pass.

**What the local simulation cannot prove (NOT TESTED):**
- GitHub environment protection, branch rulesets, required reviewers, OIDC and secret scoping.
- Runner, container and network isolation.
- That the agent's token cannot reach the verifier repo. E-F-07 indicates it currently can.
- Scaling from a 4-check toy plan to the real 108-requirement baseline.
- Root can bypass everything in this simulation.

## Findings

| ID | Finding | Class |
|---|---|---|
| E2-F-01 | Claim-store deletion bypass refused | VERIFIED |
| E2-F-02 | Hand-edited queue completions detected, with 0 false positives | VERIFIED |
| E2-F-03 | Out-of-repo evidence refused; in-repo evidence bound to digest and commit | VERIFIED |
| E2-F-04 | Claim marker conflicts with 7 existing I8 tests | VERIFIED |
| E2-F-05 | Verifier-signed flow refuses the fabricated bundles Indy accepts | VERIFIED (local only) |
| E2-F-06 | Protection against an agent with general write access | NOT TESTED |

## Files
- `protocols/`: SPR-E2-01 to -03, each committed before its experiment.
- `patches/`: `praxis-claim-guard-queue-integrity.patch`, `praxis-evidence-path.patch`, and `praxis-e2-combined.patch`. The combined patch is canonical; the other two are incremental.
- `harness/`: shell, Python and unittest.
- `raw/`, including `raw/test-suite/`.
- `experiments.json` and `findings.json`, both generated from `raw/` by `harness/build_reports.py`.
- `CHECKPOINT.md`.
