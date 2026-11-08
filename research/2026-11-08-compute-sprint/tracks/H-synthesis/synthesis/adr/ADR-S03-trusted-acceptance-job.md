# ADR-S03: Compute acceptance in a trusted job outside the candidate repository

- **Status:** Proposed — EXPERIMENTAL evidence
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track E finding E-F-02 and its fix, plus Track C CR-07. This is a candidate, not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`.

## Context

### The verdict does not detect fabricated evidence

Indy-init's `compute-acceptance-verdict.py` returned ACCEPTED (exit 0) for a repository containing only a README (E-F-02, VERIFIED by Track E in a local fixture). The inputs were:
- 118 script-written artifacts, each claiming PASS for `echo fabricated`;
- the real baseline, with 108 P0 requirements;
- the real rehearsal-005 approvals.

The verifier checks internal consistency only. Its trusted inputs are not independent:
- In rehearsal-005's `acceptance.sh`, `--evidence-manifest-sha256` is the stdout of the candidate's own `causa-acceptance ledger` step, in the same job.
- `--trusted-source-sha` is the candidate's own SHA.

### Rehearsal history

- The "computed verdict" introduced at R4 ended agents claiming acceptance (B-F-04, B-F-15; SUPPORTED, observational).
- It would not have caught a mistaken or dishonest producer (cross-track theme X-05).
- Over-claim moved down into the evidence layer: in R5, 13 of 22 spot-checked passing obligations were over-tagged (B-F-04).

### The guarantees the job would rely on are absent

- `main` on praxis is not protected, and nor is any branch of causa-acceptance-r10 (VERIFIED).
- There is no CODEOWNERS file in the 13 core repositories (VERIFIED).
- The agent's token is reportedly admin (SUPPORTED, from the R7 audit). Source: E-F-07.

### A control that works already exists

Praxis 3.25.0 with Dokimos 0.11.1 in attested mode refuses equivalent forgeries: an untrusted key, a missing receipt, a failing receipt, or a policy change (E-F-06, VERIFIED, 17/17 regression cases).

The acceptance tooling that lacks this property lives in Indy-init's 39k-line parallel toolchain (C-F-12).

## Decision (proposed)

1. Run acceptance in a repository and workflow that the candidate's agent cannot write to:
   - a protected branch;
   - CODEOWNERS on the workflow;
   - a branch-restricted environment.
2. In that job, produce evidence by running the test suites at the candidate SHA. Do not consume candidate-produced result files or candidate-printed digests.
3. Sign the resulting manifest or receipt with a key the agent cannot reach. Prefer the existing Dokimos attested-receipt path (E-F-06) over extending the Indy-init verifier (C CR-07).
4. Until this exists, label every rehearsal verdict "self-produced evidence; verifier checks consistency only".

## Consequences

**Expected:**
- Fabricated or over-tagged evidence can no longer produce ACCEPTED.
- "Accepted" becomes a unit that a cost-per-accepted-requirement metric can use (theme X-13).

**Costs** (ESTIMATE, not measured):
- One more repository or environment.
- A key ceremony.
- Re-running the suites in the trusted job: browser suites are 28–51% of CI step time (A-F-13), so acceptance gets slower.

**Prerequisites:**
- Branch protection and credential separation (E-F-07). Without them, the agent could change the trusted workflow itself.
- E-F-04: protected policy is currently read from local refs. Server-side verification is needed for the same reason.

**Interaction with ADR-S04:** the trusted job is itself governance machinery, so it must pass the pre-T0 dry run.

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| E-F-02 | VERIFIED (E, local fixture) | V2 pending — highest-priority verification item |
| E-F-06 | VERIFIED (E) | V2 pending |
| E-F-07 | SUPPORTED with VERIFIED parts (E) | V2 pending; rulesets not readable |
| E-F-04 | VERIFIED (E; documented limit) | V2 pending |
| B-F-04, B-F-15 | SUPPORTED (B) | none |
| C-F-12 | SUPPORTED (C) | none |

Files: `E-security/findings.json`, `E-security/data/E-X10-indy-fabricated-acceptance.json`, `E-security/scripts/indy_fabricated_acceptance.py`, `B-forensics/findings.json#B-F-04`, `C-architecture/complexity-reductions.json#CR-07`. Matrix themes X-04, X-05, X-10, X-18.

## Open questions

1. Does `requirements-compiler verify-plan`, the second check in rehearsal-005 that E did not test, catch the fabricated bundle? If it does, E-F-02's severity drops for R5. Its inputs are also candidate-produced.
2. Do org-level rulesets protect these branches in a way the branches API does not show (E-F-07 limitation)?
3. Can a Dokimos attested receipt express the obligation-level detail Indy-init's ledger carries (108 P0 requirements, G0–G9 gates)?
4. How much time does the trusted re-run add to a 420-minute window? This is NOT TESTED.
5. How should the verifier key be isolated from the agent's OS user? E-F-06 ran the verifier daemon as the same user.
