# Dokimos inspection (kemiller2002/dokimos @ main 717103f, 2026-10-23)

> Agent-generated read-only inspection report (2026-10-23), kept as the evidence CURRENT-STATE.md cites. File and line references are to the commit named below.

Read-only. Nothing was modified. No build was run locally; CI is the evidence for build and test results.

## 1. Responsibility, versions, interfaces
- README.md:3-13: an evidence-based code-quality system. "Metrics over time are Requirement 0" (README:9). Dokimos owns code-quality measurement and longitudinal evidence. Security belongs to Aegis/Tutors, process telemetry to Praxis/ROS, state legality to Ordo (README:13).
- PROJECT-CHARTER.md: mission and constraints. Evidence is never fabricated, missing data never counts as zero, definitions are versioned, history is immutable.
- HANDOFF.md:9-12: says the tool is operational (snapshots, comparison, policy, evidence store, gates, results, Forma UI, Folio output). It is stale: it mentions only v0.1.0 and v0.2.0.
- Releases (GitHub): dokimos-v0.1.0 (2026-09-29), 0.2.0 (10-02), 0.3.0, 0.4.0, 0.5.0 (all 10-13), 0.6.0 (10-19), 0.7.0 (10-20, latest). Directory.Build.props:11 gives Version 0.7.0.
- release/echelon.release-input.json:7-33 declares the provided capabilities: quality.snapshot, quality.compare, quality.evaluate, quality.history, completion.verify, completion.verify-attested, echelon.repository-lifecycle.
- CLI (src/Dokimos.Cli/Program.fs:447-492): analyze, snapshot, compare, ecir audit, ecir recognition-audit, construction verify, behavior verify, completion verify, evaluate, results, store, history, ratchet, identity, init/status/verify/doctor/upgrade. Exit codes are listed at Program.fs:464 (0 continue, 1 fault, 2 invalid, 3 evidence unavailable, 4 policy failure/regression, 5 store conflict, 6 invalid exceptions).
- GitHub action: actions/quality-gate/action.yml (with gate.sh and install.sh). It installs a pinned Dokimos release, snapshots, compares with the accepted baseline in the evidence branch `dokimos-evidence`, evaluates policy and persists evidence. Outputs: disposition, exit-code, snapshot-id, dokimos-version (action.yml:67-79). HANDOFF.md:11 says it was proven in Aegis.
- Two "quality result" formats:
  a) `dokimos.results` SchemaVersion 1.0.0 (schemas/dokimos-results.schema.json). Fields: Overview.Disposition ∈ {passed, passed-with-warnings, failed, required-evidence-unavailable, incompatible-snapshots}, Outcomes, Improvements, Regressions, Findings, Hotspots, Trends, Provenance (Repository, Revision, Ref, CollectedAt, DokimosVersion, ConfigurationId, AnalyzedScope, Analyzers[id, version, state], Policy, Performance), and Unavailable.
  b) Completion receipt `dokimos.completion-verification/1` (schemas/dokimos-completion-verification.schema.json:8-64). Fields: Verdict verified|rejected (exit 0|4), WorkItemId, Commit, VerificationRevision (40/64-hex), PacketDigest, EvidenceDigests (sha256:), ReusedEvidenceIds, and Diagnostics with code pattern DOK.COMPLETION.*. The input is `dokimos.completion-authority/1` (schemas/dokimos-completion-authority.schema.json). It carries fencing generation, the expected commit, the Ordo contract digest, required requirement/decision/conflict/validation IDs, evidence[Id, Digest, Revision, Status, Reusable, ObservedAt?, Validation?, Attestation?], optional TrustedVerifierKeys (ECDSA P-256 DSSE, added in 0.7.0, PR #47) and ValidationPolicyDigest.
  Other schemas: construction-verification 1.2.0, behavior-verification, recognition-audit/1, ecir-audit/1, ratchet, snapshot, comparison, evaluation, history.

## 2. Praxis install and intake
- Pinned Praxis version is **3.7.2**: .echelon/ros.json:5 `installedVersion`, read by ./praxis:17. Fallback ros.json:4 `rosVersion` is 3.1.4 (stale). The AGENTS.md template is from Praxis 3.7.1 (AGENTS.md:306). The ./praxis launcher installs the native release into ~/.echelon/tools/praxis/<ver> (praxis:28-35).
- Intake location: `.praxis/inbox/documents/`. Processed claims are in `.praxis/processed/INPUT-*/{claim.json, source/}`. There is no `input-documents/` directory.
- Lifecycle: the claim schema is `praxis.inbox-claim/1`. States are claimed → completed, with derivations (kind requirement, target path). Example: .praxis/processed/INPUT-f1620e8ac38269ea/claim.json produced requirements/ENGINEERING-RELIABILITY.md. The verification record is docs/verification/requirements-ingestion-2026-10-18.md.
- Unclaimed in the inbox on main: 2026-10-21-ARCH-001-02-compiler-derived-architecture-rules.md, 2026-10-21-VAC-DOK-001-chained-regression-verification.md, 2026-10-22-VAC-002-P2-04-authority-review-routing.md. None has a claim or derived requirement.
- Requirements live in requirements/*.md:
  - REQUIREMENTS.md: R0–R13, using "SHALL" statements such as R0.1.
  - OPERATIONAL-REQUIREMENTS.md, WEBSITE-REQUIREMENTS.md.
  - COLOR-CONTRACT-VERIFICATION.md (RQ-DOKIMOS-COLOR-001).
  - ENGINEERING-RELIABILITY.md: RQ-DOKIMOS-REL-001, status draft, YAML front matter with derived_from INPUT id and provenance, DOK-REL-001..007.
- Work queue: .ros/work/queue.md. It has no work item for ARCH-001, VAC-*, VC-004 or provenance.

## 3. PRs
- **#51** "Dokimos intake: P3 rule provenance experiments". OPEN, unmerged, head 3bc8b21, base 717103f, +17 lines in 1 file. It adds .praxis/inbox/documents/2026-10-23-VAC-002-P3-03-rule-provenance-research.md with two requirements:
  - R-PROV-1: an experimental source-aware audit tracing business-rule functions, constants and branches to an accepted requirement or decision. It flags untraceable exemptions, defaults, superseded rules and inherited rules. Findings go to owners as questions and must not become a blocking gate.
  - R-REV-1: a targeted independent provenance review, non-blocking.
  The evidence claim is that "Every one of 36 confirmed unauthorized decisions across P3 stages reused an existing code-embedded rule" (source: cohort-based-engineering PR #21). Checks: CI build-test-gate and Praxis validate succeeded. One `validate` job (run 39961730514, probably Site validation) failed; I did not determine the cause.
- **#52** "VC-004: prototype provenance checks and targeted review". OPEN, unmerged, head 6894361, +16 lines in 1 file. It adds .praxis/inbox/documents/2026-10-23-VC-004-mechanical-provenance-verification.md:
  - prototype static provenance checks;
  - detect missing, stale or superseded provenance, unauthorized defaults and untraceable exemptions, and distinguish "lack of provenance" from "proven violation";
  - block only on a formally specified invariant violated with a validated checker; ambiguity becomes a non-blocking owner question;
  - no default gate until precision, recall and false-rejection rates are measured;
  - compatibility with the existing evidence contracts.
  #52 overlaps #51 heavily: both cite cohort PR #21, and #52 is the more mechanical, VC-framed version. Neither supersedes the other formally. Both are intake documents only, with no code.
- Other open PR: #40 "GH-34: universal UI layout/action conformance" (open since 10-14).
- Recent merged PRs:
  - #50 VAC-002-P2 intake (merge 717103f)
  - #49 ARCH-001-02 intake (c99c21b)
  - #48 VAC-DOK-001 intake (41e721f, squash)
  - #47 REL-003 attested completion, v0.7.0 (04b5f85)
  - #46 0.6.0 (828208f)
  - #45 freshness / validation binding (b33be89)
  - #44 completion verify (a8b4cf6, 4631e34)
  - #43 requirements ingestion
  - #39 recognition audit: conflicts settled by approved decision (32a3801)
  - #38 CONSTRUCT-010 decision completeness (5015040)
  - #37 recognition audit
  - #33 CONSTRUCT-008 mechanical-first checks
  - #32 behavior verify / adapter oracle
  - #31 CONSTRUCT-005 construction verify

## 4. Capability status
| Capability | Status | Evidence |
|---|---|---|
| Invariant verification against specified invariants | 5 Not yet specified | Plan `defineInvariant` operations are only parsed and classified for decision provenance (ConstructionModels.fs:96,139; ConstructionDecisionModel.fs:192,303). No checker verifies them. Behaviour is checked through frozen oracle cases instead. The only text asking for this is VC-004 req 4, in unmerged PR #52. |
| Rule provenance inspection | 2 Implemented but incomplete | It exists only for Ordo-generated construction. CONSTRUCT-010 decision completeness classifies each plan choice (required/approved/implied/unresolved/unsupported) and rejects fabricated or unapproved citations (docs/construction-verification.md:252-303; PR #38). The recognition audit checks conflicts settled by an approved decision (PR #39). There is no provenance audit for handwritten business rules; it is proposed only in #51 and #52, both unmerged. |
| Proven violations vs uncertain authority; route to owners | 3 Requirements documented, not implemented | VAC-002-P2-04-R1 is in the inbox on main (merged by #50) and is not yet ingested. The same ask appears in #51 and #52. Partial precursors: construction verdicts separate `incomplete`/`unknown` from `rejected`, and conflicts must be `escalated` (construction-verification.md:231). |
| Defect-class analysis | 5 Not yet specified | No Dokimos requirement or code. "Defect class" appears only in the vendored SDE method (.sde/method/CHANGE-CLASSIFICATION.md:83-86). |
| Quality result definitions Praxis could consume | 1 Implemented and verified | completion-verification/1 receipt plus completion-authority/1, released in 0.6.0 and 0.7.0, with tests (CompletionVerificationTests, CompletionAttestation*Tests, CompletionVerifyCliTests; PR #47 reports Core 322/322 and Cli 143/143). It carries sha256 digests and schema/Dokimos versions. `dokimos.results` 1.0.0 also exists. |
| Evidence reuse / validity conditions | 2 Implemented but incomplete | Reuse requires a host-set `Reusable` flag, status passed, and equal digest and revision (CompletionVerification.fs:375-382; docs/completion-verification.md:131-138), plus a freshness window. There are no validity conditions on source, dependency or tool/analyzer digests. DOK-REL-007 (ENGINEERING-RELIABILITY.md:42) asks for documented reuse rules. |
| Dependency-aware / impact-based check selection | 5 Not yet specified | No requirement or code. DOK-REL-007 only covers avoiding duplicate runs. |
| Mutation testing / oracles / baselines | 2 Implemented but incomplete | Oracles: the frozen DOK-ORACLE-TIMER-1 (oracles/construction/time-entry-timer), construction verify and behavior verify, with Dokimos-observed runs (PRs #31, #32). Baselines: baselines/accepted-snapshot.json, quality/baseline.json, the ratchet DOK-R001..R008 (docs/quality/RATCHET-RULES.md:115-122), and quality/exceptions.json. Mutation testing: none. It is only requested as "adversarial and mutation fixtures" in COLOR-001.5 (requirements/COLOR-CONTRACT-VERIFICATION.md:47). |

## 5. VAC
- VAC-001: referenced only in VAC-DOK-001 (inbox, main). It proposes chained regression verification with per-requirement isolation (R1–R3, P3 priority). Its benefit is not demonstrated: 0 regressions in 96 units.
- VAC-002-P2: inbox document VAC-002-P2-04. R1 classifies findings as unauthorized (blocking) or ambiguity (owner question, non-blocking). R2 keeps the authority-record checks RC1–RC3 as candidates. Evidence class: "Supported but preliminary".
- VAC-002-P3: only in PR #51 (open).
- VAC-002-P1: no mention anywhere.
- "Unauthorized decision": appears only in PR #51. The code has `unauthorized-dependency` and `unauthorized-file-mutation` (ConstructionChecks.fs:27; ConstructionMechanicalModel.fs:146), which are construction mechanics, not authority.
- "Inherited rule": PR #51 only. In code, "inherited" refers to MSBuild `$(NoWarn)` (RATCHET-RULES.md:116).
- "Exemption": PR #51 and #52 only, plus one fixture (tests/fixtures/construction/time-entry-expanded-01/blueprint.json). Waivers and exceptions exist in quality/exceptions.json (schema dokimos-quality-exceptions) and in construction `--authorization`.

## 6. Tests and CI
- Run locally (HANDOFF.md:17-23): `./praxis registry check`, `./praxis validate`, `dotnet restore Dokimos.sln`, `dotnet build -c Release`, `dotnet test -c Release --no-build`.
- Test projects: tests/Dokimos.{Domain,Core,Cli}.Tests.
- Workflows:
  - ci.yml: debounce 600s; action-install; build-test-gate, which builds, checks identity, runs tests, validates the package and runs the self-gate.
  - praxis-validation.yml: registry check and validate.
  - ecir-fast-validation.yml, site-validation.yml, deploy-pages.yml, release.yml, reconcile-icon-audit.yml.
- Status on main at 717103f: CI success (run 39885212823) and Praxis validation success (39885212831). Deploy site FAILED on the last two pushes (39885212834, 39846221453); the cause was not determined because the log tail shows only cleanup.

## 7. Mentions
- Rehearsal: none.
- Causa: none as a word (case-insensitive hits are "causal").
- cohort-based-engineering: the 3 inbox documents plus PRs #51 and #52.
- CONSTRUCT-008: implemented by PR #33, the mechanical-first checks (ConstructionMechanical*.fs; tests ConstructionMechanicalTests and MechanicalFirstCliTests; tests/fixtures/construction/README.md:24).
- ARCH-001: only the ARCH-001-02 inbox document (PR #49). It proposes a compiler-derived (FCS) architecture rule family as the successor to the regex DOK-R008, with a zero-tolerance mode, deterministic/heuristic/review classes, and digests in reports. Not implemented.

## Not determined
- The cause of the Deploy site failures and of PR #51's failing validate job.
- Whether Praxis actually consumes the completion receipt today; that is not verifiable from this repository.
- Results of a local build or test run; none was run.
- Any VAC-002-P1 content.
