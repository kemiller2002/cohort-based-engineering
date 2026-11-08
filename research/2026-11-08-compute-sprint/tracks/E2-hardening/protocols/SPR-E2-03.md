# SPR-E2-03 — Trusted acceptance design prototype (E-F-02)

Preregistered 2026-11-08 ~15:00 EST, before any prototype code. Python (the existing tool is Python).
Indy-init reference: tools/compute-acceptance-verdict.py at dae2347 (read-only); rehearsal-005
tools/acceptance/ci/acceptance.sh lines 66–70 and 111 pipe the manifest digest from the candidate's own `ledger` step
into `--evidence-manifest-sha256`.

## Root cause being addressed
The verdict tool checks internal consistency of candidate-produced JSON; its "trusted" manifest digest and source SHA are
supplied by the job that the candidate controls. Nothing binds an evidence entry to an execution the candidate could not
fake.

## Design under test (local simulation)
- Two local repositories under /home/user/sprint-scratch/E2/tac/: `candidate` (owned by uid 65534 "nobody", the
  candidate process) and `verifier` (owned by root, mode 0700 for its key directory).
- The verifier repo holds: the acceptance plan (requirement id → black-box check), the acceptance checks themselves,
  an Ed25519 signing key in `verifier/keys/` (0700 root), and the pinned public key.
- verifier job (`verifier_job.py`, runs as root): clones the candidate at an operator-pinned commit into a
  verifier-owned workspace, runs each check by invoking the candidate program as uid 65534 (setpriv) in a subprocess,
  judges the output in the verifier process, writes one evidence entry per requirement
  {schema, run_id, job_id, source_sha, requirement, check_id, command, exit_code, status, stdout_sha256, started/finished},
  signs every entry and the manifest it computes itself (Ed25519), into a root-owned output dir.
- trusted verdict (`trusted_verdict.py`): accepts only a manifest signed by the pinned verifier key, recomputes the
  manifest digest itself from the entry bytes (any caller-supplied digest is ignored), checks each entry signature, the
  pinned source SHA, run_id/job_id consistency, and that every plan requirement has a PASS entry. Verdicts:
  ACCEPTED / FAILED / REFUSED (untrusted or inconsistent evidence).

## Attack cases (all must be REFUSED, never ACCEPTED)
- T1: E's fabricated bundle (E-X10 shape: 118 `causa.acceptance-evidence/1` artifacts + manifest, digest from producer).
- T2: V2's fabricated bundle (V2 fabricate_acceptance.py shape).
- T3: candidate (uid 65534) fabricates a bundle in the new format and signs it with its own Ed25519 key.
- T4: candidate tries to read the verifier key and to write into the verifier output dir (expect EACCES).
- T5: genuine signed bundle for commit A presented for pinned commit B (replay).
- T6: genuine bundle with one entry edited (status FAIL→PASS or command changed) — signature mismatch.
- T7: genuine bundle with a caller-supplied (wrong) manifest digest argument — must be ignored, verdict unaffected.
- T8: entry dropped from the manifest (missing requirement) — not ACCEPTED.

## Positive / negative controls
- P1: correct small candidate (a CLI implementing the plan) → verifier job → ACCEPTED.
- N1: buggy candidate (one requirement wrong) → verifier job produces a signed FAIL → FAILED (shows the job judges).
- N2: candidate whose program tries to print a fake "PASS" and exit 0 for every call → judged by output, FAILED.

## Success criteria
T1–T8 not ACCEPTED (T1–T3, T5–T8 REFUSED with explicit reasons; T4 EACCES), P1 ACCEPTED, N1/N2 FAILED.
Unit tests (unittest) for pure functions pass. VERIFIED for the local mechanism if all hold; the GitHub-side properties
are NOT TESTED and listed as such.

## Stated in advance: what this simulation cannot prove
GitHub environment protection rules, required reviewers, branch rulesets, OIDC-bound secrets, runner isolation, that the
verifier repo/workflow is actually unwritable by the agent's token (E-F-07 says today it is writable), and that the
acceptance checks are adequate for the real 108-requirement baseline.
