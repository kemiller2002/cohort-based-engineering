"""Curated event records for R1-R10 and the Causa competition build.

Data entry only (no logic). Each record cites a source as `repo@rev path:line`,
a commit SHA, a PR number or an Actions run id. Revisions:
  R1 research-documents@b372a7f (indy-init-rehearsal-001@dd63ab4)
  R2 indy-init-rehearsal-002@b053d1d   R3 indy-init-rehearsal-003@59cf4d2
  R4 indy-init-rehearsal-004@78a1b15   R5 indy-init-rehearsal-005@b972cb4
  R6 indy-init-rehearsal-006@41fb6d6   R7 indy-init-rehearsal-007@f61493f
  R8 indy-init-rehearsal-008@fd8fba9   R9 indy-init-rehearsal-009@0e76050
  R10 indy-init-rehearsal-010@95b3ed4  CAUSA causa@97c0a98   Indy-init@dae2347
  audits indy-init-audits@10aeded      raw/actions/*.jsonl fetched 2026-11-08
Root-cause codes are defined in TAXONOMY.md.
"""

R1 = "research-documents@b372a7f research/construction-by-design/indy-init-r001/RESULT.md"
R1E = "research-documents@b372a7f research/construction-by-design/indy-init-r001/ERRATA.md"
R2 = "indy-init-rehearsal-002@b053d1d docs/REHEARSAL-002-REPORT.md"
R3 = "indy-init-rehearsal-003@59cf4d2 docs/REHEARSAL-003-REPORT.md"
R3D = "indy-init-rehearsal-003@59cf4d2 research/rehearsal-003-defect-analysis.md"
I3 = "Indy-init@dae2347 docs/REHEARSAL-003-RESULTS.md"
I4 = "Indy-init@dae2347 docs/REHEARSAL-004-RESULTS.md"
R4 = "indy-init-rehearsal-004@78a1b15 docs/rehearsal/REHEARSAL-004-REPORT.md"
I5 = "Indy-init@dae2347 docs/REHEARSAL-005-RESULTS.md"
BL = "Indy-init@dae2347 docs/engineering-improvement/BASELINE-2026-10-28.md"
I6 = "Indy-init@dae2347 docs/REHEARSAL-006-RESULTS.md"
R7 = "indy-init-rehearsal-007@f61493f evidence/FINAL-REPORT.md"
R7K = "indy-init-rehearsal-007@f61493f evidence/DECISIONS.md"
AUD = "indy-init-audits@10aeded rehearsal-007/2026-10-29/READINESS-AUDIT-2026-10-29.md"
R8 = "indy-init-rehearsal-008@fd8fba9 evidence/FINAL-REPORT.md"
R8D = "indy-init-rehearsal-008@fd8fba9 evidence/DEVIATIONS.md"
R8S = "indy-init-rehearsal-008@fd8fba9 evidence/SCHEDULE-ACTUALS.md"
R9 = "indy-init-rehearsal-009@0e76050 evidence/FINAL-REPORT.md"
RG = "Indy-init@dae2347 docs/release-gate-repair/FINAL-REPORT.md"
R10 = "indy-init-rehearsal-010@95b3ed4 evidence/FINAL-REPORT.md"
R10B = "indy-init-rehearsal-010@95b3ed4 evidence/t0/authorization-blocker/BLOCKER-REPORT.md"
CA = "causa@97c0a98 evidence/FINAL-REPORT.md"
MC = "tracks/B-forensics/data/merge-conflicts.json (git merge-tree replay)"
CI = "tracks/B-forensics/data/ci-metrics.json (Actions run list)"


def e(rehearsal, timestamp, eventType, description, source, rootCause, contributing=(), reqs=(), human=False, detectedBy=None, mOrE="MEASURED"):
    return {
        "rehearsal": rehearsal, "timestamp": timestamp, "eventType": eventType,
        "description": description, "source": source, "rootCause": rootCause,
        "contributingFactors": list(contributing), "requirementIds": list(reqs),
        "humanIntervention": human, "detectedBy": detectedBy, "measuredOrEstimate": mOrE,
    }


EVENTS = (
    # ---------------- R1 ----------------
    e("R1", "2026-10-21T16:26:26Z", "run-start", "T0; Conditor bootstrap 9799ed8 with no application code; 82 release-profile requirements derived", f"{R1}:4; indy-init-rehearsal-001 9799ed8", "NONE"),
    e("R1", None, "requirement-intake-rework", "Requirement id formats guessed twice before reading the artifact grammar (R-01/R-02); Praxis rejected them", f"{R1}:177,221", "RC-SELF-ATTEST", ["RC-GOV-UNTESTED"], detectedBy="tool"),
    e("R1", None, "evidence-overclaim", "Test tags claimed R9.6/R9.7/R4.2 from test titles rather than assertions (R-13), including by the coordinator at T+77", f"{R1}:177", "RC-SELF-ATTEST", detectedBy="review"),
    e("R1", None, "first-green-ci", "First full green application CI at T+88 (reported)", f"{R1}:127", "NONE", mOrE="MEASURED"),
    e("R1", None, "defect-recurrence", "Forged-history defect class reported three times (R-14 -> R-18) before a class-level fix (replay through Decide) at RC3", f"{R1}:183", "RC-FIX-REGRESSION", ["RC-CONCURRENCY"], detectedBy="review"),
    e("R1", None, "independent-review", "Four adversarial review rounds reported 28 findings in code that already passed its tests", f"{R1}:116", "RC-SELF-ATTEST", detectedBy="review"),
    e("R1", "2026-10-21T20:13:00Z", "acceptance-overclaim", "RC2-RC5 treated as Accepted from container-side runs while the deploy workflow's accept job was red (R-21); noticed only at T+247", f"{R1}:48,181; {R1E} ER-2", "RC-SELF-ATTEST", ["RC-OWNER-PREREQ"], detectedBy="self (late)"),
    e("R1", None, "env-disruption", "Container restart at T+221.7; clock basis switched to wall clock; no work lost", f"{R1}:134; {R1E} ER-1", "RC-ENV-SANDBOX"),
    e("R1", None, "deployment-config", "Pages custom domain served plain http (R-22), failing the deployed accept job; human-owned setting, fixed by owner after the run", f"{R1}:46,182; {R1E} ER-5", "RC-OWNER-PREREQ", human=True),
    e("R1", None, "scope-gap", "Live GitHub persistence never exercised: R10.1-R10.4/AC-09 verified only against a mocked contents API", f"{R1}:43", "RC-PROVIDER-MODEL", ["RC-OWNER-PREREQ"]),
    e("R1", None, "provenance-deviation", "R1 built the actual competition application rather than a sacrificial app (R0.3 deviation)", f"{R1E} ER-3", "RC-PROVENANCE"),
    e("R1", None, "acceptance-claim", "Self-classified PASS at T+261.8 (61/82 scoped requirements verified in CI); predates Indy-init's ledger contract, so no computed verdict exists", f"{R1}:3-4", "NONE"),
    # ---------------- R2 ----------------
    e("R2", "2026-10-23T12:14:13Z", "run-start", "T0; Phase 0 stack discovery made blocking", f"{R2}:3,98", "NONE"),
    e("R2", "2026-10-23T13:58:28Z", "first-green-ci", "First green CI at T+104.3 (Actions first green Build and test T+104.2)", f"{R2}:83; {CI}", "NONE"),
    e("R2", None, "provider-divergence", "DC-004 (advisory provider field read as authority) found twice and DC-005 (stale mutable reads) three times only by the real GitHub provider", f"{R2}:71-73", "RC-PROVIDER-MODEL", ["RC-CONCURRENCY"], detectedBy="live provider"),
    e("R2", None, "design-reversal", "Review 6 proved GitHub REST cannot compare-and-swap a branch; on the owner's decision the write path was replaced by GraphQL createCommitOnBranch with expectedHeadOid", f"{R2}:61-63", "RC-CONCURRENCY", ["RC-PROVIDER-MODEL"], human=True, detectedBy="review"),
    e("R2", None, "defect-recurrence", "5 defect classes recurred after a claimed fix (DC-002..DC-006); 1 security + 11 closure reviews", f"{R2}:89-90", "RC-FIX-REGRESSION", ["RC-CONCURRENCY"], detectedBy="review"),
    e("R2", "2026-10-23T17:11:00Z", "first-deploy", "First deployed, identity-verified build with deployed acceptance at T+296.8", f"{R2}:86", "NONE"),
    e("R2", "2026-10-24T00:15:24Z", "acceptance-claim", "Self-declared ACCEPTED at T+721.2 (301 min past the 420 ceiling); Indy-init's verifier recomputes the historical ledger as INVALID (ADRP-016 NOT_RUN, accepted flag disagrees)", f"{R2}:48,87; Indy-init@dae2347 tools/test-acceptance-verdict.py:379-387; recomputed by track B", "RC-SELF-ATTEST", ["RC-TIME-MGMT"]),
    e("R2", None, "merge-before-review", "63b2232 merged to main before the fourth independent closure review reported (UD-4)", "indy-init-rehearsal-002@b053d1d evidence/acceptance/run.json:295-298", "RC-SELF-ATTEST"),
    e("R2", None, "owner-prereq", "Branch protection prepared but not applied; needs repository admin (UD-1)", f"{R2}:111", "RC-OWNER-PREREQ", human=True),
    e("R2", None, "upstream-defect", "Stack defects DEF-STACK-001..008 incl. Conditor SD-1 (Folio from npm) and Praxis DEF-STACK-007", f"{R2}:26,112", "RC-TOOLCHAIN"),
    # ---------------- R3 ----------------
    e("R3", "2026-10-24T07:10:46Z", "preflight-failure", "SD-1 recurred from R2: Conditor scaffold installs Folio from npm (404); 2 preflight CI failures (40074002224, 40074314605)", f"{R3D}:16-24", "RC-TOOLCHAIN", ["RC-FIX-REGRESSION"], detectedBy="CI"),
    e("R3", "2026-10-24T07:32:22Z", "run-start", "Timed phase start", f"{R3D}:12", "NONE"),
    e("R3", None, "requirement-loss", "DC-008: derivation from mission text dropped UI-016 palette and left 29 P0 requirements without disposition; escaped every R3 gate", f"{I3}:40; cohort-based-engineering research/consolidation/2026-10-24/engineering-findings.md:96", "RC-DERIV-LOSS", ["RC-GOV-UNTESTED"], ["UI-016"], detectedBy="post-hoc reconciliation"),
    e("R3", None, "process-violation", "P-1: timer-start record committed outside a work item; Praxis validation run 40074540526 failed", f"{R3D}:162-168", "RC-GOV-UNTESTED", detectedBy="CI"),
    e("R3", None, "ci-config", "D-02: workflow named a global.json that did not exist (run 40076936119)", f"{R3D}:44-52", "RC-CI-HARNESS", detectedBy="CI"),
    e("R3", None, "ci-config", "D-03: data-backed tests failed in the tool-managed Dokimos workflow (run 40076936179)", f"{R3D}:54-66", "RC-CI-HARNESS", ["RC-TOOLCHAIN"], detectedBy="CI"),
    e("R3", None, "fix-induced-defect", "D-06: D-02's fix pinned an SDK the tool-managed Dokimos workflow does not install (run 40078381238)", f"{R3D}:96-107", "RC-FIX-REGRESSION", ["RC-CI-HARNESS"], detectedBy="CI"),
    e("R3", None, "provider-divergence", "D-07: browser cache hid a rejected credential on real GitHub (recurrence of R2 DC-005); first fix incomplete (review M2)", f"{R3D}:109-136", "RC-PROVIDER-MODEL", ["RC-CONCURRENCY", "RC-FIX-REGRESSION"], detectedBy="live provider"),
    e("R3", "2026-10-24T08:51:25Z", "first-green-ci", "First green application CI at T+79.1", f"{R3}:140", "NONE"),
    e("R3", "2026-10-24T08:53:43Z", "first-deploy", "Verified deployment at T+81.4 (Actions first green deploy T+81.4)", f"{R3}:171; {CI}", "NONE"),
    e("R3", None, "provider-divergence", "H1: GitHub answers a missing branch with 422; the fake returned 404", f"{R3D}:144", "RC-PROVIDER-MODEL", detectedBy="review"),
    e("R3", None, "defect-recurrence", "M1: late answer from a failed load applied to its retry, recurrence of R2 DC-002 despite a 'prevented by design' claim", f"{R3D}:145,195", "RC-CONCURRENCY", ["RC-SELF-ATTEST"], detectedBy="review"),
    e("R3", None, "evidence-overclaim", "M5: layering test claimed by plan and preflight did not exist", f"{R3D}:149", "RC-SELF-ATTEST", detectedBy="review"),
    e("R3", None, "security-exposure", "N1: live jobs could upload traces containing the token (fix-induced by the Test A test)", f"{R3D}:157", "RC-SECURITY-EXPOSURE", ["RC-FIX-REGRESSION"], detectedBy="review"),
    e("R3", None, "acceptance-overclaim", "Draft report db89a3a said ACCEPTED with two blocked gates; independent reviewer rejected it", f"{R3}:9", "RC-SELF-ATTEST", detectedBy="review"),
    e("R3", "2026-10-25T00:00:00Z", "approval-forgery", "Remediation agent interpreted a blanket approval and wrote approval files; transcription withdrawn (OD-INDY-7)", f"{I3}:41", "RC-SELF-ATTEST", human=True, detectedBy="owner", mOrE="ESTIMATE"),
    e("R3", None, "gate-weakness", "Preservation gate accepts self-written approvals/reviews, an edited baseline, role swaps; no CI job ran it", f"{I3}:26", "RC-GOV-UNTESTED", ["RC-SELF-ATTEST"], detectedBy="review"),
    e("R3", None, "env-limit", "E-1..E-3: proxy authenticates curl, anonymous browser shares 60/h quota, Pages admin API refused", f"{R3D}:186-188", "RC-ENV-SANDBOX"),
    e("R3", None, "verdict", "NOT ACCEPTED (blocked): Test A credential and Percepta evidence unavailable; ledger 116 criteria 67 PASS", f"{R3}:3-5; {I3}:3,24", "RC-OWNER-PREREQ", ["RC-TOOLCHAIN"]),
    # ---------------- R4 ----------------
    e("R4", "2026-10-27T06:04:39Z", "run-start", "T0 = first green bootstrap CI", "indy-init-rehearsal-004@78a1b15 evidence/rehearsal/clock.json:3", "NONE"),
    e("R4", "2026-10-27T06:40:00Z", "first-live-write", "Live write path green in CI at T+36", f"{R4}:74", "NONE", mOrE="MEASURED"),
    e("R4", "2026-10-27T07:04:00Z", "format-mismatch", "Approvals file in Praxis format; verifier needs causa.requirements-approvals/1; found at T+60", f"{I4}:62", "RC-GOV-UNTESTED", ["RC-OWNER-PREREQ"], detectedBy="tool", mOrE="ESTIMATE"),
    e("R4", None, "approval-by-agent", "RDP-003 twice: coding agent wrote both approvals files on owner instruction; ratification open", f"{I4}:53", "RC-SELF-ATTEST", ["RC-OWNER-PREREQ"], human=True),
    e("R4", None, "runtime-defect", "D-HIST-WASM: loading three historical cases in one page fails; ~2 h over ~10 CI round trips because nuget.org blocked in sandbox", f"{R4}:76; {I4}:29,65", "RC-TOOLCHAIN", ["RC-ENV-SANDBOX"], ["EXT-DATA-013"], detectedBy="CI"),
    e("R4", None, "security-exposure", "Live token appeared in Playwright traces of a failed run (6269dd3); owner rotated it; fixed 64ae19b", f"{R4}:142", "RC-SECURITY-EXPOSURE", ["RC-CI-HARNESS"], ["PF-015"], human=True, detectedBy="self"),
    e("R4", None, "defect-recurrence", "DCT-001-A / DCT-002-B returned at application level after the state machine fix; app bypassed Sync and marked unsent investigations persisted", f"{R4}:43; {BL} finding 7", "RC-CONCURRENCY", ["RC-FIX-REGRESSION"], detectedBy="review"),
    e("R4", None, "owner-settings", "Owner changed Pages source, default branch and github-pages environment during the run", f"{I4}:57", "RC-OWNER-PREREQ", human=True),
    e("R4", None, "evidence-gap", "8 of 9 P0 FAILs and most NOT_RUNs are evidence gaps (no mapped check), not defects found by a test", f"{I4}:25,63", "RC-GOV-UNTESTED", ["RC-SELF-ATTEST"]),
    e("R4", None, "evidence-overclaim", "Tests tagged with obligations they did not prove (EXT-DATA-002-O2)", f"{BL} finding 4", "RC-SELF-ATTEST", detectedBy="review"),
    e("R4", "2026-10-27T11:00:31Z", "verdict", "Computed FAILED (P0 1 PASS / 9 FAIL / 98 NOT_RUN); owner stopped run at T+296", f"{I4}:3,22,24", "RC-GOV-UNTESTED", ["RC-SELF-ATTEST"], human=True),
    # ---------------- R5 ----------------
    e("R5", "2026-10-27T20:08:38Z", "run-start", "T0 = first green bootstrap CI; Praxis validation failed on bootstrap range (unattributed Conditor files)", "indy-init-rehearsal-005@b972cb4 evidence/rehearsal/clock.json:3-4", "RC-GOV-UNTESTED"),
    e("R5", None, "owner-prereq", "CAUSA_TEST_REPO empty and DEPLOY_TARGET unset at kickoff; owner set them during the run", f"{I5}:61; Indy-init@dae2347 docs/AGENT-RELIABILITY-REQUIREMENTS.md:97", "RC-OWNER-PREREQ", human=True),
    e("R5", None, "owner-decisions-in-chat", "7 owner decisions given in chat and transcribed by the agent (approvals files, 775 equivalence reviews, registry approval, DF-0001, DF-0002, AI provider, secrets)", f"{I5}:53-61", "RC-OWNER-PREREQ", ["RC-SELF-ATTEST"], human=True),
    e("R5", "2026-10-27T21:30:00Z", "runtime-defect", "View.project exceeded the .NET WASM interpreter locals limit; app could not start from ec6407b to a0e7d4a (~90 min); CoreCLR tests cannot see it", f"{BL} finding 1; {I5}:44", "RC-TOOLCHAIN", ["RC-CI-HARNESS"], ["AR-029"], detectedBy="browser smoke"),
    e("R5", None, "parallel-write", "17 merges in the window conflicted in source (src/app/View.fs, Adapter.fs, EnginePort.fs, specs); 19 'Praxis: reconcile' commits; WIP commits reached main", f"{MC}; {BL} findings 3,15", "RC-PARALLEL-WRITE", ["RC-GOV-UNTESTED"]),
    e("R5", None, "ci-harness", "Shared test ports / reuseExistingServer let three streams pass against stale builds while main could not start", f"{I5}:46; Indy-init@dae2347 docs/AGENT-RELIABILITY-REQUIREMENTS.md:87", "RC-CI-HARNESS", ["RC-PARALLEL-WRITE"], ["AR-028"], detectedBy="CI"),
    e("R5", None, "persistence-defect", "F-1 critical: per-page write marker let two writers collide; reconcile claimed 'synced' and erased the other writer's events", f"{I5}:40", "RC-CONCURRENCY", reqs=["AR-035"], detectedBy="review"),
    e("R5", None, "security-exposure", "Production page exposed EnableTestHooks through getDotnetRuntime", f"{I5}:45", "RC-SECURITY-EXPOSURE", reqs=["AR-030"], detectedBy="review"),
    e("R5", None, "evidence-overclaim", "13 of 22 spot-checked passing obligations over-tagged (partly or wrongly proven); ~20 tags removed in 5dcb91e", f"Indy-init@dae2347 docs/AGENT-RELIABILITY-REQUIREMENTS.md:99; {BL} finding 4", "RC-SELF-ATTEST", reqs=["AR-034"], detectedBy="review"),
    e("R5", None, "gate-weakness", "Praxis preservation verify 3.22.0 passes value and role swaps (AR-002-O2)", f"{I5}:47; {BL} finding 5", "RC-GOV-UNTESTED", ["RC-TOOLCHAIN"], ["AR-002", "AR-027"], detectedBy="independent check"),
    e("R5", None, "env-disruption", "Two container restarts stopped stream agents; resumed from transcripts", f"{I5}:75", "RC-ENV-SANDBOX"),
    e("R5", "2026-10-28T02:41:07Z", "verdict", "Computed INCOMPLETE: G0-G7 PASS (first G7 PASS), 0 FAIL, 49 of 326 obligations with no proving test (mostly process/owner evidence)", f"{I5}:3,16-18", "RC-GOV-UNTESTED", ["RC-OWNER-PREREQ"]),
    # ---------------- R6 ----------------
    e("R6", "2026-10-28T20:02:19Z", "run-start", "T0 = kickoff receipt", f"{I6}:20", "NONE"),
    e("R6", "2026-10-28T20:08:58Z", "provenance-deviation", "R6 imported R5's application (506cd8c); 99/99 .fs/.css/.html files byte-identical to R5 b972cb4 (track-B recomputation; audit verdict DEVIATION); later prohibited by OD-INDY-22", f"ext/full/indy-init-rehearsal-006 506cd8c vs indy-init-rehearsal-005 b972cb4 (git ls-tree); {AUD} row 18; Indy-init@dae2347 docs/OWNER-DECISIONS-2026-11-03.md OD-INDY-22", "RC-PROVENANCE"),
    e("R6", None, "owner-prereq", "Secrets CAUSA_GITHUB_TOKEN/CAUSA_WRITE_TOKEN/CAUSA_TEST_REPO, DEPLOY_TARGET and Pages source needed from the owner after T0", "indy-init-rehearsal-006@41fb6d6 evidence/progress/progress.json (snapshot T+25)", "RC-OWNER-PREREQ", human=True),
    e("R6", "2026-10-28T22:22:00Z", "ci-starvation", "One concurrency group per commit plus job-level if: always() left no main run completing for ~90 min; owner force-cancelled; 116 of 132 Build and test runs cancelled, the only success being the bootstrap commit", f"{I6}:80-86; {CI}", "RC-CI-HARNESS", human=True, detectedBy="self"),
    e("R6", None, "ci-race", "Two global-property sets of Causa.Persistence shared obj/Release (MSB3030), core red intermittently", f"{I6}:75", "RC-CI-HARNESS", detectedBy="CI"),
    e("R6", None, "persistence-defect", "R6-D-002: no cross-tab exclusion without Web Locks; changes lost every run (R5 known limit R3-F2); two fallback designs failed", f"{I6}:39-40", "RC-CONCURRENCY", ["RC-FIX-REGRESSION"], ["AR-035"], detectedBy="test"),
    e("R6", None, "persistence-defect", "R6-D-003: offline unsendable save retried without backoff (151 POSTs/60 s), wrong status text", f"{I6}:41", "RC-CONCURRENCY", reqs=["UI-010"], detectedBy="test"),
    e("R6", None, "security-exposure", "D-09: the 'read-only' credential can write", f"{I6}:54", "RC-SECURITY-EXPOSURE", ["RC-OWNER-PREREQ"], ["PF-015", "EXT-DATA-004", "EXT-DATA-005"], detectedBy="test"),
    e("R6", None, "self-reference-paradox", "Final acceptance could not read records naming the candidate's own SHA; fixed by a records-only descendant (D-12)", f"{I6}:87-89", "RC-GOV-UNTESTED", detectedBy="tool"),
    e("R6", None, "stale-evidence", "G7 closures cited R5 fix commits absent from R6 history; re-review missed the freeze (D-11)", f"{I6}:62", "RC-PROVENANCE", ["RC-TIME-MGMT"], detectedBy="verifier"),
    e("R6", None, "owner-attestation", "Owner attested kickoff, REVIEW-1 and final review in chat or by merge (D-06, D-10, D-13), so 26 process requirements stay NOT_RUN", f"{I6}:63,101-104", "RC-OWNER-PREREQ", ["RC-GOV-UNTESTED"], human=True),
    e("R6", None, "first-deploy", "First deployed vertical slice at T+128 (f91d2c5)", f"{I6}:21", "NONE"),
    e("R6", "2026-10-29T01:55:00Z", "verdict", "Computed FAILED: G5-G9 FAIL; 115 P0 70 PASS/19 FAIL/26 NOT_RUN; two critical defects open", f"{I6}:3-29", "RC-CONCURRENCY", ["RC-GOV-UNTESTED"]),
    # ---------------- R7 ----------------
    e("R7", "2026-10-29T13:31:00Z", "readiness-audit", "Pre-run audit verdict NOT READY: no compiled v4 package, no ruleset, secrets absent", f"{AUD}:33-55,80,89", "RC-OWNER-PREREQ", ["RC-GOV-UNTESTED"], detectedBy="audit"),
    e("R7", "2026-10-29T22:49:55Z", "run-start", "Owner authorized kickoff with K3 (compiled package) open (KD-001)", f"{R7}:5; {R7K}:8", "RC-OWNER-PREREQ", human=True),
    e("R7", None, "ci-integrity", "KD-016: CI steps piped through tee without pipefail, so failing commands could not fail; catalog check had never run", f"{R7K}:23", "RC-CI-HARNESS", detectedBy="self"),
    e("R7", None, "contract-mismatch", "KD-017/019: code built against the candidate data contract, not the frozen causa-storage v1.0.0; found by live catalog check", f"{R7K}:24,26", "RC-PROVIDER-MODEL", ["RC-GOV-UNTESTED"], detectedBy="live provider"),
    e("R7", None, "provider-divergence", "KD-018/020/022: lost-answer commit reported as conflict; secondary rate limit and moved-head race reported as permission refusals; found only against real GitHub", f"{R7K}:25,27,29", "RC-PROVIDER-MODEL", ["RC-CONCURRENCY"], detectedBy="live provider"),
    e("R7", None, "parallel-write", "Live CI jobs from different runs wrote to the same test repository at once", f"{R7}:95; {R7K}:27", "RC-CI-HARNESS", ["RC-PARALLEL-WRITE"], detectedBy="live provider"),
    e("R7", "2026-10-30T02:16:00Z", "independent-review", "Review 1 FAIL: 15 findings and 3 surviving mutants (saved without read-back, refresh discards edits)", f"{R7}:21; {R7K}:28", "RC-CONCURRENCY", ["RC-SELF-ATTEST"], detectedBy="review"),
    e("R7", None, "fix-induced-defect", "Second review's stuck-conflict fix introduced a race that could overwrite another writer (review 3 H1)", f"{R7}:23,124; {R7K}:31", "RC-FIX-REGRESSION", ["RC-CONCURRENCY"], detectedBy="review"),
    e("R7", "2026-10-30T03:51:00Z", "deadline-miss", "PR #28 green at 03:51Z left unmerged; agent projected remaining time from old timestamps and told owner ~2 h remained", f"{R7}:122-123", "RC-TIME-MGMT", human=True, detectedBy="owner"),
    e("R7", None, "ui-defect", "Four Forma token names in causa.css did not exist; five properties fell back to system colours (found post-deadline)", f"{R7}:129-135", "RC-UI-SPEC", detectedBy="post-deadline check"),
    e("R7", "2026-10-30T05:49:55Z", "verdict", "NOT VERIFIED, NOT ACCEPTED: three independent reviews FAIL; deployed acceptance 38/1/9 on main; first fully green main only after deadline (9b307aa)", f"{R7}:13-29,181-190", "RC-TIME-MGMT", ["RC-CONCURRENCY"]),
    # ---------------- R8 ----------------
    e("R8", "2026-11-01T17:31:24Z", "run-start", "T0; topology C role lanes; pre-existing repo used on owner direction", f"{R8}:6-9", "NONE", human=True),
    e("R8", "2026-11-01T17:35:57Z", "first-green-ci", "Bootstrap first green CI at T+4.5", f"{R8}:42-43", "NONE"),
    e("R8", None, "toolchain", "Central package management disabled implicit FSharp.Core; every .NET test assembly skipped until owner-ratified pin (DEV-R8-04)", f"{R8D}:5-9", "RC-TOOLCHAIN", ["RC-GOV-UNTESTED"], human=True, detectedBy="lane"),
    e("R8", None, "suite-not-running", "Live suites never ran (MSB1008) until CI fix #16 at T+94", f"{R8S}:22", "RC-GOV-UNTESTED", ["RC-CI-HARNESS"], detectedBy="self"),
    e("R8", None, "contract-defect", "Frozen IF41-DOMAIN carries no command body; CRs declined (DEV-R8-09, CR-T17-01)", f"{R8D} DEV-R8-09", "RC-GOV-UNTESTED", detectedBy="lane"),
    e("R8", None, "contract-defect", "INV-04 contradicts SM-SAVE T-S31/T-S32 (DEV-R8-11); INV04 stays red; SM-SAVE gap DEV-R8-12", f"{R8D} DEV-R8-11, DEV-R8-12", "RC-GOV-UNTESTED", reqs=["PERSIST-016"], detectedBy="lane"),
    e("R8", None, "parallel-write", "60 of 87 merges conflicted; 56 only in Praxis .ros state (current.json, events.jsonl); praxis history merge refused, union-script fallback (DEV-R8-08)", f"{MC}; {R8D} DEV-R8-08", "RC-PARALLEL-WRITE", ["RC-TOOLCHAIN"]),
    e("R8", None, "tool-defect", "Praxis 3.24.0 step identity breaks after ingest; agent hand-edited .ros (DEV-R8-07)", f"{R8D} DEV-R8-07", "RC-TOOLCHAIN"),
    e("R8", None, "owner-settings", "Owner enabled Pages and set DEPLOY_TARGET (~17:50Z) after proxy refused the agent", f"{R8D} GitHub Pages", "RC-OWNER-PREREQ", ["RC-ENV-SANDBOX"], human=True),
    e("R8", "2026-11-01T19:40:00Z", "first-deploy", "First verified deployment b45e969 at T+129", f"{R8}:144", "NONE"),
    e("R8", None, "approvals-invalid", "Pinned approvals file fails verifier trust checks (no immutable authority source); verdict INVALID", f"{R8}:19-25", "RC-OWNER-PREREQ", ["RC-GOV-UNTESTED"]),
    e("R8", None, "evidence-gap", "347 of 613 P0 obligations unverified: 152 because the Chromium spec file is absent, 81 bootstrap stubs", f"{R8}:92-108", "RC-GOV-UNTESTED"),
    e("R8", "2026-11-01T23:50:00Z", "verdict", "INVALID (with valid approvals would be FAILED); 266/613 obligations verified; 51/161 requirements", f"{R8}:19,73-79", "RC-GOV-UNTESTED", ["RC-OWNER-PREREQ"]),
    # ---------------- R9 ----------------
    e("R9", "2026-11-04T00:30:01Z", "run-start", "T0 recorded before conditor init; single agent; content-catalog scope", f"{R9}:14", "NONE"),
    e("R9", None, "process-violation", "Implementation began before any Praxis work item (6 violating commits edde38c..33d072d)", f"{R9}:203; {RG}:26,108", "RC-GOV-UNTESTED"),
    e("R9", None, "fault-probe", "Probe P-CONTENT-RELATION-REASSESS survived first run, exposing a no-op E2E; test fixed", f"{R9}:166", "RC-SELF-ATTEST", detectedBy="fault probe"),
    e("R9", None, "deploy-failure", "First deploy at 39dc037 failed for lack of the pinned SDK; PR #2", f"{R9}:172", "RC-CI-HARNESS"),
    e("R9", None, "gate-cannot-run", "Release gate REFUSED: frozen v4.1.2 suite commands fail on pinned SDK (MSB1008) and name an undefined webkit project; generator carried the defect through v4.1..v4.1.2", f"{R9}:191-195; {RG}:13-17", "RC-GOV-UNTESTED", ["RC-TOOLCHAIN"], detectedBy="gate"),
    e("R9", None, "tool-catalog-mismatch", "Dokimos 0.11.0 has no case for url-input; INV-029 always FAIL", f"{R9}:212; {RG}:18", "RC-TOOLCHAIN", reqs=["INV-029"]),
    e("R9", "2026-11-04T02:25:00Z", "verdict", "Catalog: Dokimos accepted 199/199 mandatory; full plan 0/541 executable, 0/119 record; owner verdict not computed; stopped at T+115 by choice", f"{R9}:3-8,93-94", "RC-GOV-UNTESTED"),
    # ---------------- R10 ----------------
    e("R10", "2026-11-06T16:40:13Z", "run-start", "T0; v4.1.5 approved scope 205 requirements / 890 obligations", f"{R10}:9-10", "NONE"),
    e("R10", "2026-11-06T16:52:46Z", "gate-refuses-valid-plan", "authorize-implementation REFUSED a valid plan (55 causes): Praxis rejects T-ids; 9 approved coordination items have no links; gate only ever tested with a synthetic plan", f"{R10B}", "RC-GOV-UNTESTED", ["RC-TOOLCHAIN"], detectedBy="gate"),
    e("R10", "2026-11-06T16:57:00Z", "owner-directed-repair", "Owner directed builder to repair Indy-init tooling mid-run (PR #174)", f"{R10B} Resolution; {R10}:57", "RC-GOV-UNTESTED", human=True),
    e("R10", None, "toolchain", "FSharp.Core missing under central package management: 0 tests ran (SL-T11) - same as R8 DEV-R8-04", f"{R10}:151", "RC-TOOLCHAIN", ["RC-FIX-REGRESSION"]),
    e("R10", None, "gate-deadlock", "Governed gate never produced a verdict: 40-min cap, write-once governance record, Playwright install timeouts, branch-name refusal; 45 of 66 gate runs cancelled, 20 failed, 1 success", f"{R10}:17-21,137-141; {CI}", "RC-GOV-UNTESTED", ["RC-CI-HARNESS"], detectedBy="CI"),
    e("R10", None, "owner-rule-change", "Owner rule B replaced governed gate: merges implementer-verified, not governed-accepted", f"{R10}:72-81", "RC-GOV-UNTESTED", human=True),
    e("R10", None, "ci-timeout", "build-and-test cancelled by its 20-min job limit on every PR once browser suites (~29 min) became real", f"{R10}:137", "RC-CI-HARNESS"),
    e("R10", None, "stack-scope", "WDL slices blocked: forma-workflow 1.2.0 outside locked set; owner re-pin not done in window", f"{R10}:29-32", "RC-STACK-SCOPE", ["RC-OWNER-PREREQ"], ["WDL-001", "VER-001"]),
    e("R10", None, "parallel-write", "Two lanes briefed to edit InvestigationList.fs; 34 of 66 merges conflicted (29 only .ros, 5 source)", f"{R10}:164; {MC}", "RC-PARALLEL-WRITE"),
    e("R10", None, "fabrication-attempt", "Coordinator rejected a lane's fabricated evidence fallback (INV-028 violation) before merge", f"{R10}:166", "RC-SELF-ATTEST", detectedBy="coordinator"),
    e("R10", None, "coordinator-error", "Sync script pushed despite failed Praxis validation; merge during gate run made STALE_TARGET; git stash lost index", f"{R10}:162-165", "RC-TIME-MGMT", ["RC-GOV-UNTESTED"]),
    e("R10", None, "contract-gap", "J2-03/04/06/07 need RecordConclusion and storage 1.1.0 events not in v4.1.5; WDL-013 had no obligations (selector compiler defect)", f"{R10}:46-48,156", "RC-GOV-UNTESTED"),
    e("R10", "2026-11-06T23:40:13Z", "verdict", "No governed verdict; 278/278 non-live tests pass; browser 20/19 failing (Chromium/WebKit); live suites BLOCKED in session", f"{R10}:1,15-22,117-133", "RC-GOV-UNTESTED", ["RC-CI-HARNESS"]),
    # ---------------- CAUSA competition ----------------
    e("CAUSA", "2026-11-07T16:10:50Z", "run-start", "Competition T0; v4.1.6 governed from Indy-init dae2347; owner set working stop 22:00Z", f"{CA}:5-6", "NONE", human=True),
    e("CAUSA", None, "owner-prereq", "Read-only token could not be requested before T0 (proxy refused); live tests fail closed BLOCKED", f"{CA}:153", "RC-ENV-SANDBOX", ["RC-OWNER-PREREQ"]),
    e("CAUSA", None, "plan-cycle", "T18<->T20 cycle in frozen slice plan: T18's acceptance spec needs Connect wired only by T20; every downstream slice refused DEPENDENCY_NOT_INTEGRATED", f"{CA}:70-75,180", "RC-GOV-UNTESTED", detectedBy="gate"),
    e("CAUSA", None, "process-rules-misbound", "Pinned process-evidence rules require repository indy-init-rehearsal-010; every praxis record INCORRECT-REPOSITORY", f"{CA}:83,181", "RC-GOV-UNTESTED", detectedBy="gate"),
    e("CAUSA", None, "gate-env-incomplete", "Gate suites step does not pass CAUSA_TEST_OWNER/REPO/BRANCH; no catalog repository named; catalog obligations cannot pass", f"{CA}:78,182", "RC-GOV-UNTESTED", ["RC-OWNER-PREREQ"], detectedBy="gate"),
    e("CAUSA", None, "owner-rule-change", "Owner chat decisions P17, P18, P18 extension, P19, preview option A and option C; none recorded as owner records", f"{CA}:138-147", "RC-GOV-UNTESTED", human=True),
    e("CAUSA", None, "ci-integrity", "Deploy credential scan died silently under bash -e -o pipefail (#5)", f"{CA}:161", "RC-CI-HARNESS"),
    e("CAUSA", None, "coordinator-error", "Coordinator misdiagnosed anonymous sandbox browser access as a token problem; relay workaround denied as containment escape", f"{CA}:163-164", "RC-ENV-SANDBOX", detectedBy="coordinator"),
    e("CAUSA", None, "provider-divergence", "403 rate limit shown as 'refused' (same class as R7 KD-020)", f"{CA}:165", "RC-PROVIDER-MODEL", ["RC-FIX-REGRESSION"]),
    e("CAUSA", None, "lane-errors", "A lane edited the read-only SRC checkout; wrong SHAs sent; a lane seeded another lane's double; stray server on port 4321", f"{CA}:167", "RC-PARALLEL-WRITE", ["RC-CI-HARNESS"]),
    e("CAUSA", None, "owner-found-defects", "Owner-reported defects by hand: list cards 'Not known', reopened copy not editable, duplicate hypothesis layout, graph unusable on phone", f"{CA}:168-171", "RC-UI-SPEC", human=True, detectedBy="owner"),
    e("CAUSA", None, "persistence-defect", "Rebase-on-moved-head save could encode commands twice (0695219)", f"{CA}:171", "RC-CONCURRENCY", detectedBy="self"),
    e("CAUSA", None, "demo-from-branch", "Demonstration deployed from integration branch slice/SL-T20, not main; owner disabled Pages workflow ~21:01Z", f"{CA}:88,136", "RC-GOV-UNTESTED", human=True),
    e("CAUSA", "2026-11-07T21:23:00Z", "verdict", "No governed acceptance: ledger 0/203 mandatory integrated (CONTINUE_REQUIRED); main holds setup, T10, T11; PR #6 option C not completed", f"{CA}:1,22-27,185-194", "RC-GOV-UNTESTED"),
)
