# Reliability readiness (REL-001 follow-ups F1–F6)

Evaluated 2026-10-20 against praxis main `4ade512` (v3.17.0), dokimos main `04b5f85` (0.7.0) and ordo `bb43c26`
(1.17.0). Released linux-x64 binaries were downloaded and checked against the sha256 pins in the run-02 gate report.
Run-02 data were read from a read-only snapshot of the run-02 branch at `c8da63f`. Nothing on that branch was changed.

Machine-readable result: [`readiness-report.json`](readiness-report.json) (`cbe.reliability-readiness/1`).
## Verdict
**optimizedWorkflowReady: false. attestedConfigurationReady: false.**

| Condition | Mandatory | Status |
|---|---|---|
| F1-attested-forgery-refused | yes | PASS |
| F1-agent-cannot-fabricate-attestation | yes | **FAIL** |
| REL-GATE-003-resolved | yes | **FAIL** |
| F2-agent-attribution | yes | PASS |
| F3-clean-commit-identity | yes | PASS |
| F4-derived-completion-args | yes | PASS |
| F4-single-test-run | yes | PASS |
| F5-price-table | no | PASS |
| F6-rollout-gate | yes | **FAIL** |
| regression-tests | yes | PASS |

## What was executed
- **Gate re-run.** `gate-evidence-binding-v317.sh` (copied from the snapshot) ran in a scratch directory on the
  released binaries. Output: `evidence/results-v3.17.0-rerun.jsonl`. It matches the snapshot case for case:
  - Attested mode refuses all four forgeries: GATE-A1 (forged result and event), A2 (self-signed receipt),
    A2B (wrong key under the trusted keyid) and A3 (genuine failing receipt). A4 (genuine pass) verifies clean.
  - Non-attested GATE-3 still verifies a forged result.
- **Trust-root probes.** `scripts/probes.sh` uses `gate-lib.sh`, which is the gate script without its dispatcher.
  Output: `evidence/probes-v3.17.0.jsonl`.
  - PROBE-1 (control): a keyless authority under `requireAttestedEvidence` is refused with `ATTESTATION_REQUIRED`.
  - PROBE-2: `requireVerifiedCompletion` alone accepts forged store evidence, so REL-GATE-003 is still open.
  - PROBE-3: the agent commits a `ros.json` that drops `requireAttestedEvidence`, and forged evidence then verifies.
    Praxis reads the policy from the worktree it is completing.
  - PROBE-4: with the policy unchanged, a receipt the agent signed itself verifies when the authority file pins the
    agent's own key. The authority path is chosen by the caller (`--authority` or `PRAXIS_COMPLETION_AUTHORITY`).
- **Regression tests** (.NET SDK 10.0.402 + runtime 8.0 via `dotnet-install.sh`): Praxis.Tests 2330/2330 against the
  real Dokimos (`evidence/praxis-tests-4ade512.txt`); Dokimos 4/4, 322/322, 143/143 (Cli needs a Git checkout).

## Run-02 arm D (echelon-optimized, 10 observations)
- **F3 identity.** Every completing workspace has a consistent identity, a clean worktree and a `.ros/`-only diff
  from the verified commit. In U6, the agent-1 workspace that did not complete reports `IDENTITY_VIOLATED`
  because it holds source changes it never pushed.
- **F4 overhead.** Each run made 1 `verify` call, 1 verifier test run, 0 `validate-run` calls, and completed on its
  first attempt with `--id --token` only.
- **F2 attribution.** Every agent was attributed through `--agent-binding`, with 0 unattributed observations and
  balanced conservation.
- **Fabrication.** No run shows an attempt, but the harness could not have detected PROBE-3/4: host files and the
  verifier share the agent's uid, X6 compares host-file digests only, and no check compares receipt keyid with `verifier.keyId`.

## Blockers and next actions
1. **REL-GATE-004 (draft, P1).** Enforce the trust root (policy, authority and key) outside the agent's control.
   Draft: `/home/user/wt/worker-a/inbox-drafts/2026-10-20-REL-GATE-004-attested-trust-root-not-enforced.md`,
   for praxis `.praxis/inbox/documents/`.
2. **REL-GATE-003.** Queued in Praxis and not yet claimed. PROBE-2 is its regression check.
3. **F6 / PRAXIS-REL-006.** Still `captured`. Gate items 5–7 are not evidenced.
4. **Run-02 harness.** Add post-hoc checks for the receipt keyid, the effective authority path and `ros.json`
   edits. Run the verifier under a separate uid.
5. **Price table.** `research/pricing/` exists only on the run-02 branch. It is needed on main once that branch merges.

## Status update 2026-10-21 (after this evaluation)
This report evaluates Praxis 3.17.0 and Dokimos 0.7.0. Its statuses are not rewritten. Since then:
- **REL-GATE-003:** fixed in praxis#280 and released in Praxis 3.18.0.
- **REL-GATE-004** (`F1-agent-cannot-fabricate-attestation`): fixed in praxis#279 (`e29e49d2`), merged but not yet
  released. Results: 2350/2350 tests, PROBE-3 → `POLICY_CHANGED`, PROBE-4 → `UNTRUSTED_AUTHORITY`.
- **To flip either condition to PASS:** re-run `scripts/probes.sh` and the gate script, with the
  `trustedVerifierKeyIds` pin, on the released binary.
- **F6** (PRAXIS-REL-006 rollout gate) is still open.

## Status update 2026-10-21 (Praxis v3.19.0)
- REL-GATE-003 and REL-GATE-004 are **resolved on the release**. The v319 gate script (cohort #12) shows:
  - GATE-A5 (this report's PROBE-3) rejected with `POLICY_CHANGED`;
  - GATE-A6 (PROBE-4) rejected with `UNTRUSTED_AUTHORITY`;
  - GATE-A4 keyids matching the host verifier.
- Evidence: `../experiments/REL-001/gate/evidence/evidence-binding-repro-v3.19.0.jsonl` and `gate/gate-report.json`.
- **Remaining limit:** an agent that can rewrite `origin/HEAD`, `origin/main` or history still defeats the check.
- **F6** (PRAXIS-REL-006 rollout gate) remains open.
