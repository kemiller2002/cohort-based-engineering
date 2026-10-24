# Current state: evidence-backed inventory

**As of:** 2026-10-23. **Method:** read-only inspection of each repository's main branch, its open PRs, and its CI
history. The full reports, with file:line evidence, are in [evidence/inspection-2026-10-23/](evidence/inspection-2026-10-23/).
They are cited below as `[praxis §4]`, `[ordo §5]` and so on.

**Inspected commits:** praxis `7bff93f1`, ordo `d11e9cf`, dokimos `717103f`, cohort-based-engineering `9531430`,
research-documents `b372a7f`, echelon-registry `2d43629`, conditor `902277d`, percepta `1eb43a9`, forma `28d1101`,
limen `1cf75cb`, aegis `2c28b6e`.

**Status scale (exactly one per capability):**
1. Implemented and verified: code and tests exist, and the tests run in CI.
2. Implemented but incomplete.
3. Requirements documented but not implemented.
4. Experimental.
5. Not yet specified.

A status describes what exists **on main**. Work this program has started is listed separately in
[EXECUTION-STATE.md](EXECUTION-STATE.md) and changes no status here until it is merged and verified.

---

## 1. Component responsibilities (verified)

| Repository | Actual responsibility | Released | Installed Praxis | Praxis intake present | CI on main |
|---|---|---|---|---|---|
| praxis | Repository operating system: work protocol, records, telemetry, provenance, completion. Runtime authority for work; Ordo is the semantic authority [praxis §1] | 3.19.0 (2026-10-21); `work finish` unreleased | self-pins 3.12.0 (stale) | `.praxis/inbox/documents/` (7 pending), plus legacy `input-documents/` (2 unprocessed files) | **Red** since `2f4ce68e`: 2 of 2,358 tests fail from runner drift (git 2.55, timestamp flake), so registry check and validate are skipped [praxis §6] |
| ordo | State Directed Engineering method plus the F# Ordo tool: ECIR, construction plans, F# emitter [ordo §1] | 1.17.0 (2026-10-20) | 3.7.2 (`.echelon/ros.json`; root `ros.json` stale) | `.praxis/inbox/documents/` (3 pending, plus 2 merged today: VC-002, VAC-002-P3-02) | Green [ordo §6] |
| dokimos | Code-quality snapshots, comparison, policy gates, and independent completion verification (since 0.6.0) [dokimos §1] | 0.7.0 (2026-10-20) | 3.7.2 | `.praxis/inbox/documents/` (3 pending, plus 2 merged today: VAC-002-P3-03, VC-004) | CI green; **site `validate` red**: Playwright 1.56.1 cannot install on the ubuntu-26.04 runner (log of job 120443747212) |
| cohort-based-engineering | Proposed method plus cross-system experiments (VAC, ARCH, REL) | n/a | no runtime; plain-file intake lifecycle | `.praxis/inbox/documents/` (11 pending, plus VC-001 merged today) | no CI |
| research-documents (private) | Frozen experiments and raw evidence | n/a | n/a | n/a | n/a |
| conditor | Installation and environment governance; refuses versions outside the authority [supporting §Conditor] | 0.10.8 | 3.7.2 (pins 3.1.4 in `conditor.json`) | **none** | Green |
| echelon-registry | Discovery and compatibility catalog: profiles, snapshots, channels. Records no installations [supporting §Registry] | channel echelon-current 1.25.0 | 3.7.2 | **none** | Green |
| percepta | UI semantic contracts and rendered evidence [supporting §Percepta] | 0.1.0 | 3.7.2 | `.praxis/processed/` only | Green |
| forma | Zero-runtime HTML/CSS, tokens, accessibility | 0.9.1 in source; Registry knows 0.9.0 | 3.7.2 | 4 unclaimed, already-implemented inputs | Green |
| limen | Browser and WASM boundary | 0.9.1 in source; Registry knows 0.9.0 | 3.7.2 | legacy `input-document/` (kept as an evidence trail) plus 1 unclaimed implemented input | Green |
| aegis | .NET operational fault handling | 2.0.0 in source; Registry knows 1.0.0 | 3.7.2 | `Input-documents/` (3 consumed, never claimed) | Green |

**Findings that affect the program:**

- **Responsibilities match the mission's architecture,** with one exception: the CBE intake VAC-002-02 names
  Percepta as owner of experiment telemetry. Percepta's contract is UI semantic evidence, so that requirement belongs
  to Praxis telemetry (reconciled in §4).
- **Charters and handoffs are stale.** PROJECT-CHARTER.md is an unfilled template in conditor, registry, limen and
  aegis; most HANDOFF.md files are stale. Agents must not treat them as current.
- **Runner-image drift is red in two repositories.** Praxis main fails on git 2.55 output and a timestamp flake;
  Dokimos site validation fails because Playwright 1.56.1 does not support ubuntu-26.04. Both are environmental, both
  block verification, and both are program wave 0.

### Praxis intake reconciliation: `input-documents/` vs `.praxis/inbox/documents/`

- **Canonical location: `.praxis/inbox/documents/<file>`,** with the lifecycle claim → derive → complete
  (`praxis inbox claim|derive|complete`, or the plain-file lifecycle in Praxis `docs/fallback-reconciliation.md`
  "Input documents").
  - The directory has existed since Praxis 3.7.0 (WI-0064). The claim lifecycle CLI first shipped in **3.8.0**
    [praxis §2].
- **`input-documents/` is legacy.** `FileInputInbox.fs` still reads it as a pending location (`InputDocuments.legacyRelative`).
- **The legacy README conflicts with the lifecycle in mechanism.** Its "move or copy accepted material" predates the
  lifecycle and never mentions it. Its own "leave empty" rule is violated: `rfa.md` and
  `ros-ordo-handoff-and-bootstrap-requirements.txt` (ROS-ORDO-001..072) have sat unprocessed since September.
- **Repositories pinned to Praxis 3.7.2 cannot run the claim CLI.** That covers ordo, dokimos, conditor, registry,
  percepta, forma, limen and aegis. Until they upgrade, they use the documented plain-file lifecycle, as
  cohort-based-engineering already does (`requirements/VAC-CBE-001.md`).
- **Rule for this program:** write new intake to `.praxis/inbox/documents/` in the owning repository. Never write to
  `input-documents/`, `input-document/` or `Input-documents/`. The legacy folders are cleaned up by EP-02
  (IMPLEMENTATION-PLAN.md).
- **Conditor and the Registry have no intake directory.** Program intake creates `.praxis/inbox/documents/` there,
  which is the documented canonical path.

---

## 2. Capability classification

### Wave A: operational efficiency

| ID | Capability | Status | Evidence | What is missing |
|---|---|---|---|---|
| A1 | Dependency-aware verification selection (changed files, interfaces, dependencies, risk, previous evidence) | **5** | Only risk-declared verification *dimensions* exist: `praxis.work-risk/1`, `WorkRisk.fs`, PRX-QUAL-020..022. Worker checklists use a host-selected validator map with no impact analysis (DF-ROS-2026-A067) [praxis §4 A1] | A specification; a path→check map; a shadow mode; the mandatory set that is never skipped |
| A2 | Evidence reuse with invalidation | **2** | **Praxis:** evidence is bound to the exact clean revision (`PRX.COMPLETION.EVIDENCE_STALE`, `ValidationResult.fs:24-63`), and checklist closure digests cover packet, candidate, manifest, policy and validator closure (`WorkerChecklist.fs`). **Dokimos:** reuse requires the host `Reusable` flag plus digest and revision match (`CompletionVerification.fs:375-382`) [praxis §4 A2; dokimos §4] | Reuse across commits when the relevant closure is unchanged; invalidation on tool, SDK, configuration or environment change; dependency-granular invalidation |
| A3 | Deterministic, idempotent completion with structured refusals | **2** | `work complete-verified` (3.17+) and `work finish` (exit 0 verified or replayed, 3 refused); about 45 `PRX.COMPLETION.*` codes; policy read from the protected base (REL-GATE-004); tests in AttestedCompletionTests, which run in CI [praxis §4 A3] | `work finish` is **unreleased**. Real-Dokimos end-to-end cases are **skipped** in CI (`PRAXIS_TEST_DOKIMOS_DLL` unset). Verified completion is **not enabled** in any Echelon repository (PRAXIS-REL-006 captured). The mission's "missing evidence never completes" holds only where the policy is enabled. Classed 2, not 1, because the delivered behaviour is not in use |
| A4 | Real-provider tests moved earlier (persistence, authorization boundaries) | **3** | R002 lesson: "run the live provider suite from the first write onwards". Rehearsal acceptance ledger G6: "BLOCKED if live provider untested" (Indy-init `docs/REHEARSAL-ACCEPTANCE-LEDGER.md`). No toolchain code [research §7] | An ordering rule in the rehearsal and application gates (RELEASE-GATES.md §3). Not a Praxis capability |
| A5 | Execution telemetry: tokens, cost, wall time, CI executions, correction cycles, accepted requirements; unavailable ≠ zero | **2** | Tokens by bucket, cost from `praxis.price-table/1`, `time.wall_ms`, never-zero unavailability (DF-ROS-2026-A010, RQ-A013..A019 verified). `telemetry reliability-report` gives verified requirements, first-pass rate and rework [praxis §4 A5] | **No CI-execution count.** 287 of 307 execution records carry no tokens (no auto-ingest: PRAXIS-REL-004 captured). Claude Code output tokens are a lower bound (REL-TOKEN-002 pending). No per-item windows within a continued session (VAC-CONT-001-R2 pending) |
| A6 | Compatibility evidence reuse without silently selecting newer unapproved releases | **2** | **Conditor:** lock v4 digests; a step whose receipt already matches is reused; it refuses versions outside the authority (`RegistryAuthorityBinding.fs:35-77`) and refuses downgrades. **Registry:** profile semver ranges plus snapshot; REG-RU-007 qualification [supporting §5] | "Approved" is implicit, never recorded. echelon-current history is not kept as immutable sets. Environment receipt re-check (CON-INDY-050..054) is draft only. Release trust keys are empty. Newer releases are unregistered rather than assessed (Praxis 3.19.0, Dokimos 0.7.0, Forma 0.9.1, Limen 0.9.1, Aegis 2.0.0) |

### Wave B: verified construction

| ID | Capability | Status | Evidence | What is missing |
|---|---|---|---|---|
| B1a | Praxis keeps requirement ids, source revisions and supersession through intake | **2** | Inbox claims keep source SHA-256 and derivations; RQ records keep `derived_from`; `ros.handoff-authority` v1 has `unknowns` and `supersededResolutionIds` as **untyped strings** [praxis §4 B1] | Recent REL intakes derive straight to code with no RQ record. RQ-A032 status is stale (draft though implemented) |
| B1b | Deterministic, versioned handoff that separates requirement, decision, question and observation | **3** | VC-003 (praxis inbox, merged today via #286). ROS-ORDO-001..072 never ingested | The whole exporter. The draft contract is CONTRACTS.md C1 |
| B1c | Frozen four-sentence authority contract in the implementation brief, with its version in telemetry | **3** | VAC-002-P3-01 R-PRAX-1 (praxis inbox, merged today via #285) | Implementation; owner decision OD-6 |
| B2a | Typed decision models with provenance | **2** | Typed decision records /1–/3 and authorized-decision ids, bound by digest (`ConstructionDefaultPlan.fs:105-118`) [ordo §5] | The authorizer and source revision are not recorded |
| B2b | Construction constraints, valid states, authorized transitions | **1** | ECIR validation, readiness and admission; plan vocabularies 1–4; CI green [ordo §5] | — |
| B2c | F# construction | **2** | Four-tier F# emitter (unions, decide/transition, ports), byte-pinned golden files and compile-negative tests; F# is the only target [ordo §5] | Data-carrying states, single-case types and validated constructors; no CLI command to construct |
| B2d | Never convert unresolved policy into an accepted rule | **1** for plan choices | A complete plan is impossible while any choice is unresolved (`ConstructionClassification.fs:15,75`); `UNRESOLVED_CONFLICT` refused [ordo §5] | Covers construction-plan choices only, not business rules in handwritten code |
| B2e | Consume a Praxis handoff | **5** | No reader; the handoff-authority schema is never read by Ordo code [ordo §5] | CONTRACTS.md C1 |
| B2f | Inherited-rule (reused-code) traceability | **3** | VAC-002-P3-03-R2 and VC-002 R2 (Ordo inbox) | Implementation |
| B3a | Invariant verification against specified invariants | **5** | Plan invariants are parsed but never checked; only frozen oracle cases are verified [dokimos §4] | Implementation |
| B3b | Rule-provenance inspection | **2** | CONSTRUCT-010 rejects unapproved or fabricated decision citations, for **Ordo-generated** code only [dokimos §4] | Handwritten and legacy rules (VAC-002-P3-03-R1, VC-004) |
| B3c | Separate proven violations from uncertain authority; route authority questions to owners | **3** | VAC-002-P2-04-R1 in the Dokimos inbox; construction verify separates "incomplete or unknown" from "rejected" [dokimos §4] | Implementation |
| B3d | Defect-class analysis | **5** | Only in the vendored `.sde` method docs [dokimos §4]. The rehearsal ledger has `defect_classes[]` as an application-level contract | A specification in Dokimos |
| B3e | Quality results Praxis can consume | **1** | `dokimos.completion-verification/1` receipts (digests, verdict, `DOK.COMPLETION.*` codes), DSSE attestation since 0.7.0 [dokimos §2] | — |
| B4 | Integration: intake → authorized model → Ordo → F# compile → Dokimos evidence → Praxis completion | **5** | Nothing connects these today | The vertical slice (IMPLEMENTATION-PLAN.md B4) |

### Wave C: execution efficiency

| ID | Capability | Status | Evidence |
|---|---|---|---|
| C1 | Minimal agent tool profiles | **3** | REL-TOKEN-004, unprocessed in the Praxis inbox; Praxis has no worker launcher [praxis §4 C1] |
| C2 | Durable context handoffs | **1** | `work checkpoint` and `work continue`, DF-ROS-2026-A042, RQ-A022, checkpoint and continuation tests in CI [praxis §4 C2] |
| C3 | Typed inter-agent communication | **2** | `praxis.remote` request and response schemas (protocol 1.4), `local-worker-packet/1` and `local-worker-result/1`; the full coordinator loop is not built (DF-A060..A074 draft) [praxis §4 C3] |
| C4 | Dependency-aware parallel execution | **2** | Planner waves and collision graph (PRX-PLAN-080..094); advisory or shadow only (PRX-PLAN-161 "MUST only recommend") [praxis §4 C4] |
| C5 | Checkpoint-driven CI | **3** | praxis#122 "Debounce commit-driven CI" open since 2026-09-29; PRX-PLAN-020 captured. **Dokimos already runs a `debounce` job** in its CI, which is reusable prior art [praxis §4 C5; dokimos PR checks] |
| C6 | Critical-path scheduling | **2** | `criticalPath` (`Graph.fs:149`) with tests; advisory only [praxis §4 C6] |

---

## 3. Experiments and prior work

| Work | Status | Key result | Evidence class | Location |
|---|---|---|---|---|
| VAC-001 agent continuity | **Complete** within scope | One continuous agent: −40.9% cost per accepted requirement versus a fresh agent per change (CI −48.1% to −33.0%). Controls +14% to +31%. Rebuilding from verified state +86%. Correctness at ceiling, so no reliability effect could be measured | Cost: demonstrated. Reliability: untested | `research/verified-agent-continuity/`, `research/experiments/VAC-001/` |
| R-EXP-1 (VAC-003), R-EXP-2 (VAC-004) | Preregistered, **not run** | — | — | `r-exp-1-protocol.md`, `r-exp-2-protocol.md`; pilot ceilings $80 and $110 not yet authorized |
| VAC-002 pilot (P1) | Checkpoint | 72/72 accepted, so it could not discriminate; review found a silent L04 staff exemption | Inconclusive | `research/experiments/VAC-002/` |
| VAC-002-P2 | Complete | 0/80 unauthorized decisions (every arm had a README authority section: confound); controls cost 1.76× to 3.25× and caused all observed harm | Control harm: demonstrated | `.../VAC-002/P2/` |
| VAC-002-P3 | Complete (CBE#21, `9531430`), $92.31 of $150 | Contract 3/18 vs 7/18, p = 0.125. Executable authorization: 0 prevented, 10 false rejections, 4 harmful. **All 36/36 errors came from rules embedded in reused code.** C06 beat every control (15/15) | H1 inconclusive; H4 contradicted; H5 demonstrated; mechanism demonstrated | `.../VAC-002/P3/` |
| ARCH-001 | Complete | 128/128 at ceiling; guidance +15%, enforcement +25% cost | Not supported (ceiling) | `research/architectural-correctness/` |
| ARCH-002 | Open PR CBE#17 | — | — | not on main |
| CONSTRUCT-008 | Complete, n = 3 | Directional; selective adoption recommended, not a default | Preliminary | research-documents (private) |
| CONSTRUCT-010 | Preregistration **draft**, on an unmerged branch; no scored trials | — | — | research-documents branch `research/construct-010`; `construct-010-trials` |
| REL-001 | Run-02 complete | Optimized Echelon +35.5% cost versus bare Claude, all arms at ceiling | Demonstrated cost | `research/experiments/REL-001/` |
| Praxis A021 / A024 | Complete | Grouping cheaper ($9.48 vs $21.51). Continuity cheapest; structured handoffs not cheaper | Preliminary | praxis `research/experiments/` |
| Rehearsal 1 (EX-INDY-INIT-2026-R001) | **PASS** at T+261.8 of 420 min | 25 defects. Releases were treated as Accepted while the deploy accept job was red (R-21) | — | `indy-init-rehearsal-001`, research-documents |
| Rehearsal 2 | **Not accepted**: G7 BLOCKED | Deployed at 296.8 min; 4 defect classes recurred; the live GitHub provider found DC-004 and DC-005, which mocks could not | — | `indy-init-rehearsal-002/docs/REHEARSAL-002-REPORT.md` |
| Rehearsal 3 plan | "APPROVED EXPERIMENT DESIGN; NOT EXECUTED" (owner commits `5e94e92`, `734c4bd`) | R3-DV-001..016: 420-min hard cap, event-driven exits, deferred noncritical tests, never-deferred security and data integrity | — | `Indy-init/docs/REHEARSAL-003-DEFERRED-VERIFICATION-EXPERIMENT.md`. Preflight has BLOCKED items |
| CBE operating model | Proposed method; VAC-CBE-001 R1/R2 owner-approved | Continuity by default; extensions recorded as questions | — | `docs/operating-model.md`, `requirements/VAC-CBE-001.md` |

## 4. Open PRs named by the mission, and duplicate reconciliation

| PR | State before this program | Action | Disposition |
|---|---|---|---|
| cohort-based-engineering#21 | Merged 2026-10-23 (`9531430`) | — | Source of the P3 evidence |
| cohort-based-engineering#22 (VC-001) | Open, intake only | **Merged** 2026-10-23 (`af2c7f4`) | Pending CBE input; becomes EXP-1 (EXPERIMENTS.md) |
| praxis#285 (VAC-002-P3-01 R-PRAX-1) | Open, intake only; `validate` red from main's drift | **Merged** (`914a2f1`) | Pending Praxis input. **Duplicate** of R1 in CBE's `2026-10-23-VAC-002-P3-01` input. The Praxis copy is canonical for R1; the CBE copy keeps R2–R4 |
| praxis#286 (VC-003) | Open, intake only | **Merged** (`9704841`) | Pending Praxis input. Overlaps ROS-ORDO-001..072 (legacy) and CBE VAC-002-01 R1; derive one handoff requirement set citing all three |
| ordo#103 (VAC-002-P3-02 R-ADM-1..3) | Open, intake only | **Merged** (`1b3ec62`) | **Duplicate** of CBE's P3-02 input (Ordo part). It targets code that is **not in Ordo**: the executable-authorization checker lives only in the CBE harness (`P2/DECISION-AUTHORITY.md`: "changes no production schema in Ordo"). Disposition: a constraint on any future Ordo decision admission. The B2 slice's handoff admission honours it |
| ordo#104 (VC-002) | Open, intake only | **Merged** (`9addcbe`) | Pending Ordo input; becomes increment B2 |
| dokimos#51 (VAC-002-P3-03) | Open, intake only | **Merged** (`9e38a3b`) | **Duplicate** of the Dokimos part of CBE's P3-03 input |
| dokimos#52 (VC-004) | Open, intake only | **Merged** (`6c8554e`) | Refines #51 R1/R3 into a mechanical checker. Derive **one** requirement set from both inputs; neither supersedes the other |

**Other duplicates and misroutings found:**

- **ENGINEERING-RELIABILITY-001** is pending in CBE's inbox but was already processed in Praxis
  (INPUT-695a7e4723d7f795). Disposition: reject in CBE as a duplicate, citing the Praxis claim.
- **CBE inputs that target other repositories were never forwarded.** VAC-002-01, -02 and -04 say "Forward at
  triage". Disposition:
  - forward 01 to Praxis (merged into the VC-003 handoff set) and to Ordo;
  - forward 02 to **Praxis** telemetry, not Percepta;
  - forward 04 to Ordo and Praxis as **deferred** (it says so itself).
- **VAC-CONT-001** (Praxis) and **VAC-CBE-001** (CBE) are related, not duplicates: Praxis per-item usage windows versus
  the CBE operating model.
- **Four "VC" requirement sets were merged before any of them was triaged.** These are the only existing
  verified-construction requirements, and this program's waves B and X consume them rather than writing new ones.

## 5. Release set state

- **Newest approved compatible release set:** Registry profile echelon-current **1.25.0**: praxis 3.16.0, ordo 1.17.0,
  dokimos 0.6.0, percepta 0.1.0, aegis 1.0.0, limen 0.9.0, forma 0.9.0, folio 0.4.0, and others.
  Conditor 0.10.8 qualifies all of them [supporting §5]. Rehearsal 2 ran on it.
- **Newer releases exist but are not approved:**
  - recorded but outside the snapshot: Praxis 3.17–3.19, which carry the REL-GATE-003 and -004 completion-gate fixes;
  - Dokimos 0.7.0;
  - never registered: Forma 0.9.1, Limen 0.9.1, Aegis 2.0.0.
- **Repositories pin an older set.** Registry, Percepta, Forma, Limen and Aegis pin **echelon-current 1.2.0**
  (`resolved-release-set.json`, sha256 `ea1b39a0…`), whose profile is no longer in the Registry.

## 6. Changes on main since the inspection (2026-10-23, this program)

These rows change classifications because the work is now merged on main and verified in CI. Everything else above
still stands.

| ID | Was | Now | Evidence |
|---|---|---|---|
| CI health | Praxis main red; Dokimos site validation red | **Green** | praxis#287 (`638b2e7`): git 2.55 test and uutils `date` fix. dokimos#53 (`a4fa237`): Playwright 1.63.0 |
| B2c/B2e/B2f | 2 / 5 / 3 | **4 Experimental** | ordo#105 (`d31290c`): handoff admission, Ordo-emitted invoice slice, validated constructors, capability-gated persistence, construction trace; 69 tests. Not in the default build |
| B3a/B3b/B3c | 5 / 2 / 3 | **4 Experimental** | dokimos#53 (`5988bf0`) and #54 (`fc9b31f`): provenance audit v1/v2 and bounded invariant oracle. **Held-out accuracy fails its thresholds** (recall 80%, false-question rate 25%; EXPERIMENTS.md §4) |
| B4 | 5 | **4 Experimental** | `integration/b4/B4-RESULT.md`: five frozen outcomes PASS; the Praxis completion step NOT_RUN |
| A2 (Dokimos side) | 2 | 2, plus an experimental `isReusable` prototype | dokimos `experiments/rule-provenance` |
| A3 | 2 | **2: released in Praxis v3.20.0 (`work finish`, real-Dokimos CI path, idempotence tests); waits only on approval of a release set and pilot enablement (OD-9)** | praxis#288 runs the real-Dokimos completion cases in CI (0 SKIP) and adds CLI idempotence contract tests. Still unreleased and not enabled |

