# REPORT.md — Track E: Security and Governance (E-001, 2026-11-08)

> Committed by RD-000 from E-001's final hand-back text. The harness refuses report-file writes by subagents (DECISION-LOG D-010). Worker final commit: `4d513a9`.
>
> **Outputs:**
> - `findings.json`
> - `scripts/`: `wf_audit.py`, `indy_fabricated_acceptance.py`, `secret_scan.py`, `supply_chain.py`, `bypass-cases.sh`, `nx1-installed.sh`, `upstream-rel001/`
> - `tests/`: 19 passing
> - `data/`: `E-X01`, `E-X02`, `E-X03`, `E-X10`, workflow and supply-chain audits, redacted secret scan, flag survey, branch-protection, prompt-injection scan

## Scope and method
**Environment.** Every bypass attempt ran against local fixture repositories under `/home/user/sprint-scratch/E/`. The tools were built from source in scratch copies:

- Praxis 3.25.0 (12bf995)
- Dokimos 0.11.1 (fecbe0c)
- Ordo sde (db6d39e)
- Indy-init dae2347 (full clone)

**GitHub access.** Read-only `list_branches` calls only. Nothing was pushed, dispatched or changed. Repository content was treated as untrusted data.

**Static audits:**

| Audit | Coverage |
|---|---|
| CI workflows | 155 workflow files |
| Supply chain | 23 repositories |
| Secrets | 128,562 history blobs across 59 repositories; all values redacted |
| Prompt injection | keyword scan |

The scans also covered the two private repositories added mid-sprint: causa-acceptance-r10 and indy-init-audits.

**Classification.** VERIFIED means reproduced here. SUPPORTED means based on code or document reading.

## Executive summary
1. **Completion is self-declared across the ecosystem (E-F-01, High, VERIFIED).**
   - None of the 45 surveyed `ros.json` files enables verified completion.
   - In default mode, `praxis work complete` accepts any existing file as test evidence. I used `/etc/hostname`, and afterwards `verify` and `work validate` both pass.
2. **Rehearsal acceptance can be fabricated by the party being judged (E-F-02, High, VERIFIED).**
   - Indy-init's `compute-acceptance-verdict.py` returned ACCEPTED (exit 0) for a repository containing only a README.
   - The inputs were 118 script-written evidence files claiming PASS for commands that never ran, plus the real baseline (108 P0) and the real rehearsal-005 approvals.
   - The script treats the evidence-manifest digest as an independent pin. In rehearsal-005's `acceptance.sh`, that digest is printed by the candidate's own tool, in the same job, in the candidate's own repository.
3. **The "protected branch" that every control relies on is not protected (E-F-07, High, SUPPORTED with VERIFIED parts).**
   - VERIFIED: GitHub reports praxis `main` and every listed causa-acceptance-r10 branch as `protected=false`.
   - VERIFIED: there is no CODEOWNERS file in praxis, ordo, Indy-init or rehearsals 001–010.
   - SUPPORTED, from the R7 audit: the agent's GitHub token is admin on every repository, and the agent holds the authorization signing key.
4. **Praxis's evidence-binding and attested-mode controls work (E-F-06, Info, VERIFIED).**
   - The REL-001 gate script ran unchanged on 3.25.0, and all 17 cases matched. This refreshes the stale 3.19.0 results.
   - What remains open is manipulation of local state:
     - deleting the claim store (E-F-03);
     - moving local refs or rewriting history (E-F-04, a documented limit);
     - "verified" completion with zero evidence in unattested mode (E-F-05).

## Bypass matrix (Praxis 3.25.0 / Dokimos 0.11.1)

| Case | Attempt | Result |
|---|---|---|
| GATE-1/2 | Failing-run file or unrelated file cited as evidence | Refused `EVIDENCE_UNRECOGNIZED` |
| GATE-3U | Forged validation result, no matching event | Refused `EVIDENCE_UNRECORDED` |
| GATE-3 | Forged result plus forged event (non-attested mode) | **Succeeded** (documented) |
| GATE-4 / GATE-5 | `validate-run -- false` / `-- true` | Refused `EVIDENCE_NOT_PASSED` / **succeeded** (the agent chooses the test command) |
| A1 | Forged store evidence in attested mode | Refused `RECEIPT_MISSING` |
| A2 / A2B | Self-signed receipt / own key under the trusted key ID | Refused `RECEIPT_UNTRUSTED_KEY` / `RECEIPT_INVALID_SIGNATURE` |
| A3 | Genuine failing receipt (completion while the gate is red) | Refused `RECEIPT_NOT_PASSED` |
| A5 / A6 | Committed weaker `ros.json` / own authority trusting own key | Refused `POLICY_CHANGED` / `UNTRUSTED_AUTHORITY` |
| NX-1 | Default policy, `/etc/hostname` cited as tests | **Succeeded** |
| NX-2a / 2b | Claimed item, plain complete / same after deleting the claim store | Refused `VERIFIED_COMPLETION_REQUIRED` / **succeeded** |
| NX-3 / NX-4 | Committed policy weakening / same plus `update-ref origin/main` | Refused `POLICY_CHANGED` / **succeeded** |
| NX-5a / 5B | Keyless authority under attested policy / weakened policy, moved `origin/main` and forged evidence | Refused `ATTESTATION_REQUIRED` / **succeeded as "verified"** |
| NX-6a / 6B | No remote: weakening commit / orphan-root history rewrite | Refused `POLICY_CHANGED` / **succeeded as "verified"** |
| NX-7 | Unattested mode, authority requiring no validations or evidence | **Succeeded as "verified"** (labelled `unattested`) |
| NX-8 | Evidence from revision A cited at revision B | Refused `HEAD_MISMATCH` / `ARGUMENT_MISMATCH` |
| NX-9 | `queue.json` status hand-edited to complete | **Undetected** |
| NX-10 | Agent records an owner approval as a human actor | Accepted, labelled `authenticity: unattested` |
| E-X10 | Fabricated Indy-init evidence bundle | **ACCEPTED** |

All refusal codes carry the `PRX.COMPLETION.` prefix.

**Totals:** 15 refused, 11 succeeded.

**Not tested:**
- Completion while a live GitHub check is red (no permission to act on GitHub).
- A requirement with no trace (requirements manifest). A safety classifier stopped the draft script; the partial file was deleted and not regenerated.
- Isolation of the verifier key from the agent's OS user.

## Findings

### E-F-01 — High, VERIFIED: default completion accepts arbitrary files as evidence
- **What happens.** Plain `work complete` checks only that the required evidence types are named and that the paths exist.
  - Paths outside the repository are allowed.
  - Nothing is executed.
  - Nothing is bound to a revision.
- **Scope.** None of the 45 surveyed `ros.json` files sets `requireVerifiedCompletion`, `requireAttestedEvidence` or `trustedVerifierKeyIds`.
- **Existing guard.** The durable-checkpoint guard applies only when tracked files changed. Even then it requires a commit, a push and a checkpoint, not a test run.
- **Reproduce.** `scripts/nx1-installed.sh`; `bypass-cases.sh` case NX-1; `data/flag-survey.txt`.
- **Fix.**
  1. Enable attested verified completion, starting with the repositories that feed acceptance.
  2. Until then, label plain completions "self-declared" wherever they appear.
  3. Reject evidence paths outside the repository, and record a digest and commit for each evidence file.

### E-F-02 — High, VERIFIED: Indy-init acceptance accepts fabricated evidence
- **What happens.** The verdict tool checks digests and fields for internal consistency only. It cannot tell whether a command ran.
- **Why the trusted inputs are not independent.** In rehearsal-005, `acceptance.sh` feeds two values to the tool as trusted inputs:
  - `manifest_sha`, printed by the candidate's own `causa-acceptance ledger` step;
  - the source SHA.

  The workflow, the pins and the producing tool all live in the candidate repository.
- **Result.** A README-only repository was ACCEPTED. This extends cohort-based-engineering's finding that Rehearsal 2's acceptance was self-declared to the "computed" verdicts of later rehearsals.
- **Reproduce.** `scripts/indy_fabricated_acceptance.py`.
- **Fix.**
  1. Compute acceptance in a repository and job the candidate's agent cannot write to, on a protected branch, with a branch-restricted environment.
  2. Derive evidence from test-runner output produced inside that job.
  3. Sign the manifest with a key the agent cannot reach.
- **Limit.** The second check, `requirements-compiler verify-plan`, was not tested.

### E-F-03 — Medium, VERIFIED: the claim guard can be deleted
- **What happens.** After a claim, plain completion is refused with `VERIFIED_COMPLETION_REQUIRED`. After `rm -rf <git-common-dir>/praxis/claims/ID`, it succeeds.
- **Fix.** Make the guard check the tracked event log for a claim, not only the local store.

### E-F-04 — Medium, VERIFIED (documented limit): protected policy is read from local refs
- **What happens.** A committed policy weakening is refused. But either of these defeats it:
  - `git update-ref refs/remotes/origin/main HEAD` (NX-4, NX-5B);
  - an orphan-root history rewrite in a repository with no remote (NX-6B).
- **Missing mitigation.** I found no implementation of the host-side audit the docs prescribe.
- **Fix.**
  1. Verify completion server-side, against the remote's protected branch.
  2. Implement the host-side audit:
     - compare receipt key IDs with the host's verifier;
     - check which authority file was used;
     - reject agent commits that change `ros.json`.

### E-F-05 — Medium, VERIFIED: zero-evidence "verified" completion in unattested mode
- **What happens.** The caller supplies the authority file. An authority requiring no validations and no evidence produces:
  - a Dokimos-accepted completion with empty `evidenceDigests`, labelled `unattested`;
  - a "verified completion" commit.

  GATE-5 (`validate-run -- true`) also verifies, because the agent chooses the command.
- **Fix.**
  1. Read the required validations from protected policy, not from the caller's authority, or refuse an authority that requires nothing.
  2. Surface "unattested" wherever "verified" is displayed.

### E-F-06 — Info, VERIFIED: existing controls still work on 3.25.0
- **Result.** All 17 gate-v319 cases matched; see the bypass matrix.
- **Recommendation.** Add the gate script to Praxis release CI.

### E-F-07 — High, SUPPORTED (parts VERIFIED): no merge gates, and the agent's credential is reportedly admin
- **VERIFIED.**
  - praxis `main` and all causa-acceptance-r10 branches report `protected=false`.
  - None of the 13 core repositories has a CODEOWNERS file.
- **SUPPORTED** (indy-init-audits, R7 sub-audit 3).
  - The agent's GitHub App token is admin.
  - Agent merges appear under the owner's login.
  - There are no rulesets.
  - The agent holds the P-256 signing key and chooses its own trust store.
- **Consequence.** E-F-02, E-F-04 and every pin in the workflows are agent-controllable.
- **Fix.**
  1. Rulesets on `main`: required PR, required human review, required trusted checks, no force-push, no bypass for the agent.
  2. CODEOWNERS for `.github/`, `ros.json`, `acceptance/` and `tools/`.
  3. A separate agent identity without admin rights.
  4. Keys held in branch-restricted environments.
- **Limit.** The branches API flag may not reflect every ruleset.

### E-F-08 — Medium, SUPPORTED: owner attestations rest on the review login alone
- **What happens.** `ReviewAttestations.fs` accepts any APPROVED, CHANGES_REQUESTED or DISMISSED review and identifies the reviewer by `user.login` only. If the agent's token acts as the owner's user, the agent satisfies the owner attestation.
- **Fix.** Require a signature the agent cannot produce, or reviews from an account no agent token can act as.

### E-F-09 — Medium, SUPPORTED: release provenance binds only the repository
- **What happens.**
  - `native-release.yml` can be dispatched on any branch with write tokens, then attests and publishes.
  - Consumers verify with `gh attestation verify --repo` and no workflow or ref constraint.
  - `NuGet/login@v1` is pinned by tag while holding an OIDC token that can be exchanged for a NuGet key. The same pattern appears in dokimos, aegis, fides, arca and vitium.
- **Fix.**
  1. Restrict publishing to `main` or tags through an environment.
  2. Add `--signer-workflow` and `--source-ref` to verify calls.
  3. Pin actions by commit SHA.

### E-F-10 — Low, VERIFIED: CI hygiene
- **Action pinning.** 821 action references are pinned by tag; only 38 by commit SHA.
- **Missing `permissions:` block.** `praxis-validation.yml` and Indy-init's `preflight-tooling.yml`.
- **Shell interpolation of inputs.** `${{ inputs.* }}` is placed directly into shell in rehearsal-006 acceptance, Indy-init live preflight and conditor remote workflows. These run on manual dispatch only, so exploiting them requires write access.
- **Well designed.** The privileged triggers: `praxis-reconcile-apply` builds from the trusted base commit, accepts same-repo PRs only, and passes the branch name through an environment variable.

### E-F-11 — Low, VERIFIED: hand-edited `queue.json` goes undetected
- **Fix.** Have `work validate` cross-check `queue.json` against the event log.

### E-F-12 — Low, VERIFIED: self-declared owner approvals are accepted
- **What happens.** Praxis accepts them but records `authenticity: unattested`.
- **Fix.** Consumers must require attested authenticity for owner and review evidence.

### E-F-13 — Low, VERIFIED: supply chain
- **NuGet.** There are no lock files anywhere, so transitive packages are not hash-pinned. Direct versions are exact; npm has lockfiles.
- **Installer.** Conditor and percepta CI run `curl …/main/install-native.sh | sh`. The installer comes from a branch that can change, and it checks assets only against a checksum file from the same release.

### E-F-14 — Info, VERIFIED: no live credential found
- **Result.** 264 pattern hits; all 49 that looked live were reviewed. Every one is a test fixture, such as a bare private-key header string or a synthetic token.

### E-F-15 — Info, SUPPORTED: no prompt injection found
- **Result.** The keyword scan found no content instructing agents to override instructions or exfiltrate data.
- **Related.**
  - The R7 audit recorded agent isolation that was enforced only by instructions.
  - In this session the GitHub tools refused a repository outside the allowlist (dokimos).

### E-F-16 — Info, VERIFIED: what causa-acceptance-r10 is
- **What it holds.** A live-persistence data store written by a dedicated GitHub App (`causa-acceptance-r10[bot]`); no acceptance tooling.
- **Assessment.** The separate app identity is a good control, but the branches are unprotected.

## Remediation priority
1. **Merge gates and identity (E-F-07).** Rulesets, CODEOWNERS and a non-admin agent identity are prerequisites for every other control.
2. **A trusted acceptance job (E-F-02, E-F-08).**
3. **Attested verified completion, enabled and verified server-side (E-F-01, E-F-03, E-F-04, E-F-05).**
4. **Provenance and CI pinning (E-F-09, E-F-10, E-F-13).**

## Limitations
- No live GitHub enforcement was tested, and no rulesets or repository settings were read.
- The verifier ran as the same OS user as the agent.
- The requirement-trace case is incomplete.
- The secret and prompt-injection scans are pattern-based only.
