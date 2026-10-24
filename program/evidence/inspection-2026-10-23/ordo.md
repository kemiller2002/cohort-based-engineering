# Ordo repository inspection (kemiller2002/ordo @ main d11e9cf, 2026-10-23)

> Agent-generated read-only inspection report (2026-10-23), kept as the evidence CURRENT-STATE.md cites. File and line references are to the commit named below.

Read-only. No builds run (no `dotnet` in container). CI results come from GitHub Actions.

## 1. Responsibility, releases, public interfaces
- Self-description: "State Directed Engineering" methodology repo + Ordo tool (README.md:1-25; PROJECT-CHARTER.md "Purpose"). Public name Ordo; research names SDE (DF-SDE-2026-0005, HANDOFF.md "Authoritative changes").
- The charter is stale at v0.3.0 (2026-09-05). Its "Next bounded outcome" is the first engineering validation, and WI-0019 is still `ready` (.ros/work/queue.md).
- Code (F#): src/Ordo.Core (ECIR, constructibility contracts, decisions, default plan, ledger, pattern recognition, execution governance), src/Ordo.Construction (deterministic F# generator), src/Ordo.Decisions (+ Providers.Anthropic), src/Sde.Core and Sde.Cli (the `ordo`/`sde` CLI), and src/Ordo.Site.
- Released versions: tags v1.4.0..v1.17.0. Latest is GitHub release "Ordo v1.17.0" (2026-10-20, tag commit bb43c26); distribution/package.json:3 says "1.17.0".
- Native release: release/echelon.release-input.json (executable `ordo`, alias `sde`, github-release mechanism).
- Packages: native-release.yml:87-95 packs `EchelonFoundry.Ordo.Core` and `EchelonFoundry.Ordo.Construction` as nupkg release assets (ordo-core.nupkg, ordo-construction.nupkg). npm `@echelon-foundry/sde` is still a compatibility channel; the publish run on 1.17.0 was skipped (gated).
- CLI (src/Sde.Cli/Args.fs:101,195-221): init, status, verify, upgrade, doctor, boundary assess, and ecir validate|check|scaffold|recognize. The CLI has no construction/generation command (HANDOFF.md WI-0044 "Not done": "No `sde` command: the CLI has no construction-plan family").
- Wire contracts consumed by Praxis and other hosts: schemas/ecir-v1.schema.json, ordo-construction-plan.v1 and vocabulary-2/3/4, ordo-execution-contract.v1, ordo-execution.v1, ordo-boundary-amplification.v1. In-code wires (docs/architecture/*): ordo.construction-decisions/1-3, ordo.default-plan/1, ordo.requirements-ledger/1, ordo.choice-classification/1, ordo.pattern-registry/1, ordo.pattern-recognition/1, ordo.delegation-contract/1, ordo.constructibility-readiness/1.

## 2. Praxis intake and installed version
- `.praxis/inbox/documents/` exists. It holds 3 unclaimed documents:
  - 2026-10-21-ARCH-001-03
  - 2026-10-21-VAC-ORDO-001
  - 2026-10-22-VAC-002-P2-03
- There is no `input-documents/` directory.
- Lifecycle: inbox document → claim → `.praxis/processed/INPUT-<id>/{claim.json,source/}` with schema `praxis.inbox-claim/1`, state completed, and a derivation → `research/requirements/RQ-SDE-2026-000N`. Three were processed on 2026-10-18 by openai/codex (execution EXE-20261018T124842421Z-f3f0c468):
  - INPUT-d68ba75aa37d75df → RQ-0001, visual intent
  - INPUT-8a37a8766a122b40 → RQ-0002, versioned constructibility contracts
  - INPUT-a385c22ff220f848 → RQ-0003, Design by Construction
  - All three RQs have `status: draft`.
- Version mismatch: ros.json `rosVersion: 1.2.1-main.16.1` (and README.md:3), but .echelon/ros.json `installedVersion: 3.7.2` (package @echelon-foundry/repository-operating-system).
  - The `./praxis` launcher (praxis:17-18) prefers `.echelon/ros.json` installedVersion, so the effective Praxis is 3.7.2 (WI-0042 "Move ordo to Praxis 3.7.2").
  - There is no vendored praxis/ directory; `./praxis` downloads the pinned native release to ~/.echelon.
- Where requirements live:
  - research/requirements/RQ-*: canonical, Praxis-derived.
  - .ros/work/queue.md: work items.
  - docs/architecture/*.md: per-feature specs, tracked as CONSTRUCT-0xx / ORDO-* / GH-*.
  - research/decisions/DF-SDE-*.
  - Upstream CONSTRUCT-008 validation lives in kemiller2002/research-documents.

## 3. PRs
- #103 "Ordo intake: P3 authorization admission defects": OPEN, not merged, mergeable clean, head fdb2ae9.
  - Adds one file: .praxis/inbox/documents/2026-10-23-VAC-002-P3-02-authorization-admission-defects.md.
  - Contents: R-ADM-1 (authorized deferral), R-ADM-2 (A5 self-citation), R-ADM-3 (narrow A6). It keeps executable authorization off the default path.
  - P3 evidence: 0 prevented, 10 false rejections, 4 harmful.
  - Source: cohort-based-engineering PR #21.
  - Intake only. Nothing implemented. Not superseded.
- #104 "VC-002: prototype provenance-backed F# construction": OPEN, not merged, head a202d5a.
  - Adds one file: .praxis/inbox/documents/2026-10-23-VC-002-provenance-backed-typed-construction.md.
  - Requirement 1: a versioned IR with requirement IDs, decision IDs, source revisions, unresolved questions and supersession.
  - Requirement 2: never infer authority from existing code.
  - Requirement 3: F# DUs, single-case types, validated constructors and transitions for a financial slice.
  - Requirements 4-7: compiler-enforced boundaries, deferral valid, traceability manifest, minimal dependencies. It stays experimental pending VC-001.
  - Intake only. Partially overlaps existing capability (ECIR dispositions, generator digests and trace), but is not implemented as written.
- Other open PRs:
  - #89: UI conformance for the site.
  - Drafts #83, #84, #85, #86, #87, #90: stacked CONSTRUCT-010 vocabulary 5-7 work (effect policies, persistence, decision records /4 and /5). Their titles claim versions 1.16-1.21 that collide with the versions actually released. They are stale and unmerged. main schemas stop at vocabulary-4.
- Recent merged PRs:
  - #102 (merge d11e9cf): VAC-002-P2 intake.
  - #100 (squash ab9696f): VAC-ORDO-001 intake.
  - #101 (merge f69f8ac): ARCH-001-03 intake.
  - #99 (9a8a2de): REL-GATE-002, which refuses unresolved conflicts and adds manifest-free readiness.
  - #98 (e6fe390): constructibility contracts consumer oracle.
  - #97 (16b09e3): strict versioned constructibility contracts.
  - #93: recognition decision records /2 and /3.
  - #88: conflicts settled by an authorized decision.
  - #82: vocabulary 4 / decision records /3.
  - #81: conflictResolution.
  - #80: vocabulary 4.
  - #79: coverage report.
  - #78: classification.
  - #77: pattern registry.

## 4. CONSTRUCT series / ARCH-001
- CONSTRUCT-001: typed construction plan, GH-64 (src/Ordo.Core/ConstructionPlan.fs:2; docs/architecture/construction-plan-v1.md:4).
- CONSTRUCT-002: construction engine, GH-65 (src/Ordo.Construction/Construction.fs:1).
- CONSTRUCT-008: mechanical-first construction, i.e. the default plan generated from approved decision records.
  - Implemented in src/Ordo.Core/ConstructionDefaultPlan.fs:1 and ConstructionDecisions.fs:2.
  - Spec: docs/architecture/construction-default-plan.md:1-5, status "draft / implemented".
  - Work item CONSTRUCT-008-ORDO is complete (.ros/work/queue.md:5).
  - The CONSTRUCT-008 *validation experiment* (summa-delivery-01, chrona-timer-01) lives in kemiller2002/research-documents@f6778c2 research/construction-by-design/ (tests/fixtures/construction/coverage-calibration/README.md:9-15).
  - Finding: mechanical-first cost 8-34% more on low-coverage slices (docs/architecture/pattern-registry.md:8).
- CONSTRUCT-009: requirements ledger (ConstructionLedger.fs:2; construction-default-plan.md:204). Complete.
- CONSTRUCT-010: classification, conflict resolution, coverage, vocabulary 4, decisions v3. Complete per queue lines 8-13. Later phases are unmerged drafts.
- ARCH-001 is not an Ordo requirement. It is an architectural-correctness experiment in cohort-based-engineering (PR #16).
  - ARCH-001-03 is an unclaimed intake document asking for an *optional* `ordo ecir check` trace manifest (advisory only).
  - Not implemented: no trace manifest in src.
  - Unrelated id: docs/architecture/executable-ordo.md has `id: SDE-ARCH-001`.

## 5. Capability classification
| Capability | Status | Evidence |
|---|---|---|
| Typed decision models with provenance (who/revision) | 2 | ECIR Decision nodes plus externally authorized decision ids (ConstructionIr.fs:36-45, 102-113). Typed decision records /1-/3 (ConstructionDecisions.fs:141-146). DefaultPlanProvenance carries only digests (manifest, blueprint, decisions) and the generator version (ConstructionDefaultPlan.fs:105-118). No authorizer identity or source git revision on decision records: "authorizations are test inputs ... not approvals" (coverage-calibration/README.md); the host binds the digest into a signed grant. Provenance fields exist only on BoundaryAmplification (`authorizedBy`) and MutationBoundary (`AuthorizedBy`). |
| Accepted req / authorized decision / unresolved policy / observed behavior | 2 | Dispositions Modeled/Deferred/Unresolved/Rejected/Superseded and node kinds Conflict, Deferral, EngineeringRationale (ConstructionIr.fs:24-45). Choice classes required/approved/implied/unresolved/unsupported (decision-classification.md). There is no "observed implementation behavior" state anywhere. |
| Construction constraints, valid states, authorized transitions | 1 | ECIR validation and readiness violations (ConstructionIr.fs:62-122). Constructibility admission and readiness (ConstructibilityContract.fs:77, 366). Typed plan vocabulary 1-4. Tests: Ordo.Tests Construction* and ConstructibilityAdmissionTests. CI green (Praxis validation on d11e9cf). |
| F# code generation | 2 | src/Ordo.Construction/Emit.fs generates Four-Tier F#: state, command and refusal DUs, Transition.decide, orchestration over ports. Byte-pinned goldens in tests/Ordo.Construction.Tests/Golden/* (door, gate-v4, time-entry v1/v2/v3). Only target is F#: no TypeScript, no C#. Not supported: data-carrying states, single-case types, validated constructors, multiple workflows, computed predicates (HANDOFF.md "Vocabulary v1 has no data-carrying states..."; Construction.fs:16-19). Library only, with no CLI command. |
| Never convert unresolved policy into an accepted rule | 1 | CompletePlan exists only when no choice is unresolved or unsupported (ConstructionClassification.fs:15, 75). Admission refuses unresolved conflicts with ORDO.CONTRACT.UNRESOLVED_CONFLICT (#99). onFailure `null` means "NOT DECIDED" (construction-default-plan.md). Tests: ConstructionClassificationTests and ConstructionConflictResolutionTests. Scope is limited to plan choices, not repository decision records (VAC-ORDO-001 not implemented: no `coveredBy` in src). |
| Consumption of a Praxis handoff | 5 | No reader for ros.handoff-authority or any "ros-ordo handoff". schemas/ros-handoff-authority.schema.json is a Praxis-managed artifact (.echelon/ros.json:435), not consumed by src. The direction is the reverse: Praxis and hosts consume Ordo contracts (ordo.execution-contract/1, ecir/1, constructibility contracts). |
| Pattern recognition / construction contracts | 2 | PatternRegistry.fs, PatternRecognition.fs, PatternRecognitionWire.fs; `ecir recognize`, which is report-only (pattern-registry.md:1-30). Merged in #77, #88, #93. The doc says "implemented, unreleased" and WI-0045 is still `active`. |
| Inherited rule provenance | 3 | Requested only in open PR #104 (requirement 2) and VAC-ORDO-001 R3 (inbox, unclaimed). No implementation. The only `inherited` in src is a PatternRecognition gap variable. |

## 6. Tests and CI
- Local commands: `dotnet test tests/Ordo.Tests/Ordo.Tests.fsproj`; likewise Ordo.Construction.Tests, Ordo.Complexity.Tests, Ordo.Churn.Tests, Ordo.Site.Tests. Sde.Core.Tests needs `npm run build:payload` in distribution/ first (HANDOFF.md env note).
- Workflows:
  - praxis-validation.yml runs on every push and PR: praxis registry check, praxis validate, and the Complexity, Churn, Ordo and Construction tests.
  - sde-distribution.yml (path-filtered): Sde.Core tests, pack, and a per-OS matrix.
  - Also pages.yml, release.yml, native-release.yml, publish.yml and release-trigger-guard.yml.
- Green on main:
  - Praxis validation success on d11e9cf (run 39885208626).
  - SDE distribution last ran on 9a8a2de, success.
  - Release and native release of 1.17.0 succeeded.
- Not verified locally (no dotnet).

## 7. Financial examples
- No REL-001 Ledger fixture. "Ledger" means the requirements-disposition ledger (CONSTRUCT-009), not a financial ledger.
- Closest financial material: tests/fixtures/construction/coverage-calibration/summa/ (COH-SUMMA-DELIVERY, invoice *delivery* states drawn from summa-invoice-generation-requirements.txt, decision DEC-SUMMA-ATTEMPT-STATES). It is a verbatim copy from research-documents.
- No invoice, payment or account domain example in examples/ (examples/ecir is generic).
- VAC-ORDO-001 mentions `withdraw` and holds, from VAC-001 experiments held elsewhere.

## 8. Mentions
- VAC-001: only in the VAC-ORDO-001 inbox document.
- VAC-002 / P2: VAC-002-P2-03 inbox document. P3: PR #103 and PR #104.
- cohort-based-engineering: cited by all 3 inbox documents and PRs #103/#104.
- Rehearsal: none.
- Causa: none ("causal" matches only).
- The term "cohort" itself is used widely (ECIR Cohort node kind).
- P1: no explicit document in Ordo.

## Not determined
- Whether the open draft PRs #83-#90 are formally abandoned (no closing comments read).
- Whether the GitHub "merged" flag on closed PRs is reliable: the list API returned `merged:false` with a `merged_at` set. merged_at is treated as merged.
- Local build and test pass: not run.
- Actual NuGet feed publication beyond release assets.
