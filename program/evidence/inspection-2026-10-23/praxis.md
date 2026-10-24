# Praxis repository inspection (kemiller2002/praxis)

> Agent-generated read-only inspection report (2026-10-23), kept as the evidence CURRENT-STATE.md cites. File and line references are to the commit named below.

Inspected: 2026-10-23. Local clone `/home/user/praxis`, `main` = `7bff93f1` (Merge PR #284), history deepened with `git fetch --depth=200`. Read-only: no Praxis command was run and nothing was modified. GitHub data came from the MCP tools (PRs, releases, Actions runs, job logs).

---

## 1. Responsibility, released version, distribution and pinning

### Responsibility
- README.md:1-8: "Praxis is Echelon Foundry's repository operating system." The package identity `@echelon-foundry/repository-operating-system` is kept for compatibility. Praxis provides initialization, verification, diagnostics and upgrade tooling "that makes research, engineering, decisions, and handoffs durable without relying on conversation history".
- README.md:14-34 lists what it provides: a work protocol (begin/block/resume/complete, configurable completion evidence, attribution events); canonical research records (journals, REPs, theories, evidence, with supersession rules and generated registries); adaptive execution telemetry ("distinguishes unavailable from zero and observed from derived"); agent identity and provenance; validation; and CI.
- AGENTS.md (GV-START-001 v1.11.0) is the agent contract:
  - Mission (AGENTS.md:49-51).
  - Authority order (:66-68).
  - Core rules, including "Treat execution telemetry as evidence ... distinguish zero from unavailable" (:70-81).
  - Handoff contents (:83-85).
  - The work protocol `work begin` → `step` → `work checkpoint` → `work complete --evidence TYPE=PATH` → `registry build` → `validate` (:87-91).
  - Upstream sync every 30 minutes (:93-119).
  - Durable checkpoints and continuity, where `requireDurableCheckpoint` makes completion refuse un-checkpointed work (:121-164).
- The governance index is `docs/00-governance/README.md`, plus AI-Repository-Operating-System.md, Agent-Operating-Manual.md, Engineering-Standards.md, Governance-Decision-Log.md and the REP specification.
- Praxis is the runtime authority for work execution. Ordo is the semantic authority (requirements/EXECUTION-ORCHESTRATION.md:11-14; docs/ordo-observation.md:7).

### Released version
- `release.json` version is **3.19.0** (release.json:3). The remote protocol is 1.4.
- Git tags run up to `v3.19.0` (`git ls-remote --tags`). The latest GitHub Release is "Praxis v3.19.0", published 2026-10-21T07:01Z. Earlier releases: 3.18.0 (10-21), 3.17.0 (10-20), 3.16.0 (10-20), 3.15.0 (10-19), 3.14.0 (10-19).
- **Unreleased on main after 3.19.0:** `173cae20` REL-TOKEN-003 `praxis work finish`. `git merge-base --is-ancestor 173cae20 e29f1b5e` is false, so `work finish` is not in any release yet. Everything else after the release is intake documents only (PRs #281-#284).

### Distribution and downstream pinning
- PACKAGE-USAGE.md:11-30 describes two channels:
  - native bundles on GitHub Releases (`scripts/install-native.sh|ps1`, `echelon install praxis`, `scripts/praxis-bootstrap.sh` with attestation verification);
  - a .NET global tool, `dotnet tool install -g EchelonFoundry.Praxis`.
  - npm is retired (DF-ROS-2026-A044, DF-ROS-2026-A049). Legacy `ros-fs-<platform>` binaries are still built for old `./ros` launchers.
- Pinning (docs/upgrading.md:182-189):
  - A scaffolded repository pins `.echelon/ros.json` `installedVersion`, falling back to `ros.json` `rosVersion`.
  - Its generated `./praxis` launcher installs and runs that exact release under `~/.echelon/tools/praxis/<version>/`.
  - `praxis upgrade` moves the pin. The shared `.echelon/toolchain.json` `praxis` pin is also bumped (docs/upgrading.md:83-87).
- The Praxis repo pins itself:
  - `.echelon/toolchain.json` = `{"ordo":"1.5.0","praxis":"3.12.0"}` (WI-0101, PR #261). CI job `pinned-release-validate` validates the repo with that pinned release (.github/workflows/praxis-validation.yml:50-75). **The self-hosting pin is stale: 3.12.0 while 3.19.0 is released.**
  - `.echelon/sde.json` installedVersion is 1.5.0.
- `vendor/` holds vendored dependencies, not Praxis distribution artifacts:
  - `vendor/nuget/` has `echelonfoundry.ordo.core.1.8.2`, `ordo.construction.1.8.2` and `limen.routing.0.9.0` nupkgs with `.lock` files (CONSTRUCT-008, commit 36e1c136);
  - `vendor/forma/` has design-system 0.4.1.
  - Note the Ordo mismatch: vendored 1.8.2 against the toolchain pin of 1.5.0. Draft PR #266 proposes pinning Ordo 1.16.1.
- `starter/greenfield` and `starter/project-administration` are scaffold templates (HANDOFF.md, PROJECT-CHARTER.md, manifest.json and so on), not a pinning mechanism.

---

## 2. Intake: `input-documents/` vs `.praxis/inbox/documents/`; requirements and work items

### Which version introduced the inbox
- `.praxis/inbox/documents/README.md` was added by `d54bd6db` (2026-09-26, WI-0064). It is an ancestor of the 3.7.0 bump, so the directory existed by 3.7.0. Requirement: requirements/PRAXIS-DUAL-ENTRY-RECONCILIATION.md items 8-11 and the "Required repository layout".
- The crash-safe lifecycle CLI (`praxis inbox claim|derive|complete|release|reject|recover|show|list`) arrived in `01f23532` (2026-10-06, PRAXIS-MISC-01, DER-09/DER-10).
  - It is **not** an ancestor of the 3.7.2 release commit `42f478f3`, and **is** an ancestor of the 3.8.0 release commit `48bb3ba5`.
  - **So the canonical inbox lifecycle first shipped in Praxis 3.8.0 (2026-10-07).**
- `src/Praxis.Infrastructure/Work/FileInputInbox.fs:17,27`: the pending directories are `[InputDocuments.canonicalRelative; InputDocuments.legacyRelative]`, so `input-documents/` is read as a legacy pending location. `README.md` is excluded (:64).
- docs/fallback-reconciliation.md:70-110 documents the lifecycle table (pending → `.praxis/processing/<claim-id>/` → `.praxis/processed/` or `.praxis/rejected/documents/`). It also documents that `complete` is refused until derivations are committed in HEAD.
- Tests: tests/Praxis.Tests/InputInboxTests.fs. It crashes every step and recovers, and covers a legacy-path claim ID (:150).

### Does `input-documents/README.md` conflict?
- `input-documents/README.md` (last touched by b5f8d738, 2026-09-10, before the inbox existed) says to "Move or copy accepted material into its canonical location" and "Leave this directory empty after a completed intake run, except for this file."
- `.praxis/inbox/documents/README.md` says to "leave the source unprocessed until those derived changes have been durably reconciled" and to use `praxis inbox claim|derive|...`.
- The outcomes do not contradict each other: both end with the directory empty. The mechanism does conflict. The legacy README predates the claim/derive/complete lifecycle, does not mention it or `.praxis/processing/` claims, and invites an ad-hoc "move or copy". It was never updated to point at the canonical inbox. **Its "leave empty" rule is currently violated**, because two non-README files have sat there unprocessed since September (below).

### The 3 files currently in `input-documents/`
| File | Origin | Content | Processed? |
|---|---|---|---|
| README.md | b5f8d738 (2026-09-10) | legacy intake instructions | n/a |
| rfa.md (8,424 B) | b5f8d738 (2026-09-10) | `RP-RFA-2026-001` "Research Frontier Analysis" agent mission prompt (front matter: research_area research-operating-system, status active). A research-agent persona prompt, not a Praxis requirement | **No.** No claim under `.praxis/processing/processed/rejected`, and no reference to `RP-RFA-2026-001` anywhere outside input-documents |
| ros-ordo-handoff-and-bootstrap-requirements.txt (23,959 B) | 1567578e "moved to new repo" (2026-09-19) | "ROS Requirements — Ordo Decision Handoff and Automatic Ordo/SDE Bootstrap"; about 40 requirements `ROS-ORDO-001..072`. Sections: serialization, resume/staleness, storage/versioning, checkpointing, handoff minimization, security, handoff observability, automatic Ordo bootstrap, version policy, update checks, integrity, idempotency, offline behaviour, testing, Definition of Done | **No.** `grep ROS-ORDO-0` finds no reference outside input-documents and there is no claim. Some of it overlaps existing features (`praxis ordo handoff`, `echelon setup`, checkpoints), but never through intake, and none of it is traced |

Because `FileInputInbox` treats `input-documents/` as pending, both files should show up as pending in `praxis inbox list`. I inferred this from the code and did not run the command.

### Canonical inbox state
- Pending in `.praxis/inbox/documents/` on main, unclaimed with `.praxis/processing/` empty:
  - REL-ROUTE-001;
  - REL-TOKEN-001 (P1 measurement correctness);
  - REL-TOKEN-002 (P1);
  - ARCH-001-01;
  - REL-TOKEN-004 (minimal tool profile, P3);
  - VAC-CONT-001;
  - VAC-002-P2-05.
- Processed (9): INPUT-046652470c22465c (REL-001 F1-F6), -0578a52a35aff58a (REL-GATE-001), -3af3690702599679 (REL-TOKEN-003), -59f6f1fb81fc30c2 (REL-GATE-002), -5d2d693879d4ecf3 (REL-GATE-004), -684a43561de78083 (PRX-VIS-001), -695a4e7723d7f795 (ENGINEERING-RELIABILITY-001), -75d557dd4372a265, -b08b009bbcfa9297 (REL-GATE-003).
- Open PRs #285 and #286 each add one more inbox document (section 3).

### How requirements are stored
Requirements live in three places:
1. **Canonical RQ records:** `research/requirements/RQ-ROS-2026-ANNN--slug.md`, 33 files, A001-A033. They are Markdown with YAML front matter (`id, title, status, version, owners, created, updated, priority, related_documents, tags, derived_from: [INPUT-…], provenance.contributions`). Example: research/requirements/RQ-ROS-2026-A033…md:1-27. They are projected into `registries/requirements.json` by `praxis registry build`.
   - Status values seen: implemented (A001-A012, A020, A024-A026), verified (A013-A019, A027), accepted (A021-A023), draft (A028-A033).
2. **Requirement specs:** `requirements/*.md` with numbered IDs inside, for example `PRX-EXEC-*` in EXECUTION-ORCHESTRATION.md ("Accepted; partially implemented", with a per-ID status table), `PRX-PLAN-*`, `PRX-GRP-*`, DER-01..26 and `PRX-QUAL-*`.
3. **Decision records:** `research/decisions/DF-ROS-2026-ANNN--slug.md` (53 files). Evidence lives in `research/evidence/EV-*`.

### How work items are derived
- Work items live in `.ros/work/queue.json` (317 items; `queue.md` is a projection). They are created with `praxis add` or captured as `captured`, `ready`, `active` or `complete`.
- An intake derivation is recorded in the claim's `claim.json` (`praxis.inbox-claim/1`) as `{kind, targetKind, target, summary, locator, actor, executionId}`.
- Recent reliability intakes (REL-GATE-*, REL-TOKEN-003) derive `kind: requirement` **directly to source-file paths**, for example `.praxis/processed/INPUT-3af3690702599679/claim.json` → `src/Praxis.Application/Work/WorkFinish.fs`. They create no RQ record, so REL-* requirements exist only as work items, the processed source documents and code. Older intakes created RQ records (RQ-A031..A033 from INPUT-684a…, -695a…, -75d5…; docs/verification/requirements-ingestion-2026-10-18.md).
- **Status drift:** RQ-ROS-2026-A032 ("Atomic work ownership and independently verified completion") is still `status: draft`, although PRAXIS-REL-001..013, REL-GATE-003/004 and REL-TOKEN-003 implemented it and are `complete` in queue.json.

---

## 3. Pull requests

### PR #285: "Praxis intake: P3 minimal authority contract"
- **State: open**, not draft, not merged, no merge commit. Head `requirements/vac-002-p3-evidence` @ `43e94907`, base `7bff93f1`. Created 2026-10-23T13:30Z.
- Change: one file, +13 lines, `.praxis/inbox/documents/2026-10-23-VAC-002-P3-01-minimal-authority-contract.md`.
  - **R-PRAX-1:** add the frozen four-sentence authority contract from cohort-based-engineering VAC-002/P3 verbatim to the standard implementation-agent brief, with its version recorded in telemetry.
  - Evidence: 3/18 unauthorized decisions with the contract vs 7/18 without, p=0.125, **inconclusive**.
  - It explicitly says not to add a mandatory checklist or typed decision records as defaults. Source: kemiller2002/cohort-based-engineering PR #21.
- Supersession: it effectively supersedes the gating condition in VAC-002-P2-05 on main, which said to add an Authority section "once VAC-002-P2-01 has measured the section's effect". P3 now supplies that measurement (inconclusive) and still recommends adoption on policy grounds. Neither document marks supersession formally.
- CI: the `validate` job **failed**. The other 10 jobs passed (lifecycle ×3, worker-checklists ×3, local-worker-portability ×3, pinned-release-validate, reconcile). The same `validate` failure exists on main (section 6), so it is very likely the same two environment-sensitive tests. I did not pull this PR's log.

### PR #286: "VC-003: preserve decision authority across Praxis ingestion"
- **State: open**, not draft, not merged. Head `requirements/verified-construction-shift-20261023` @ `f67ee81b`. Created 2026-10-23T13:35Z.
- Change: one file, +15 lines, `.praxis/inbox/documents/2026-10-23-VC-003-authority-preserving-ingestion.md`. Requirements:
  1. extend or map the Praxis IR to carry stable requirement IDs, accepted decision IDs, provenance, source revision, supersession and an explicit unresolved status;
  2. code-embedded rules are observations, not requirements;
  3. no self-authorization; a missing authority produces an unresolved question;
  4. preserve the P3 frozen contract and its version, depending on #285 R-PRAX-1;
  5. **export a deterministic, schema-validated handoff contract to Ordo with a requirement-coverage mapping and an unresolved-policy list, plus compatibility and migration rules**;
  6. capture the incremental cost and tokens; do not require full repeated verification at every intermediate commit.
  - Acceptance: a versioned schema, contract tests, an Ordo integration fixture, and staging behind an experimental opt-in until VC-001 evidence exists.
- Relationship: it complements #285 and does not supersede it (it cites it). It overlaps the unprocessed `input-documents/ros-ordo-handoff-and-bootstrap-requirements.txt` (ROS-ORDO-001..) on Ordo handoff serialization. Neither supersedes the other formally.
- CI: `validate` failed; the rest passed.

### Other open PRs (18 in total, including #285 and #286)
- #267 (draft) GH-260 UI layout conformance.
- #266 (draft) CONSTRUCT-010: pin Ordo 1.16.1 and versioned decision records.
- #239 (draft) pinned native history reconciliation.
- #238 (draft) bind concrete validators to independent candidate checklists.
- #202 (draft) A021 publication package.
- #176 (draft) control plane PRAXIS-CTL-02..05.
- #141 (draft) EX-A022 experiment setup.
- #137 (draft) shared Echelon release v2 contract.
- #133 (draft) A021-R2 replication.
- **#122 (open) "Debounce commit-driven CI and keep agents working between pushes" (GH-121)**: relevant to checkpoint-driven CI, unmerged since 2026-09-29.
- #106 retire npm (stale; npm was already retired by other means).
- #81 and #78 (draft) provenance interchange.
- #75 change-health metrics.
- #71 (draft) artifact root scope.
- #51 ROS Central migration.

### Recent merged PRs touching reliability, completion gates, evidence, verification, telemetry and checkpoints (newest first)
| PR | Merged | Title (abridged) |
|---|---|---|
| #284 | 10-23 | VAC-002-P2 intake (candidate agent-contract Authority section) |
| #283 | 10-21 | ARCH-001-01 intake (independent architecture validation at completion) |
| #282 | 10-22 | VAC-CONT-001 continuity evidence and per-item usage intake |
| #281 | 10-21 | REL-TOKEN-003 `praxis work finish`; queue REL-TOKEN-004 |
| #280 | 10-21 | REL-GATE-003: attested/unattested labelling; requireVerifiedCompletion implies attestation |
| #279 | 10-21 | REL-GATE-004: policy and trust root from the protected branch; queue REL-TOKEN-001..003 |
| #278 | 10-20 | Intake: REL-001 F1-F6 derivations |
| #277 | 10-20 | REL-001 F1-F6: attested evidence (DSSE receipts), clean completion identity, derived completion, per-agent attribution, price tables, rollout gate |
| #276 | 10-20 | Intake REL-001 follow-ups |
| #275 | 10-20 | PRAXIS-REL-008: Ordo execution readiness for verified completion (REL-GATE-002) |
| #274 | 10-19 | PRAXIS-REL-005: bind completion evidence to host-observed validation results (REL-GATE-001) |
| #273 | 10-19 | Reliability integration: Ordo contract admission, atomic ownership, Dokimos-verified completion, cost telemetry |
| #264 | 10-14 | WI-0102 cumulative transcript usage and cost attribution (CONSTRUCT-010 Phase 6) |
| #263 | 10-14 | CONSTRUCT-010 compact typed handoff /3, worker isolation, construct check |
| #261 | 10-13 | WI-0101 pin 3.12.0 and validate the pinned release in CI |
| #259 | 10-13 | RQ-A030 reclassification and external evidence references |
| #257 | 10-13 | CONSTRUCT-008 mechanical-first construction |
| #255 | 10-13 | Mandatory construction-package scope verification in worker checklists |
| #248 | 10-12 | Probe-qualified Linux containment for local workers |
| #244 | 10-12 | Finalize an interrupted predecessor's steps on completion |
| #241 | 10-12 | Concrete local coordinator/worker runtime |
| #240 | 10-12 | Connect concrete checklist evidence to guarded native completion |
| #237 | 10-12 | Concrete pinned local validator runners |
| #236 | 10-12 | Enforce independent candidate-bound worker checklists |
| #232, #229, #225, #224, #222, #221 | 10-09..10-11 | Signed worker host; local-agent foundations; ECIR host authority; P-256 receipts; ECIR-003 cohort approval; fail-closed observations |
| #227 | closed, not merged | Local handoffs, durable worker output, integration recovery |

---

## 4. Capability status

Status scale: 1 implemented and verified, 2 implemented but incomplete, 3 requirements documented but not implemented, 4 experimental, 5 not yet specified.

| ID | Capability | Status | Evidence |
|---|---|---|---|
| A1 | Dependency-aware verification selection | **5** | No code selects tests or validators from changed files, interfaces or previous evidence. The nearest thing is risk-declared obligations: `praxis.work-risk/1` (src/Praxis.Domain/Work/WorkRisk.fs:1-80, PRX-QUAL-020..022). The declared ChangeClass and RiskLevel derive required verification-matrix *dimensions* (HappyPath, Negative, Corruption, Concurrency, Compatibility, Recovery, LiveEffect), not test selection. Tests: CompletionObligationsTests.fs. Worker checklists use a "host-selected" validator map (DF-ROS-2026-A067) with no impact analysis. No RQ, DF or intake specifies impact-based selection. ARCH-001-01 and REL-ROUTE-001 (inbox) select a *protocol or validation*, not tests. |
| A2 | Evidence reuse with invalidation | **2** | Invalidation exists and is coarse:<br>• Completion evidence `praxis.validation-result/1` is bound to the exact clean revision and claim. Stable codes `PRX.COMPLETION.EVIDENCE_STALE` and `EVIDENCE_REVISION_MISMATCH` (src/Praxis.Domain/Work/ValidationResult.fs:24-63). `complete-verified` requires HEAD = receipt commit (PR #277, F3).<br>• Worker checklists digest packet + candidate commit + manifest digest + policy revision + validator input-closure digest, giving `checklist-evidence-stale` (src/Praxis.Domain/Work/WorkerChecklist.fs:14-174). DF-A067:63-66 says "Cache reuse requires the exact current identity, not a historical pass."<br>• The execution evaluator identity is a sha256 over the closure (gate code, config, test selection, schemas, fixtures, policies, dependencies) (docs/execution-runtime.md:42-46). Stale-verification refusal is in src/Praxis.Domain/Execution/Governance.fs:1102.<br>• CI step "Checklist refusal and input invalidation".<br>Missing: reuse across commits when the relevant closure is unchanged, invalidation on toolchain or environment changes, and any dependency-granular invalidation. Any commit change invalidates everything. |
| A3 | Deterministic, idempotent completion with structured refusals | **1** (caveats) | Commands: `work complete-verified --id --token` (derived completion, PR #277, released 3.17+) and `work finish` (src/Praxis.Cli/WorkFinishCommands.fs; exit 0 = verified or replayed, 3 = refused, 2 = invalid arguments, 1 = storage; `--json`). About 45 stable `PRX.COMPLETION.*` refusal codes, for example EVIDENCE_*, RECEIPT_*, POLICY_CHANGED, UNTRUSTED_AUTHORITY, CONTRACT_NOT_READY, DIRTY_WORKTREE, HEAD_MISMATCH. Policy is read from the protected base (REL-GATE-004); Ordo readiness is gated (REL-GATE-002); `requireDurableCheckpoint` is in AGENTS.md:149-153 and ros.json:61. Tests: AttestedCompletionTests.fs ("finish … replays", PROBE-3/4 refusals), WorkClaimTests, CompletionObligationsTests. They pass in CI (see the log in section 6).<br>Caveats:<br>(a) `work finish` is unreleased (after 3.19.0);<br>(b) the real-Dokimos end-to-end cases SKIP in CI (`PRAXIS_TEST_DOKIMOS_DLL` unset);<br>(c) verified completion is opt-in and **not enabled** in Echelon repositories (docs/verified-completion-rollout.md:3; PRAXIS-REL-006 still `captured`), and the Praxis repo itself sets only `requireDurableCheckpoint`;<br>(d) the CI `validate` job on main is currently red for unrelated reasons;<br>(e) RQ-A032 is still `draft`. |
| A4 | Real-provider test ordering | **5** | Nothing in src, docs, requirements or research specifies ordering of real-provider tests. Not a Praxis responsibility. The only related item is that real-Dokimos end-to-end tests are skipped unless `PRAXIS_TEST_DOKIMOS_DLL` is set. |
| A5 | Execution telemetry (tokens, cost, wall time, CI, corrections, accepted requirements; unavailable ≠ zero) | **2** | Implemented:<br>• Tokens by bucket, cost via a versioned `praxis.price-table/1`, `time.wall_ms` plus a separate calendar/overlap `timing`, and `supported-unavailable` never zero (docs/development-telemetry.md:56-87, 287, 365-389, 449-450, 573-670; DF-ROS-2026-A010; RQ-A013..A019 `verified`).<br>• `telemetry reliability-report` emits verifiedRequirements, firstPassVerificationRate, reworkFrequency (correction-cycle proxy) and completionRejectionFrequency (src/Praxis.Domain/Telemetry/ReliabilityReport.fs:499, 816-821), plus per-agent attribution (PRAXIS-REL-010).<br>• Tests: Telemetry*Tests.fs (about 30 files) and ReliabilityPipelineTests.<br>Gaps:<br>• No CI-execution count is captured; CI enters only as planner observations (PRX-PLAN-020, captured).<br>• 287 of 307 execution records have no tokens because nothing auto-ingests transcripts (docs/development-telemetry.md:575-581); PRAXIS-REL-004 auto-ingest is `captured`.<br>• Claude Code output tokens are a lower bound (REL-TOKEN-002, pending in the inbox).<br>• No per-request ledger (REL-TOKEN-001, pending).<br>• No per-item windows within a continued session (VAC-CONT-001-R2, pending). |
| B1 | Preserving requirement IDs, authorized decisions, unresolved questions, source revisions and supersession; deterministic versioned handoff | **2** | Implemented:<br>• `praxis ordo handoff` with schema `ros.handoff-authority` v1 (schemas/ros-handoff-authority.schema.json): required repositoryRevision, source, stateFingerprint, facts, assumptions, **unknowns**, obligations, legalNextActions, **supersededResolutionIds**, authoritativeArtifacts, historicalDecisionReferences, completedVerification (docs/ordo-observation.md:60-79; src/Praxis.Domain/Ordo/Model.fs:225-294). Tests: OrdoObservationTests.<br>• Ordo contract admission carries `requirementKeys`, `authorizedDecisionIds` and `ORDO.CONTRACT.UNRESOLVED_CONFLICT` (src/Praxis.Domain/Ordo/ContractAdmission.fs:23-720; OrdoContractAdmissionTests).<br>• The local worker packet keeps the original requirementKeys and decisionIds per member (docs/local-agent-coordination.md:31-60).<br>• Inbox claims keep source SHA-256 and derivations; RQ records keep `derived_from` and provenance.<br>Gaps:<br>• No single Praxis→Ordo handoff with a requirement-coverage map and unresolved-policy list.<br>• No authority-vs-observation distinction.<br>• ROS-ORDO-001..072 never ingested.<br>• VC-003 (PR #286) is open.<br>• Recent REL intakes create no RQ records. |
| C1 | Minimal agent tool profiles | **3** | Specified only as an **unprocessed intake source**, `.praxis/inbox/documents/2026-10-21-REL-TOKEN-004-minimal-agent-tool-profile.md` (`minimal-worker`: Bash, Read, Edit, Write, no MCP). That document itself notes Praxis has no worker launcher. Execution roles and capability sets exist (PRX-EXEC-001..006; PRX-EXEC-002 "Partial"), but they are Ordo role authorities, not provider tool lists. |
| C2 | Durable context handoffs | **1** | `work checkpoint` and `work continue`, with verified durable checkpoints (HEAD = checkpoint = upstream head) and the predecessor recorded as interrupted (AGENTS.md:121-164; DF-ROS-2026-A042; RQ-ROS-2026-A022 `accepted`; docs/work-protocol.md). Tests: CheckpointCliTests, CheckpointDomainTests, CheckpointGuardTests, CheckpointPersistenceTests, ContinuationCliTests, RecoveryProofTests. They run in CI. `requireDurableCheckpoint: true` in ros.json:61. A group checkpoint (PRX-GRP-044) is captured, not done. |
| C3 | Typed inter-agent communication | **2** | The remote protocol is typed and versioned: `praxis.remote` request and response schemas (schemas/praxis-remote-request|response.schema.json; DF-ROS-2026-A041, A045; RemoteProtocolTests; protocol 1.4). Local coordinator↔worker contracts are `praxis.local-worker-packet/1` and `praxis.local-worker-result/1`, with strict decoding and bounds (docs/local-agent-coordination.md:31-60; LocalAgentHandoffTests; CI step "Portable handoff contracts"). The fallback envelope is protocol/praxis-envelope-v1.schema.json. Incomplete: "The complete coordinator-to-workers loop … do[es] not yet exist", and no adapter authenticates controller observations (docs/local-agent-coordination.md:153-160). DF-A060..A074 are all `draft`. |
| C4 | Dependency-aware parallel execution | **2** | A deterministic planner computes waves, a collision graph and max concurrency (PRX-PLAN-080..094; DF-ROS-2026-A046 "recommends … waves"; DF-A047 groups are advisory; DF-A053 grouped by default). There is a local runtime with worktrees and dispatch (PRs #241, #225). requirements/EXECUTION-ORCHESTRATION.md says "Accepted; partially implemented". The planner is shadow/advisory (PRX-PLAN-001, PRX-PLAN-161 "MUST only recommend"). |
| C5 | Checkpoint-driven CI | **3** | CI runs on every push and pull_request (.github/workflows/praxis-validation.yml:6-8). PR #122 "Debounce commit-driven CI" (GH-121) has been open and unmerged since 2026-09-29. PRX-PLAN-020 (observe CI for checkpoint commits) is a captured work item. No accepted RQ or DF makes CI checkpoint-triggered. |
| C6 | Critical-path scheduling | **2** | `criticalPath` in src/Praxis.Domain/Planning/Graph.fs:149; Scheduling.fs:56, 324; Grouping.fs:1790. PRX-PLAN-045 (SHOULD). Tests: PlanningTests.fs:257 ("16 critical path follows the longest hard-dependency chain") and :320. It is advisory and shadow-mode only (PLANNING-OPTIMIZATION.md:3, PRX-PLAN-001/161) and does not drive dispatch. |

---

## 5. Existing records that already specify parts of this

**RQ records** (research/requirements):
- RQ-ROS-2026-A013..A019, A027 `verified`: step telemetry, availability, cost provenance, evidence references.
- A022 `accepted`: durable checkpoints and continuity.
- A021 and A023 `accepted`: remote execution.
- A026 `implemented`: envelopes.
- A028 `draft`: local coordinator/worker handoffs.
- A029 `draft`: worker checklists require independently verified current evidence.
- A030 `draft`, but PR #259 merged: external evidence references at completion.
- A031 `draft`: visual-evidence gates.
- **A032 `draft`: atomic ownership and verified completion (implemented; status stale).**
- A033 `draft`: Design by Construction.

**requirements/ specs:**
- EXECUTION-ORCHESTRATION.md: PRX-EXEC-*; **PRX-ARCH-001 "Partial — Praxis re-implements Ordo semantics locally"** (:375, :562).
- PLANNING-OPTIMIZATION.md: PRX-PLAN-*, Accepted, shadow.
- PLANNING-WORK-GROUPS.md: PRX-GRP-*, Accepted phase one.
- CODE-QUALITY-HARDENING.md: PRX-QUAL-*, approved; risk obligations.
- PRAXIS-DUAL-ENTRY-RECONCILIATION.md: DER-01..26, approved.

**Decisions:**
- Accepted: DF-ROS-2026-A010 (adaptive telemetry), A037, A042 (durable checkpoints), A043, A041/A045 (remote protocol and inbox relay), A046/A047/A053 (planner and groups), A051, A052 (consume Dokimos/Ordo quality evidence at completion).
- Draft: A060-A074 (local coordinator, checklists, containment, construction).

**Work items** (.ros/work/queue.json):
- Complete: PRAXIS-REL-001, 005, 008-013; REL-GATE-003, REL-GATE-004, REL-GATE-004-LOCATOR; REL-TOKEN-003.
- **Captured (not done):**
  - PRAXIS-REL-002: qualify Dokimos 0.6.0.
  - PRAXIS-REL-003: release and qualify via Conditor and Registry.
  - PRAXIS-REL-004: auto-ingest transcripts at completion.
  - PRAXIS-REL-006: enable requireVerifiedCompletion in Echelon repositories.
  - PRAXIS-REL-007: REL-001 pilot replicates.
  - PRAXIS-PLAN-11: grouped-by-default review, which VAC-CONT-001 feeds.

**Pending intake sources** (not canonical): REL-ROUTE-001, REL-TOKEN-001, REL-TOKEN-002, REL-TOKEN-004, ARCH-001-01, VAC-CONT-001, VAC-002-P2-05, plus PR #285 (VAC-002-P3-01) and PR #286 (VC-003).

**CONSTRUCT:** CONSTRUCT-004/008/010 appear in commits and PRs (#250, #257, #263, #264, draft #266) and in Praxis code comments (src/Praxis.Domain/Telemetry/SessionTranscript.fs, Acceptance.fs, RequestAttribution.fs; Infrastructure/Planning/*). There are no CONSTRUCT-* work-item IDs in queue.json.

**cohort / rehearsal:** "cohort" is an ECIR/Ordo construction concept (cohort approval, `cohortId` in worker packets; DF-A071; docs/ecir-execution.md:40). "rehearsal" appears only in a `.ros` next-action string ("cross-repo clean-room rehearsal with Project Administration", queue.json:4267) and in remote-request fixtures. There is no Rehearsal capability.

---

## 6. Tests and CI

- How tests run: a custom F# test runner, not `dotnet test`.
  - `dotnet build Praxis.slnx -c Release`, then `dotnet tests/Praxis.Tests/bin/Release/net10.0/Praxis.Tests.dll`.
  - Suites: `--suite browser` (headless Chrome), `--suite pinned-release`.
  - Filters: `PRAXIS_TEST_FILTER`.
  - After the tests, the job checks the checkout is unchanged, then runs `./praxis architecture check`, `registry check` and `validate` (.github/workflows/praxis-validation.yml:10-48).
  - About 188 files under tests/Praxis.Tests; 2,358 tests on the latest main run.
- Workflows (.github/workflows): praxis-validation.yml (main gate), containment-qualification, deploy-pages, foundations-verify, native-release, praxis-reconcile(-apply), praxis-remote(-inbox), release, ros-fs-assets, site.
- Duration: the `validate` job takes about 17-24 minutes (the F# test step alone about 16 minutes). Windows worker-checklists take about 23 minutes. The full workflow wall time is about 23-29 minutes.
- **Main is currently red.**
  - Praxis validation runs on main for `2f4ce68e` (#282, 10-22) and `7bff93f1` (#284, 10-23) **failed**. Runs through `64005151` (#283, 10-21) passed.
  - Failing job: `validate`, step "F# tests": "2358 test(s); 2356 passed; 2 failed" (run 39885217729, job 120191711985). The two failures:
    1. `git status: outside a repository the outcome is unavailable rather than clean`. The golden test expects git's error text "(or any of the parent directories)" but the runner's newer git (2.55.0) prints "(or any parent up to mount point /) Stopping at filesystem boundary…". This is an environment-dependent assertion.
    2. `fence release: the version bump and remote enablement stamp work transitions with real millisecond timestamps`: "timestamps must strictly increase: …01:52:01.955Z then …01:52:01.119Z". This is a clock or ordering flake.
  - Both commits that turned main red only add documents, so the cause is runner or environment drift (a git upgrade), not those changes.
  - Because the test step fails, the browser tests, architecture check, registry check and `praxis validate` are skipped on main.
  - All other jobs (pinned-release-validate, lifecycle ×3, worker-checklists ×3, local-worker-portability ×3) pass.
  - The `validate` job on PRs #285 and #286 also fails.
- No local build or test run was attempted.

---

## 7. Causa, Rehearsal, VAC-001, VAC-002, P1/P2/P3

- **Causa:** no occurrence anywhere in the repo, `.ros` included.
- **Rehearsal:** no capability or record. One `.ros` next-action string mentions a "clean-room rehearsal" (queue.json:4267).
- **VAC-001:** cited only in the pending inbox document `2026-10-21-VAC-CONT-001-…md`.
  - 96 chained work units. A continuous agent was 40.9% cheaper per accepted requirement than a fresh agent with handoff (CI −48.1% to −33.0%), with 0 failures and 0 compactions. Reconstruction from verified state cost +86%.
  - Proposals: R1 record as evidence for the DF-A053 / PRAXIS-PLAN-11 review; R2 per-item usage windows inside one session; R3 defer restart-policy changes.
  - Source: cohort-based-engineering branch `claude/verified-agent-continuity-vfjrrx`.
- **VAC-002:** two documents.
  - P2 is in the pending inbox (`2026-10-22-VAC-002-P2-05-…md`): 0/48 unauthorized decisions with an "Authority" section, but the section's effect was not varied. R1 says to add it to the AGENTS.md template once P2-01 measures its effect.
  - P3 is in open PR #285 (R-PRAX-1, frozen four-sentence contract, 3/18 vs 7/18, p=0.125, inconclusive).
  - VC-003 (PR #286) builds on P3.
- **P1/P2/P3** mean two different things in Praxis:
  - **Priority labels** on intake documents: REL-TOKEN-001/002 are P1; REL-ROUTE-001, ARCH-001-01, VAC-CONT-001 and VAC-002-P2-05 are P2; REL-TOKEN-004 is P3.
  - **VAC-002 phases** P2 and P3, from cohort-based-engineering.
  - Separately, test names "P1..P4 postmerge" in PostmergeReconciliationTests are unrelated.

## Could not determine
- Whether `praxis inbox list` actually lists the two legacy files. Inferred from FileInputInbox.fs; not run.
- The exact failing tests on PR #285 and #286. Probably the same two as main; log not pulled.
- Whether downstream Echelon repositories currently pin 3.19.0. Only the Praxis self-pin (3.12.0) was inspected.
