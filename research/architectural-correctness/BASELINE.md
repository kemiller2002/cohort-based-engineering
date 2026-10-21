# ARCH-001 baseline: architectural guarantees in the Echelon toolchain

**Experiment:** ARCH-001 Echelon architectural correctness.
**Date:** 2026-10-21.
**Coordinator branch:** `claude/echelon-architectural-correctness-m4glhq`.

**Pins inspected (read-only):**

| Repository | Commit / version |
|---|---|
| ordo | `bb43c26` (v1.17.0) |
| praxis | `986211c` (v3.19.0) |
| dokimos | `04b5f85` (v0.7.0) |
| summa | `8b0e93e` |
| signal | `e19101f` |
| cohort-based-engineering | `5b2ccb5` |

**Detailed evidence, with file and line citations:**

- [`inventory/architecture-spec-inventory.md`](inventory/architecture-spec-inventory.md): Worker A (rules, apps, ambiguities).
- [`inventory/capability-inventory.md`](inventory/capability-inventory.md): Worker E (Ordo, Praxis, Dokimos, AST tooling).
- [`inventory/prior-evidence.md`](inventory/prior-evidence.md): Worker F (A021, A021-R2, A022–A024, REL-001 runs 01–03).

This document records **what exists**, not what is proposed. Anything proposed is marked as a proposal.

## 1. The authoritative four-tier architecture

The authority is **SDE-DOCTRINE-003 "Four-Tier Architecture" v0.2.1**. Its status is `accepted`, and it is marked "REQUIRED as SDE's canonical architectural layering".

- **Source:** `ordo/doctrine/FOUR-TIER-ARCHITECTURE.md`.
- **Installed copies:** byte-identical in `summa/.sde/architecture/` and `signal/.sde/architecture/`, shipped by `@echelon-foundry/sde`.
- **Supporting theory:** TH-SDE-2026-0001, status `supported`, confidence 0.75. It was validated on one application, HelixNote.

The four tiers, verbatim:

1. **Semantic Model**: "What can be true?" Must not know about Postgres, HTTP, JSON, frameworks, browser APIs, serialization, filesystems or infrastructure.
2. **State Transition / Domain Execution**: "What legal change may happen?" Effects are requested as data and executed by Tier 4.
3. **Application / Projection / Orchestration**: coordinates use cases, projections and boundary translation. It "must not become a second semantic authority".
4. **Host / External Effects**: database, network, HTTP, browser, filesystem, clock, queue, framework and interop. It reports Unknown outcomes as first-class values.

Further rules:

- "Dependencies point downward only. Tier 1 never imports from Tier 2, 3, or 4."
- Tier 1/2 imports no I/O, provider-SDK, persistence-adapter or ROS dependency.
- Effects flow decide (T2) → coordinate (T3) → perform (T4) → interpret Succeeded/Failed/Unknown (T2).

Other documents also use "four-tier" vocabularies. None of them is the authority for Echelon applications:

- Praxis's own Domain/Application/Infrastructure/CLI layering.
- HelixNote's state-kind model, which the doctrine says not to merge with these tiers.
- The Limen engine/kernel layout.

See inventory §1.3 and A7.

### Ambiguities and their resolution for this experiment

The inventory found eleven (§7, A1–A11). The resolutions below are **adopted for ARCH-001 only**. They are not proposed changes to the doctrine.

| Id | Ambiguity | ARCH-001 resolution |
|---|---|---|
| A1 | No document maps projects or modules to tiers | Each evaluated repository declares the mapping explicitly in the verifier policy. An unmapped project is a finding. |
| A2 | Adjacent-only versus any-lower dependencies | Any downward edge is legal; only upward edges violate. This is the literal text, and Praxis's enforced graph also allows skipping. |
| A3 | Tier 1 and Tier 2 share projects in the apps | The fixture separates them into two projects, so the 1↔2 rule is checkable. |
| A4 | JSON: barred from Tier 1, but Boundary Preservation mandates hand-written encoders | The fixture keeps JSON in Tier 4 adapters. For the apps this remains heuristic. |
| A5 | Clock read in the apps' `*.Application/Runtime.fs` composition roots | The fixture's composition root is in Tier 4. Clock, randomness and GUID generation outside it are violations. |
| A6–A11 | Storage tier, name collisions, normative strength, stale cross-references, missing gates, ROS dependence | Adopted as in the inventory. A8, single-application validation, is a threat to validity. |

## 2. Guarantee classification

Legend:

- **FS**: formally specified, not enforced.
- **ME**: mechanically enforced (a check that runs and fails closed).
- **TNE**: tested but not enforced as a general rule.
- **GO**: guidance only.
- **MA**: missing or ambiguous.

The rule identifiers are the AR-xx entries in inventory §8.

### 2.1 Architecture (dependency direction and responsibility placement)

| Guarantee | Status | Evidence |
|---|---|---|
| Dependencies point downward; Tier 1 imports nothing above it (AR-01, AR-02) | **FS** for Echelon apps | Neither summa nor signal declares tiers or tests the direction. The graphs comply by convention (inventory §5). |
| Project graph is acyclic | **ME** (by the compiler) | MSBuild/F# forbid project cycles. F# file order forbids forward references within a project. |
| Tier 1/2 references no I/O or provider package (AR-03) | **FS** | No check exists. |
| Tier 1/2 uses no I/O, JSON, clock or randomness API (AR-04, AR-06) | **FS** | Possible deviations exist in both apps: `System.Text.Json` in Summa.Ledger and Signal.Engine (inventory §5). |
| Tier 3 is not a second semantic authority (AR-07); effect flow (AR-09); single authority for each fact (AR-19) | **FS**, requires review | Semantic properties. No check, and none is mechanically decidable in general. |
| Unknown is a first-class outcome (AR-10) | **FS** | Doctrine plus DECISION-AND-EVIDENCE-SEMANTICS. No check. |
| UI and browser kernel hold no domain rules (AR-23) | **TNE** in Summa, **FS** in Signal | Summa INV-ARCH-006 is a token list for money formatting only. |
| Shared contract package has no references (AR-26) | **ME** in Summa only | `Summa.Contracts.Tests/PackageTests.fs`. |
| Architecture checks run before completion (AR-25) | **MA** | Required by the method documents. The only cited check, HelixNote's `check-semantic-architecture.sh`, is in no pinned repository. |
| Project→tier mapping declared (AR-28) | **MA** | Not stated anywhere. |
| Tier 3 depends on ports, not providers (AR-29) | **MA** | Both apps' Application projects reference provider SDKs directly. |
| Praxis's own layering | **ME** for Praxis only | `praxis/tests/Praxis.Tests/ArchitectureTests.fs`: hard-coded project graph plus forbidden adapter tokens, run in CI. |
| Ordo-generated code tier order (AR-27) | **ME** inside Ordo only | Compile-negative `dotnet fsi` probes (FS0039) in Ordo's tests. Applies only to code Ordo generates. |

### 2.2 Decisions and constructibility (Ordo)

| Capability | Status | Evidence |
|---|---|---|
| ECIR `ecir/1` decision contracts. Node kinds: decision, contract, invariant, interface, cohort, verificationObligation, conflict, deferral, engineeringRationale. | **Implemented and tested** | `ordo/src/Ordo.Core/ConstructionIr.fs:36-45`. |
| Constructibility admission (`ordo ecir check`): reciprocal requirement↔node mapping, verification obligation and owner cohort per requirement, DAG checks, unresolved conflicts refused | **Implemented and tested** | `ConstructibilityContract.fs`. Exit 0 admitted, 1 refused, 2 usage. |
| Requirement → decision traceability | **Implemented and tested** up to verification-obligation ids | Readiness mode with `--authorized-decision`. |
| Decision → code or test traceability | **Missing** | Nothing links a decision id to a source file, symbol or test. |
| Architecture rules expressed in a contract | **Missing** | No node kind exists for a tier, module or dependency rule. `ArchitectureConstraints` is an opaque string list; the CLI hard-codes it to `[]` and nothing evaluates it. |
| `ordo boundary assess` | **Implemented and tested**, advisory only | Classifies changed *paths* by a glob-to-layer map. Always exits 0. Does not check dependencies. |

### 2.3 Verification and evidence integrity (Praxis, Dokimos)

| Capability | Status | Evidence |
|---|---|---|
| Dokimos DOK-R008 forbidden ProjectReference rule | **Implemented and tested**, as a ratchet | A regex over `.fsproj` `<ProjectReference>` lines. Project-level only. Fails when the count grows past the baseline, not when it is above zero. Blind to `open`, type and function dependencies. |
| Praxis host verifier: exact-commit clone, `protectedPaths` hashes, shell-free validation commands, DSSE/ECDSA receipts | **Implemented and tested** (REL-GATE-003/004) | `TrustedVerifier.fs`. 43 attested-completion tests. |
| Completion policy protected from agent weakening; trust root outside the worktree; verifier keys pinned | **Implemented and tested** | `ProtectedCompletionPolicy.fs`. |
| Dokimos completion verification against a host authority, bound to the expected commit and contract digest | **Implemented and tested** | `CompletionVerification.fs`, `CompletionAttestationBinding.fs`. The Dokimos receipt itself is unsigned. |
| An architecture checker as attested completion evidence | **Possible today, not configured anywhere** | Add it as one `validations[]` entry in the `echelon.validation-policy/1` file. No Praxis code change is needed. |
| `praxis architecture check` | **Implemented**, but **not** a code-architecture check | Enforces the implementation-language policy only. |

### 2.4 Compiler and AST analysis

| Capability | Status |
|---|---|
| `ordo/tools/Ordo.Complexity` (FCS 43.8.400 untyped parse tree, Roslyn 4.11) | Implemented and tested (28 tests). Untyped only, and a metrics tool, not a rule engine. |
| Typed symbol-level analysis (FCS type-check) anywhere in the ecosystem | **Missing.** Praxis lists "Compiler-derived F# tier analysis" as a *proposed* remaining slice of GH-234. |
| Line-based import scanning (`ordo/src/Sde.Cli/Boundary.fs`, Dokimos `SourceLexing.fs`) | Implemented. Not compiler-resolved. |

## 3. What prior experiments did and did not establish

Detail is in [`inventory/prior-evidence.md`](inventory/prior-evidence.md).

**A021 and A021-R2** compared grouped and independent execution, n=1 per arm.

- Grouped execution was cheaper: $9.48 vs $21.51, and $10.75 vs $26.05 in R2.
- Blinded qualitative review found a more coherent model in the grouped arm, while the independent arm reused existing code better.
- There was no numeric architecture score.

**A024** is the only numeric architecture rubric: 5 dimensions scored 0/1/2.

- The continuous session was cheapest but scored 5/10, against 10/10 and 8/10 for the other conditions.
- All three conditions passed 36/36 acceptance criteria. Acceptance tests did not capture architecture.

**REL-001 runs 01–03** never scored architecture.

- Runs 01 and 02 hit a ceiling on hidden-oracle correctness.
- Run-02 found the optimized Echelon arm cost 35.5% more than bare Claude, 95% CI +24.9% to +49.5%.
- Run-03 is a draft and owned by another session. ARCH-001 does not use its state, pins or hosts.

**Not established by any prior work:**

- any automated or static architecture metric;
- any variance estimate for architecture outcomes (every comparison was n=1);
- the effect of architecture guidance or enforcement on violations;
- any follow-up or change-resilience cost.

ARCH-001 targets exactly these gaps.

**Overlap to avoid:** A024 follow-on #1 (guidance ablation) is the closest. ARCH-001 differs in three ways: it ablates *architecture* material rather than workflow, it has a mechanical verifier, and it has a follow-up phase. A023's grouping design and REL-001 run-03 are untouched. H7 (grouping) is deferred to a separate experiment.

## 4. Implications for the ARCH-001 design

1. **Arm B** receives SDE-DOCTRINE-003 verbatim plus a fixture-specific instance document. That instance document adds the tier map (A1) and no new principles.
2. **Arm C** receives Ordo's real, implemented capability: an `ecir/1` contract, `ordo ecir check` admission and conflict refusal, and requirement→decision traceability. Decision→code traceability does not exist in Ordo, so it is supplied as a *brief instruction* (cite DEC ids in code and tests). It is scored only as decision fidelity.
3. **Arm D** needs a verifier that does not exist yet. ARCH-001 Workstream C builds `archcheck`:
   - It works on compiler-resolved structure: the FCS typed tree plus the MSBuild project graph.
   - It subsumes DOK-R008's project-level semantics and adds symbol-level rules.
   - The experiment uses it as a new research instrument, **not** as a pre-existing gate (A10).
4. **Completion orchestration** is the same harness `submit` gate in every arm, so C and D differ only in the architecture check.
   - Praxis's attested verifier is **excluded from all arms**. Adding it to C/D only would confound workflow with enforcement. REL-001 already studies that workflow.
   - Conclusions are therefore about Ordo contracts and architecture enforcement, not about the Praxis work protocol.
   - Integrating `archcheck` as a Praxis `validations[]` entry is an implementation recommendation, not something this experiment tests.
5. **Evidence integrity.** OS-level isolation between trial agents and the scorer was not available in this container: creating a separate trial user was refused by the environment's policy. Integrity therefore rests on four controls, documented in PROTOCOL.md:
   - hidden material sealed outside every repository and encrypted in git until trials finish;
   - pristine, hash-pinned scorer copies;
   - transcript audit for protected-path access (contamination exclusion);
   - before/after integrity hashes.
