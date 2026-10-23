# Implementation plan

Increments are ordered by dependency and by expected reduction in the cost of accepted, correct functionality. Each
increment has:

- one owning repository;
- the intake document its requirements come from;
- the existing records it extends, so it never duplicates them;
- acceptance criteria;
- compatibility obligations.

Each owning repository derives canonical work items from its intake (Praxis inbox lifecycle). This plan does not
replace those items.

Status values: `not started`, `in progress` (with commits listed in EXECUTION-STATE.md), `done` (merged and verified).

---

## Wave 0: make verification trustworthy

### EP-00 Praxis main green (runner drift)

- **Owner:** praxis. **Source:** CURRENT-STATE §1 (red since `2f4ce68e`). **Status:** implemented in praxis#287 (2358/2358 locally); CI pending.
- **Acceptance:**
  1. Classify "outside a repository" from git's exit status or stable prefix, not the full message. A test covers both
     the git ≤ 2.54 and the 2.55 message forms.
  2. Root-cause the timestamp-ordering failure and fix it; never skip or quarantine the test.
  3. Full F# suite passes locally and in CI. `praxis validate` and registry check run again on main.
- **Compatibility:** no behaviour change for users other than correct classification.

### EP-01 Dokimos site validation on ubuntu-26.04

- **Owner:** dokimos. **Source:** CURRENT-STATE §1 (job 120443747212). **Status:** not started.
- **Acceptance:**
  1. The site `validate` job installs a supported browser on the current runner image. Either upgrade Playwright to a
     version that supports ubuntu-26.04, or pin `runs-on` to a supported image with a dated revisit note; the owner
     picks one under OD-5.
  2. The Deploy site workflow is green.
- **Compatibility:** no change to Dokimos results or CLI.

### EP-02 Intake hygiene

- **Owners:** each repository. **Status:** not started.
- **Acceptance:**
  1. Praxis `input-documents/README.md` points to `.praxis/inbox/documents/` and the claim lifecycle, and stops
     describing "move or copy".
  2. The two legacy Praxis files are claimed:
     - `rfa.md` is rejected as a prompt, not a requirement;
     - ROS-ORDO-001..072 has its derivations recorded or is rejected as superseded by VC-003, item by item.
  3. The unclaimed but implemented inputs in Forma (4), Limen (1) and Aegis (3) are each claimed and completed, with
     derivations that point at the implementing commits, or with `--no-derivations REASON`.
  4. The CBE inbox is triaged:
     - ENGINEERING-RELIABILITY-001 is rejected as a duplicate;
     - VAC-002-01, -02 and -04 are forwarded per CURRENT-STATE §4.
- **Compatibility:** Praxis 3.7.2 repositories use the plain-file lifecycle.

### EP-03 Release-set reconciliation for the program's own repositories

- **Owners:** registry, conditor. **Status:** not started.
- **Acceptance:** each program repository's `conditor.json` and `.echelon` pins agree with one Registry-approved set.
  Conditor's own pin of Praxis 3.1.4 conflicts with the 3.7.2 it actually runs, and this increment resolves that. No
  repository is moved to an unapproved release.

---

## Wave A: operational efficiency

Ordered by readiness. A3 is closest to done, so it goes first.

### A3 Deterministic completion in use

- **Owner:** praxis. **Status:** not started.
- **Extends:** PRAXIS-REL-003 (release and qualify via Conditor and the Registry) and PRAXIS-REL-006 (enable
  `requireVerifiedCompletion`), both captured work items. No new requirement is needed for those parts.
- **New source:** intake `2026-10-23-EP-A3-completion-in-use.md`, which adds the CI end-to-end obligation.
- **Acceptance:**
  1. **Release:** a Praxis release contains `work finish`, and the Registry records it as assessed. Approval is the
     owner's call.
  2. **Real-Dokimos path in CI:** CI sets `PRAXIS_TEST_DOKIMOS_DLL` to a pinned Dokimos release, so the end-to-end
     completion cases run instead of being skipped.
  3. **Refusal is idempotent:** completing with missing evidence returns exit 3 and the same refusal codes on repeated
     calls, and changes no state. Completing twice with valid evidence replays (exit 0) without duplicating records.
  4. **Pilot:** one program repository enables verified completion (the owner chooses, OD-9). Its first five
     completions are recorded with verdicts.
- **Compatibility:** opt-in stays opt-in for repositories that have not enabled it.

### A2 Evidence reuse with validity conditions

- **Owners:** dokimos (A2a), praxis (A2b). **Status:** prototype in progress (in the B3 slice: `isReusable`).
- **Sources:** intakes `2026-10-23-EP-A2a-evidence-validity-conditions.md` (dokimos) and
  `2026-10-23-EP-A2b-closure-scoped-reuse.md` (praxis).
- **A2a acceptance (Dokimos):**
  1. Results and completion-verification receipts carry a `validity` block (C3). Its digests cover source, tool name
     and version, configuration, SDK, and an optional dependency digest.
  2. A `reuse-check` returns *reusable* only when every digest matches. Each mismatch gives a distinct reason code,
     with one test per reason.
  3. The existing `Reusable` host flag stays required: digests add conditions, never remove one.
- **A2b acceptance (Praxis):**
  1. Completion may accept evidence produced at an earlier commit only when the evidence's validity digests,
     recomputed at the current HEAD over the evidence's declared closure, all match.
  2. Otherwise `PRX.COMPLETION.EVIDENCE_STALE` names the mismatched digest.
  3. Mandatory gates (RELEASE-GATES.md §2) are never satisfied by reused evidence.
- **Compatibility:** receipts without a validity block behave exactly as today (exact-revision binding).

### A1 Dependency-aware verification selection (shadow first)

- **Owner:** praxis; Dokimos defines result meaning. **Status:** not started. **Depends on:** A2a (validity), A5
  (CI counting).
- **Source:** intake `2026-10-23-EP-A1-dependency-aware-verification.md` (new; nothing existing specifies it:
  CURRENT-STATE A1 is status 5).
- **Acceptance:**
  1. `praxis.verification-map/0.1` (C5) is parsed strictly. Its mandatory set is non-empty and cannot be deselected.
  2. `praxis verify plan --base REV --head REV` emits the selected checks, with each reason: the path, interface or
     dependency that triggered it, the risk class, and prior valid evidence.
  3. **Shadow mode:** the plan is recorded next to the checks actually executed. Nothing is skipped.
  4. The EXP-2 replay over at least 50 historical commits reports would-skip rate and would-have-escaped failures.
  5. Promotion to enforcing mode only through EXPERIMENTS.md §6.
- **Compatibility:** no change to existing CI until promotion.

### A5 Telemetry completeness

- **Owner:** praxis. **Status:** not started.
- **Extends:**
  - REL-TOKEN-001 (per-request ledger) and REL-TOKEN-002 (output-token lower bound), both pending P1 inputs;
  - PRAXIS-REL-004 (auto-ingest at completion);
  - VAC-CONT-001-R2 (per-item windows);
  - VAC-002-02 (session-aware cost), forwarded from CBE.
- **New source:** intake `2026-10-23-EP-A5-ci-and-correction-telemetry.md`, which adds what nothing covers: a CI
  execution count and CI minutes per work item, and correction cycles defined as completion refusals plus
  post-completion reopenings.
- **Acceptance:**
  1. Per work item, telemetry records `ci.executions` and `ci.minutes`, taken from the CI provider's run list filtered
     to the item's commits. When the provider is unreachable these are `unavailable`, never 0.
  2. `correction.cycles` is derived from recorded refusals and reopenings.
  3. The reliability report shows cost per accepted requirement with each component's availability.
- **Compatibility:** additive metric ids registered in the metric registry.

### A4 Real-provider tests earlier

- **Owner:** application and rehearsal gate (Indy-init lineage), with policy recorded in RELEASE-GATES.md §3. Not a
  toolchain increment.
- **Acceptance:**
  1. For any slice that writes to a persistence or authorization boundary, the live-provider test for that boundary
     runs at the slice's first checkpoint, not only at final integration.
  2. Final integration still runs the full live suite.
  3. A Rehearsal 3 amendment needs the owner (OD-4).

### A6 Compatibility evidence reuse

- **Owners:** echelon-registry (A6a), conditor (A6b). **Status:** not started.
- **Sources:**
  - Registry intake `2026-10-23-EP-A6a-explicit-approval-and-immutable-sets.md` (new);
  - Conditor: the existing CON-INDY-050..054 drafts. No duplicate intake; the program only references them.
- **A6a acceptance (Registry):**
  1. Every echelon-current profile version is kept as an immutable set with `approval {by, at, evidence}`.
  2. Releases known but not approved are recorded as `assessed: pending|rejected`. Today Praxis 3.17–3.19, Dokimos
     0.7.0, Forma 0.9.1, Limen 0.9.1 and Aegis 2.0.0 are unregistered or silently excluded.
  3. Resolution never selects an unapproved release, and a test proves it.
- **A6b acceptance (Conditor):** per CON-INDY-050..054. A prior environment receipt is reused only while the
  resolved-set digest, the descriptor digests and the host fingerprint match.

---

## Wave B: verified construction, one bounded vertical slice

**Fixture:** `contracts/fixtures/invoice-slice/`. Its README lists the five frozen expected outcomes. Everything here is
**experimental** and stays outside default build and CI paths until EXPERIMENTS.md §6 promotes it.

### B1 Praxis authority handoff export

- **Owner:** praxis. **Status:** not started.
- **Source:** VC-003 (praxis inbox) plus VAC-002-01 R1 (forwarded) plus R-PRAX-1 (praxis inbox).
- **Acceptance:**
  1. `praxis handoff export --format echelon.authority-handoff/0.1 --work ID` emits C1 from canonical RQ and DF
     records, open questions and recorded observations. The output is deterministic and schema-valid.
  2. Contract tests:
     - an agent-written decision is exported as `proposed`, never `accepted`;
     - superseded records carry `supersededBy`;
     - code-derived rules appear only as observations.
  3. The exported invoice fixture equals the hand-authored `handoff.json` modulo `produced`.
  4. Gated behind an experimental flag.
- **Compatibility:** `ros.handoff-authority` v1 output unchanged.

### B2 Ordo provenance-backed construction

- **Owner:** ordo. **Status:** prototype implemented and tested locally (ordo#105, 69/69); experimental.
- **Source:** VC-002 plus VAC-002-P3-03-R2 (ordo inbox); constraint from VAC-002-P3-02 / ordo#103.
- **Acceptance (VC-002's own):**
  1. Handoff admission accepts the fixture, and accepts the refuse-and-record question. It rejects:
     - an accepted decision without a human authorizer;
     - an observation claiming authority;
     - a superseded record cited as current.
  2. The existing Ordo emitter generates the invoice workflow tier; the value layer supplies single-case types and
     validated constructors.
  3. A payment above 10,000.00 is refused for **every** customer. Neither the STR- exemption nor the 25,000.00 limit
     exists in the constructed code.
  4. Void from PartiallyPaid is refused with a code naming Q-FIN-001, and the trace disposition is
     `deferred-pending-question`.
  5. Negative compile tests fail to compile:
     - constructing a validated payment directly;
     - persisting without the payments-service capability;
     - persisting a raw amount.
  6. A C2 trace and generated sources come out byte-identical on rerun.
  7. LIMITATIONS.md states what is runtime-only, and that compile tests do not show prevention of unauthorized
     decisions.
- **Compatibility:** no change to Ordo's released packages, CLI or CI.

### B3 Dokimos provenance and invariant audit

- **Owner:** dokimos. **Status:** prototype implemented and tested locally (dokimos#53, 59/59); experimental.
- **Source:** VAC-002-P3-03-R1/R3 plus VC-004 (dokimos inbox, one requirement set).
- **Acceptance:**
  1. On the fixture's legacy code, the audit reports OBS-LEGACY-001 (exemption) and OBS-LEGACY-002 (superseded limit)
     as `uncertain-authority`, non-blocking, owner finance-controller. The legacy file's bytes are unchanged.
  2. Constructed-code checks report:
     - citing superseded DEC-FIN-000 → proven;
     - an unmarked rule constant → missing-provenance;
     - encoding Q-FIN-001 as a rule → `unresolved-question-encoded-as-rule`.
  3. The invariant oracle reports INV-INV-001..004 as holding within its stated bound on a reference model. Every
     seeded mutant (dropped limit, STR- exemption, overpayment, void-after-payment, Paid with balance) is reported
     violated, with a counterexample.
  4. Output is C3, deterministic, with validity digests. `isReusable` gives a distinct invalidation per changed digest.
- **Compatibility:** no change to released CLI, results schema or CI gates.

### B4 Integration run

- **Owner:** coordinator (CBE program). **Status:** run 2026-10-23; five outcomes PASS, Praxis step NOT_RUN ([integration/b4/B4-RESULT.md](integration/b4/B4-RESULT.md)).
- **Acceptance:** one script runs, in order:
  1. fixture handoff;
  2. Ordo admission and construction;
  3. `dotnet build` and tests of the constructed model;
  4. Dokimos audit and invariant oracle against the **built** `Invoice.Slice.dll`;
  5. an evidence bundle (handoff digest, trace digest, audit digest, build and test results).
- The bundle is then mapped to the C4 completion evidence form.
- **Praxis completion of the slice** (`work complete --evidence`) is attempted in a scratch Praxis-initialized
  repository. If that cannot be done without a released Praxis containing `work finish`, the step is reported
  NOT_RUN, not passed.
- **Record:** all five frozen outcomes in the fixture README, each PASS, FAIL or NOT_RUN with evidence paths.

---

## Wave C: execution efficiency (bounded)

| ID | Increment | Owner | Source | Acceptance | Status |
|---|---|---|---|---|---|
| C1 | Minimal worker tool profile | praxis | REL-TOKEN-004 (existing, pending) | Derived per that input; the profile is recorded in telemetry per execution | not started |
| C2 | Durable handoffs | praxis | — | Already status 1. Program work uses `work checkpoint` and `work continue` | done (existing) |
| C3 | Typed inter-agent messages | praxis | DF-A060..A074 (draft) | Decide the drafts (owner) before new work. No new protocol | blocked on owner |
| C4/C6 | Parallel and critical-path dispatch | praxis | PRX-PLAN-080..094, PRX-PLAN-045 | Stay advisory until EXP-2 measures CI and elapsed effect. Promotion through EXPERIMENTS.md §6 | not started |
| C5 | Checkpoint-driven CI | praxis | praxis#122 (open), PRX-PLAN-020 | Reuse Dokimos's existing `debounce` job pattern. Full CI runs at checkpoint commits and PR readiness; cheap checks run per push; mandatory gates are never skipped. Measured in EXP-2 | not started |

## Requirements ingestion record

| Increment | Repository | Intake path | Relation to existing records |
|---|---|---|---|
| EP-A3 | praxis | `.praxis/inbox/documents/2026-10-23-EP-A3-completion-in-use.md` | Extends PRAXIS-REL-003/006; adds the CI end-to-end obligation only |
| EP-A2b | praxis | `.praxis/inbox/documents/2026-10-23-EP-A2b-closure-scoped-reuse.md` | Extends DF-A067 and the validation-result binding |
| EP-A1 | praxis | `.praxis/inbox/documents/2026-10-23-EP-A1-dependency-aware-verification.md` | New; no existing specification |
| EP-A5 | praxis | `.praxis/inbox/documents/2026-10-23-EP-A5-ci-and-correction-telemetry.md` | Adds CI and correction metrics only; cites REL-TOKEN-001/002, PRAXIS-REL-004, VAC-CONT-001 |
| EP-A2a | dokimos | `.praxis/inbox/documents/2026-10-23-EP-A2a-evidence-validity-conditions.md` | Extends `CompletionVerification.fs` reuse |
| EP-01 | dokimos | `.praxis/inbox/documents/2026-10-23-EP-01-runner-image-drift.md` | New |
| EP-A6a | echelon-registry | `.praxis/inbox/documents/2026-10-23-EP-A6a-explicit-approval-and-immutable-sets.md` | Complements REG-RU-001..007 |
| B1 | praxis | VC-003, VAC-002-P3-01 (merged) | Existing; no new intake |
| B2 | ordo | VC-002, VAC-002-P3-02 (merged) | Existing; no new intake |
| B3 | dokimos | VC-004, VAC-002-P3-03 (merged) | Existing; no new intake |
| EXP-1 | cohort-based-engineering | VC-001 (merged) | Existing; no new intake |
| EXP-2, EXP-3 | cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-EXP-2-verification-scheduling-replay.md`, `2026-10-23-EXP-3-rule-provenance-offline.md` | EXP-3 extends VAC-002-P3-03-R3 and P3-01-R2 |
