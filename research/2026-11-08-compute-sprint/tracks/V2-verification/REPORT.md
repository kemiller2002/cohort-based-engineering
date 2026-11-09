# V2-verification report (worker V2-001, 2026-11-08)

> Committed by RD-000 from V2-001's final hand-back text (harness refuses subagent report-file writes; D-010). Worker final commit: `b7d5e24`.
>
> Outputs: `verdicts.json`, `CHECKPOINT.md`, `scripts/` (9 scripts + `test_v2.py`, 15 unittest tests passing, including an end-to-end run against the real verifier with a tamper check), `data/` (captured inputs and outputs for each verdict).

**Result:** of 13 claims, 12 VERIFIED and 1 PARTIALLY VERIFIED (B-F-03); none contradicted. The highest-consequence security claims (E-F-01, E-F-02, E-F-03) were each reproduced with my own build, fixtures and scripts.

## Incident (self-reported; clean-up checked by the Director)

The first run of the Praxis reproduction script had a bug: `cd` ran inside a command substitution, so the change of directory never took effect.

- **What happened:** `praxis` ran in the track's `scripts/` directory and created two things:
  - `scripts/.ros/`;
  - `/home/user/cohort-based-engineering/.git/praxis/`, holding one claim event for probe item WI-V2B and an empty claims directory.
- **Clean-up:** I checked that both held only my artifacts, then removed them. No tracked file and no other track's data was affected.
- **Fix:** the script now changes directory in the current shell. It refuses to run unless the fixture is its own repository root, with its own `.git`, under `/home/user/sprint-scratch`.
- **Director check (RD-000):** `.git/praxis` is absent, the working tree is clean, `git fsck` passes, and no stray `.ros` directories remain in any sprint worktree. The clean-up is accepted (DECISION-LOG D-015).

## Verdicts

| # | Claim | Verdict | Recomputed |
|---|---|---|---|
| 1 | B-F-02: R2 recomputes INVALID | VERIFIED | INVALID, exit 1. R2's ledger is byte-identical to Indy-init's fixture |
| 2 | B-F-07: R6 imported R5 byte for byte | VERIFIED | 99/99 .fs/.css/.html files identical; 417/458 files overall |
| 3 | B-F-01: no run reached computed acceptance | VERIFIED | No ACCEPTED verdict anywhere; the claim is vacuous for 6 of 11 runs |
| 4 | B-F-03: governance was the terminal blocker from R8 on | PARTIALLY VERIFIED | Holds as "first refusal". Does not hold as "dominant blocker" for R8; doubtful for R9 and R10 |
| 5 | R10 gate: 45/66 cancelled, 1 success | VERIFIED | All time: 45 cancelled, 20 failed, 1 success. In window: 44 cancelled, 19 failed, 1 success of 64 |
| 6 | C-F-01: release-set skew | VERIFIED | 23 repos on Praxis 3.7.2; 15 on set 1.2.0; causa and R10 match 1.37.0 by lock file |
| 7 | C-F-04: Conditor trusts no Registry keys | VERIFIED | `"keys": []` at line 4 |
| 8 | C-F-08: Aegis 2.0.0 never released | VERIFIED | 0 tags; NuGet and the Registry have only 1.0.0; every consumer is on 1.0.0 |
| 9 | C-F-05: Praxis pins Ordo.Core 1.8.2 and duplicates admission code | VERIFIED | Pin is 1.8.2; 723 + 320 = 1,043 lines |
| 10 | E-F-01: `work complete` accepts /etc/hostname as evidence | VERIFIED | Reproduced on 3.25.0; 0 of 47 ros.json files enable verified completion |
| 11 | E-F-02: fabricated bundle is ACCEPTED | VERIFIED | ACCEPTED, exit 0, for a README-only repository |
| 12 | E-F-03: deleting the claim record bypasses the guard | VERIFIED | Exit 3 before the deletion, exit 0 after |
| 13 | E-F-07: no branch protection, no CODEOWNERS | VERIFIED | protected=false and no rulesets on praxis, ordo and Indy-init |

## Details

### 1. B-F-02 (independence: high)

- **Method:** exported Indy-init@dae2347 `tools/` with `git archive` and ran `compute-acceptance-verdict.py` on R2's own committed ledger (indy-init-rehearsal-002@b053d1d, `evidence/acceptance/ledger.json`).
- **Result:** INVALID, exit 1, with the claim problem "ledger 'accepted' is true but the computed verdict is INVALID".
- **Resolves B's limitation:** the R2 ledger and Indy-init's fixture are byte-identical (sha256 6ab44de1…).
- **Definitional caveat:** the INVALID label mostly comes from applying a later contract.
  - 77 of the 83 reasons are schema v2 and trusted-input requirements that did not exist when R2 ran.
  - The one substantive reason is "P0 requirement ADRP-016: NOT_RUN". On its own that gives INCOMPLETE, never ACCEPTED.
  - "Not acceptable" is robust; the specific label INVALID is not.

### 2. B-F-07 (high)

- **Method:** compared `git ls-tree` path→blob maps of R6@506cd8c and R5@b972cb4.
- **Result:**
  - 99/99 .fs/.css/.html files identical at the same path; 417/458 tracked files identical.
  - Widening to .fs/.fsproj/.css/.html/.js/.fsx/.ts gives 133/133.
  - The import commit added 92 files and modified 1. The remaining 6 were already identical in the pre-import scaffold c80f35e.

### 3. B-F-01 (medium-high)

- **Committed computed verdicts:**

  | Run | Verdict |
  |---|---|
  | R4 | FAILED on final candidate ab08b76 (earlier candidates INVALID and FAILED) |
  | R5 | INCOMPLETE ×2 |
  | R8 | INVALID ×2 |
  | R6 | FAILED per Indy-init results; the API shows run 40803128103 "Acceptance (final)" concluded failure |
  | R2 | INVALID on recompute (claim 1) |

- **No computed verdict:** R1, R3, R7, R9, R10 and Causa.
- `git grep` finds no ACCEPTED verdict at HEAD in any of the 11 run repositories.
- **Caveats:**
  - The claim is vacuous for the 6 runs that have no computed verdict.
  - R1 met its own frozen PASS criteria: its deployed accept job was green on the final release.

### 4. B-F-03 (medium; a judgment from the final reports of R8–R10 and Causa)

**R8.** The first-ranked blocker is governance: the approvals file fails trust, so the verdict is INVALID. With valid approvals it would still be FAILED:
- G3, G7 and G8 fail;
- 346 of 613 P0 obligations were not run;
- only 51 of 161 requirements were fully verified.

Product and verification incompleteness is at least co-dominant.

**R9.** The release gate refused at the run-suites step, for two reasons:
- the frozen plan's suite commands fail with MSB1008;
- the webkit project is absent.

Separately, 0/541 executable and 0/119 record obligations were implemented, and the agent stopped by choice at about 115 of 420 minutes.

**R10.** No governed verdict was produced, because of the gate cap and the write-once record. In addition:
- T22 and T29–T36 were never started;
- the browser suites had 20/173 Chromium and 19/173 WebKit failures;
- the WDL slices were blocked on a lock re-pin.

**Causa.** The classification holds strongly. The 0/203 result is dominated by:
- the T18↔T20 cycle in the frozen plan;
- process rules pinned to the R10 repository;
- the missing catalog repository.

**Definitional caveat.** B counts spec contradictions (INV-04), SDK incompatibility (MSB1008) and CI timeouts as "governance machinery".
- Under that broad category, the "first refusal" reading holds.
- Under a narrow category (approval and process records only), it does not hold for R9.

### 5. R10 gate (high)

- **Method:** fetched the full run list for workflow 409560650 myself from the Actions API (GET only).
- **Result:**
  - All time: 66 runs, of which 45 cancelled, 20 failed, 1 success.
  - In the window 16:40:13Z–23:40:13Z: 64 runs, of which 44 cancelled, 19 failed, 1 success.
  - B's raw data matches the API on all 66 run IDs, with no outcome mismatch.
- **"Deadlock" is interpretive:**
  - 36 of the 45 cancellations lasted 36–73 minutes, consistent with the 40-minute job timeout.
  - 9 lasted 0–21 minutes, consistent with being superseded by a newer PR push.
  - The only success was a push to main at 18:48Z.

### 6. C-F-01 (high)

- **Universe:** 37 repositories (all ext clones except ext/full, plus Indy-init and rehearsal-010). C used 33; the numerators are unaffected.
- **Result:**
  - 23 repositories install Praxis 3.7.2.
  - 15 bind their Conditor authority to echelon-current 1.2.0.
  - No repository has a 1.37.0 authority file. causa and rehearsal-010 have none at all, but their `.conditor/lock.json` versions equal 1.37.0's for every shared component.
  - causa also locks forma-workflow 1.2.0, which is not in the 1.37.0 set.
- **Discrepancy:** C's text says "9 more" repositories are on sets 1.3.0–1.24.0. The correct count is **8**, which is also what C's own `repo-facts.json` lists.

### 7. C-F-04 (high)

- **Source:** local clone only; the conditor remote is outside this session's access.
- **Result:** `trust/registry-release-keys.json:4` reads `"keys": []` at 528ef45, unchanged since 7b9eb13 (2026-10-13).
- This file is the only trust source: it is embedded as a resource and read by `ReleaseAttestation.embedded`.

### 8. C-F-08 (high)

- `Aegis.Core.fsproj` declares 2.0.0 (commit ec0e876).
- `git ls-remote --tags` shows 0 tags. The Registry and NuGet.org list only 1.0.0; C did not check NuGet.
- Every consumer pins 1.0.0.
- The consumer count depends on definition: 16 NuGet code consumers, which matches C, or 36 counting any pin, including rehearsals.

### 9. C-F-05 (high for the counts, medium for "duplicate")

- `Praxis.Domain.fsproj:9` pins Ordo.Core 1.8.2.
- `ContractAdmission.fs` (723 lines) plus `Model.fs` (320 lines) total 1,043 lines.
- All 29 ORDO.CONTRACT.* codes Praxis uses appear among Ordo's 42 in `ConstructibilityContract.fs`.
- The vendored 1.8.2 DLL contains no Constructibility, ORDO.CONTRACT or ContractAdmission strings.
- **Caveats:**
  - "Duplicate" means the same vocabulary re-implemented, not proven-equivalent code.
  - The 1,043 lines include the Ordo model, not admission logic alone.
  - Which implementation came first cannot be determined from the shallow clones.

### 10. E-F-01 (high)

- **Build:** Praxis 3.25.0 from 12bf995 in a scratch export; 0 warnings, 0 errors.
- **Reproduction:** on a fresh `praxis init` fixture, `work complete --evidence tests=/etc/hostname`:
  - exits 0 and marks the item complete;
  - records /etc/hostname in the completion event;
  - is followed by `work validate` reporting valid with 0 findings, and `praxis verify` exiting 0.
- **Control:** a non-existent path is refused, so the only check is existence.
- **Survey of committed content:**
  - 59 repositories, 47 with a root ros.json. None enables `requireVerifiedCompletion`, `requireAttestedEvidence` or a non-empty `trustedVerifierKeyIds`.
  - No committed JSON anywhere uses these keys.
  - The source confirms the flags are read only from `<root>/ros.json` `workProtocol`.
  - E counted 45 files; the conclusion is the same.

### 11. E-F-02 (high)

- **Independence:** my own fabrication script, written from the verifier source without reading E's script.
- **Setup:**
  - A candidate repository whose only tracked file is README.md.
  - 118 fabricated artifacts covering G0–G9 and all 108 P0 requirements, each claiming PASS for the command `true`.
  - The real pinned baseline and approvals, read from my own full-history Indy-init clone.
- **Result:** the verifier at dae2347 returned ACCEPTED, exit 0, with no reasons. The same happened at 459f65a, the revision rehearsal-005 actually pinned.
- **Negative control:** changing one byte of one artifact gives a digest mismatch and a non-ACCEPTED verdict.
- **Pipeline wiring confirmed** in rehearsal-005's `acceptance.sh`:
  - Lines 66–70 take the manifest digest from the stdout of `$CA ledger`, the candidate repository's own tool (build-and-test.yml:47).
  - Line 111 passes that value as `--evidence-manifest-sha256`.
  - `--trusted-source-sha` is `github.sha`.
- **Not tested:** `requirements-compiler verify-plan`. Whole-pipeline acceptance of R5 is therefore not shown.

### 12. E-F-03 (high)

- After `work claim`, plain `work complete` exits 3 with `PRX.COMPLETION.VERIFIED_COMPLETION_REQUIRED`.
- After `rm -rf .git/praxis/claims/WI-V2B`, the same command exits 0 with /etc/hostname as evidence, and validation is clean.

### 13. E-F-07 (high for the 3 repositories queried)

- **Branch protection** (read-only API): praxis, ordo and Indy-init report main protected=false, and `rules/branches/main` returns `[]`, so no ruleset applies.
- **CODEOWNERS:**
  - absent on all three remotes;
  - absent at HEAD in praxis, ordo, Indy-init, mercatus, signal and rehearsals 001–010;
  - present only in causa-data and limen.
- **Not queryable from this session:** conditor and causa.

## Corrections for synthesis

- **B-F-03, restated:** "Governance and verification-machinery failures were the first refusal from R8 on, and masked large product incompleteness in R8–R10."
- **B-F-02:** present the INVALID verdict with its caveat. Substantively, the ledger is INCOMPLETE because ADRP-016 was not run.
- **C-F-01:** "9 more" should read **8**.
