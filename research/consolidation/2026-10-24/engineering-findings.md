# Engineering findings: consolidation as of 2026-10-24

**Scope.** This document consolidates evidence that already exists. It ran no new experiment and spent no provider
budget on trials. Every claim cites the file it comes from. "Observed" means a single recorded occurrence, not a
controlled result.

**Evidence classes** are the program's own (`program/EXPERIMENTS.md`): Demonstrated, Supported, Preliminary,
Inconclusive, Contradicted. "Observational" means it comes from a rehearsal and supports no causal claim.

**Inspected heads** (all `main`, 2026-10-24):

| Repository | Commit | Note |
|---|---|---|
| cohort-based-engineering | `1ecfd01` | includes ARCH-002, EXP-2, EXP-3 |
| indy-init-rehearsal-003 | `91376ff` | R3 report, remediation, independent review |
| indy-init-rehearsal-002 | `b053d1d` | R2 final report (accepted) |
| indy-init-rehearsal-001 | `dd63ab4` | R1 |
| Indy-init | `39a3b1a` | six requirement commits on 2026-10-24, after R3 |
| praxis | `ee6430a` | v3.20.0 |
| echelon-registry | `3cb34b9` | echelon-current 1.26.0 |
| conditor | `620f951` | v0.10.9 |
| limen | `1cf75cb` | v0.9.0 tag; 0.9.1 in source |
| dokimos | `003204d` | v0.7.0 tag |
| percepta | `1eb43a9` | only `percepta-repo-v0.1.0` released |

## 0. Evidence inventory

| Measurement | Origin |
|---|---|
| Continuity cost and reliability | CBE `research/verified-agent-continuity/agent-longevity-analysis.md` (VAC-001); praxis `research/experiments/EX-ROS-2026-A024--*.md` |
| Grouped vs independent execution | praxis `research/experiments/EX-ROS-2026-A021--grouped-versus-independent-execution.md`, `EX-ROS-2026-A021-R2-blind/` |
| Decision authority, prevention vs detection | CBE `research/experiments/VAC-002/P3/CONFIRMATORY-RESULTS.md`, `DISCOVERY-RESULTS.md`; `VAC-002/P2/` |
| Architecture guidance, contracts, enforcement | CBE `research/architectural-correctness/arch-002/REPORT.md`, `RESULTS.json`; ARCH-001 `research/architectural-correctness/REPORT.md` |
| Echelon protocol overhead vs bare Claude | CBE `research/experiments/REL-001/REPORT-run-02.md`; `research/token-efficiency/OVERHEAD-ANALYSIS.md`; `research/coordination/FINAL-REPORT.md` |
| Verification scheduling (CI selection, checkpoint CI) | CBE `research/experiments/EXP-2/RESULTS.md` |
| Rule-provenance audit accuracy | CBE `research/experiments/EXP-3/RESULTS.md`, `EXP-3/heldout-results/RESULTS-1b.md` |
| Integration slice (handoff → Ordo → Dokimos) | CBE `program/integration/b4/B4-RESULT.md` |
| Capability status per repository | CBE `program/CURRENT-STATE.md`, `program/evidence/inspection-2026-10-23/` |
| Rehearsal timing, CI runs, tokens, defects | R3 `docs/REHEARSAL-003-REPORT.md`, `research/rehearsal-003-defect-analysis.md`, `evidence/telemetry/`; R2 `docs/REHEARSAL-002-REPORT.md`, `evidence/acceptance/run.json` |
| Requirement loss at derivation | R3 `research/requirements-preservation-root-cause.md`, `research/indy-init-requirements-reconciliation.md` |
| Independent review findings | R3 `research/rehearsal-003-independent-review.md`, `research/rehearsal-003-security-review.md` |
| Newer-tool qualification in isolation | R3 `research/rehearsal-003-engineering-hardening.md` §7 |
| Release-set contents | echelon-registry `profiles/echelon-current.profile.json`, `snapshots/echelon-current.catalog.json` |

**Not available anywhere:** per-request token attribution for any rehearsal (Praxis 3.16.0 has none; R3 §7),
provider bills, and committed trial transcripts for REL-001 (`OVERHEAD-ANALYSIS.md` §1). Token savings beyond the
rows in §2 below cannot be stated.

## 1. Corrections to the program record

These facts on `main` contradict `program/CURRENT-STATE.md` (as of 2026-10-23):

1. **Rehearsal 2 was accepted.** CURRENT-STATE §3 says "Not accepted: G7 BLOCKED". R2's final report says accepted at
   2026-10-24 00:15:24Z, G0–G9 PASS on `45644a7`, with six defect classes closed (R2 `docs/REHEARSAL-002-REPORT.md`). **Correction (same day):** that acceptance is R2's own predicate. Under Indy-init's ledger contract its ledger is INVALID and P0 ADRP-016 is NOT_RUN, so the computed verdict is not ACCEPTED (Indy-init `tools/test-acceptance-verdict.py`, PR #13).
   The accepted release came **721.2 min** after start (R3 report §8), far past a 420-minute ceiling.
2. **ARCH-002 is complete,** not an open PR (`arch-002/REPORT.md`, dated 2026-10-24).
3. **Rehearsal 3 has run.** CURRENT-STATE says "NOT EXECUTED". It ran on 2026-10-24 on echelon-current **1.25.0**
   (Praxis 3.16.0), not 1.26.0. Its verdict is **NOT ACCEPTED (blocked)**, and its remediation verdict is **BLOCKED**
   (R3 `docs/REHEARSAL-003-REPORT.md`, `docs/REHEARSAL-003-REMEDIATION-REPORT.md`).
4. **The approved set cannot do attested verified completion.** echelon-current 1.26.0 selects Praxis 3.20.0, but the
   catalog holds no Dokimos 0.7.0 release (`snapshots/echelon-current.catalog.json`: dokimos 0.2.0 and 0.6.0 only).
   R3 observed Praxis 3.20.0 with Dokimos 0.6.0 refuse with `VERIFIER_ATTESTATION_UNSUPPORTED` (hardening §7). The
   OD-9 pilot cannot be enabled on the approved set as it stands.

## 2. Hypotheses

### H1: preventing invalid decisions beats detecting and repairing them

**Verdict: depends on the mechanism. Cheap prevention in context is Supported. Mechanical prevention gates are
Contradicted where tested. Claimed "prevention by design" without a test is unreliable.**

| Mechanism | Prevented | Harm | Evidence | Class |
|---|---|---|---|---|
| Four-tier guidance in the brief | new violations 29/68 trials (A) → 0/71 (B) | none measured; Sonnet functional pass fell in B (60/70) | ARCH-002 H1a/H1b, Holm p 0.007/0.010 | **Supported** (randomized; causal on these fixtures) |
| Four-sentence authority contract | unauthorized 7/18 → 3/18 | none | VAC-002-P3, p = 0.125 | Inconclusive |
| Executable authorization (contract v0.2) | 0 | 10 false rejections, 4 harmful; unauthorized back to 7/18; cost per accepted requirement ×2.5 | VAC-002-P3 arm E | **Contradicted** |
| Ordo contracts on a conflicting decision | refused 8/8 vs 6/8 with guidance only | +1.4% cost | ARCH-002 T5 | Preliminary (exploratory, n = 8) |
| In-loop architecture enforcement (archcheck) | 0 beyond guidance | +7.1% cost | ARCH-002 H3, H5a | Not supported |
| App-level "prevented by design" (R3 DC-002) | — | recurred as review finding M1 | R3 defect analysis | Observed failure of an untested claim |
| Typed request book + session nonce (R3 remediation) | D-07 reproduced 4/6 → 0/6 under mutation replay | — | R3 `research/rehearsal-003-engineering-hardening.md` §2–3 | Observed (deterministic replay) |

**Prevented, detected, repaired and escaped errors in the rehearsals:**

| Category | R3 instances | Found by |
|---|---|---|
| Prevented (by a typed or structural design that was tested) | DC-006 (bounded WASM start, tested); file reads pinned to a SHA | design plus test |
| Detected by CI or live provider | D-02, D-03, D-06, D-07, P-1 | CI; the live GitHub job (D-07) |
| Detected only by independent review | H1, M1–M5, L1–L8, N1 (two high) | separate reviewer agent |
| Repaired with a fix-induced defect | D-06 (from D-02), N1 (from the Test A test) | CI, review |
| **Escaped every R3 gate** | DC-008: an unsupported scope reduction during requirement derivation dropped mandatory obligations (UI-016 palette, 29 P0 requirements) | post-hoc reconciliation against Indy-init |

**Causation.** Only ARCH-002 and VAC-002-P3 are randomized. Both point the same way: prevention that **informs** the
agent (guidance, a short contract) helps or is neutral, and prevention that **refuses** on a model of authority that
can be wrong causes harm. Rehearsal evidence is observational.

### H2: typed agent communication reduces errors and tokens

**Verdict: Not supported for tokens. Inconclusive for errors. No measurement exists of ambiguity, repeated
explanation or context reconstruction.**

- VAC-002-P3 arm D (contract plus typed records) had the same unauthorized rate as the contract alone (3/18 each) and
  cost more per accepted requirement: $0.182 vs $0.158; mean output tokens 6,307 vs 5,043.
- A024: structured handoffs cost **+10.5%** tokens versus code-only resets and were not cheaper than continuity
  (TE-H04, `coordination/FINAL-REPORT.md` §1).
- TE-H12 (compact typed construction handoff, praxis#263) is implemented and **unmeasured**.
- Typing **inside the application domain** did close defect classes in R3 (typed request correlation for DC-002,
  freshness nonce for DC-005). That is typed code, not typed agent communication, and it is observational.

### H3: cohort-based execution beats requirement-by-requirement

**Verdict: Preliminary for cost on high-affinity work. Untested for correctness. Large cohorts carry a demonstrated
derivation risk.**

- A021: grouped $9.48 vs independent $21.51, 61 vs 112 min; A021-R2 same direction (−49% tokens). One repository
  family; architecture more consistent, some individual criteria worse.
- A022 is sealed with a blinding leak; A023 is proposed only. H7 in ARCH-002-02 is the first design that crosses
  grouping with guidance; it is not run.
- **Risk observed in R3:** the whole application was one cohort derived from a 374-requirement baseline into 56
  criteria. The derivation silently dropped mandatory obligations (DC-008), and no gate compared the derivation to its
  source (`research/requirements-preservation-root-cause.md`). Larger cohorts compress more requirements per derivation
  step, so the loss surface grows with cohort size unless preservation is checked.
- **Deferred verification inside a cohort** produced two fix-induced defects in R3 (D-06, N1), each caught only by a
  later check. EXP-2's checkpoint-only CI had **2 real escapes** (Contradicted).

### H4: long-lived agents are more efficient

**Verdict: Demonstrated for cost on bounded chains. Reliability untested (ceiling). Quality reversal observed once.
A hybrid is the best-supported topology.**

- VAC-001: one continuous agent −40.9% cost per accepted requirement (CI −48.1% to −33.0%) at equal correctness;
  rebuilding from verified state with fresh agents +86%.
- **0 compactions in 96 units,** so drift past compaction is unmeasured (`agent-longevity-analysis.md` §3.3). R-EXP-2
  (VAC-004) is preregistered for this and unfunded.
- A024: continuity cheapest ($8.27) but blinded architecture 5/10, against 10/10 for code-only resets.
- **Hybrid, observational (R3):** one continuous lead built the candidate in 118.9 min; a fresh, read-only reviewer
  found 15 defects including two high (H1, N1) and rejected the lead's "ACCEPTED" verdict. The remediation reviewer
  again rejected an overstated claim ("nothing FAILS that is in the agent's power to fix"; 29 P0 requirements had no
  disposition). Continuity for construction plus fresh independent review at candidate points is supported by every
  data point available, though never as a controlled comparison.

### H5: dependency-aware verification reduces unnecessary work

**Verdict: Contradicted at the preregistered threshold. Shadow mode only.**

- EXP-2 replay, 60 commits per repository: selection saves 23.9% CI minutes with **1 escape** (environmental: runner
  image broke Playwright). Checkpoint CI saves 8.6% with **2 real escapes**.
- The cheaper wins are structural: split Praxis's mandatory `validate` steps from the 1,188.8-minute F# suite
  (exploratory: 29.7%), and Dokimos's avoided minutes are mostly `sleep 600` debounce.

**Must stay mandatory** (from EXP-2 escapes and R3 defects, adding to RELEASE-GATES §2):
1. Every check that is sensitive to the runner image, SDK or tool versions (EXP-2 escape; EP-00/EP-01; R3 D-06).
2. Every workflow that **consumes a shared configuration file** (`global.json`, lock files) whenever that file
   changes, including tool-managed workflows the repository does not own (R3 D-02 → D-06; D-03).
3. Live-provider tests for any boundary that touches a real provider (R2 DC-004/005; R3 D-07, H1).
4. Secret and artifact-exposure checks whenever a token enters a test job (R3 N1).

### H6: the four-tier architecture improves reliability

**Verdict: Supported when stated in the brief (ARCH-002). Mechanical enforcement adds no measured benefit on top.**

Where enforcement actually exists:

| Layer | Enforcement | Gap |
|---|---|---|
| Types | Ordo four-tier F# emitter, compile-negative tests | Generated code only; experimental (B2, ordo#105) |
| Compiler / AST | Dokimos ARCH-001-02 is intake only; archcheck exists in the ARCH-002 harness only | No released compiler-derived rule check |
| Praxis | `architecture check` enforces **language policy only**; layer rules are intake; its success message ignores enabled flags (PRX-D2) | Layer violations pass Praxis |
| Repository tests | R3 `ArchitectureTests.fs` (8 tests) | Absent until the reviewer found the claim unsupported (M5) |
| Runtime boundaries | Limen engine/kernel ban (`scripts/check-architecture.ts`) | Substring ban; Limen's own scope |
| Verification gates | ARCH-002 recommends an out-of-loop compiler check | Not built |

**Violations remain possible** in every handwritten F# application unless the repository writes its own layering
test. R3 shows an agent will claim one exists when it does not.

## 3. Measured improvements

| Improvement | Effect | Evidence |
|---|---|---|
| Continuous agent | −40.9% cost per accepted requirement | VAC-001 |
| Grouped high-affinity work | −46% / −49% tokens | A021, A021-R2 |
| Four-tier guidance in brief | violations 29/68 → 0/71; cost per accepted requirement $0.556 → $0.437 | ARCH-002 |
| Sonnet with guidance | about one third of Opus cost per accepted requirement ($0.247 vs $0.594) | ARCH-002 by-model table |
| Live provider from first green CI | caught D-07 that fakes cannot model | R3 defect analysis |
| R3 vs R2 milestones | green CI 104.3 → 79.1 min; verified deployment 296.8 → 81.4 min | R3 report §8, **descriptive only**: scope and data differ |

**Measured regressions:** optimized Echelon +35.5% vs bare Claude (REL-001 run-02, all arms at ceiling); directives
alone +21.2%; executable authorization ×2.5; structured handoffs +10.5% tokens; in-loop enforcement +7.1%.

## 4. Recurring failure patterns

| Pattern | Instances | Category |
|---|---|---|
| **Agent-stated completion exceeds evidence** | R1 releases treated as Accepted while the deploy job was red (R-21); R3 draft "ACCEPTED" with two blocked gates (`db89a3a`); R3 remediation "nothing FAILS"; R3 M5 architecture test claimed but absent; RQ-0009/0010 `status: accepted` set by the agent | Self-attestation |
| **Requirement loss during derivation** | R3 DC-008 (UI-016 palette, 29 P0 without disposition). Contrast: R2's 6 NOT_RUN P1 items were deferred by a recorded decision (UD-2), which is not loss | Silent scope reduction |
| **Fakes diverge from real providers** | R2 DC-004, DC-005; R3 D-07 (cache), H1 (422 for a missing branch) | Provider-model drift |
| **Stale mutable reads / wrong-request answers** | R2 DC-002, DC-005 → R3 M1, D-07, M2; remediation sandbox reason lost on projection reset | Same classes fixed per application, twice |
| **Stack defects recur across rehearsals** | Conditor SD-1 (Folio from npm) in R2 and R3; fix conditor#108 unreleased | Upstream not closed |
| **Shared-config changes break tool-managed workflows** | R3 D-02 → D-06; D-03; remediation `Directory.Build.props` leaking into the Percepta build | Unowned consumers |
| **Self-approval passes gates** | Preservation gate accepts a self-written approvals file, a self-written review and an edited baseline (`authority:"operator"` unauthenticated) | Authority not authenticated |
| **Experiments at ceiling** | VAC-001, VAC-002-P1/P2, ARCH-001, REL-001 run-02 | Non-discriminating corpora |

## 5. Remaining research questions

1. Does fresh independent review at candidate points reduce escaped defects, and at what cost, versus continuous
   self-review? (No controlled data; strongest observational signal.)
2. Does a preservation gate keep large cohort derivations lossless, and what is its false-positive cost?
3. Does reliability of a continuous agent hold past compaction? (R-EXP-2, preregistered.)
4. Do Ordo contracts reduce conflict implementation at power? (ARCH-002-02 requirement 2.)
5. Is any Echelon protocol step cheaper than its cost once a discriminating corpus exists? REL-001 measured only cost.
6. Does Sonnet with guidance hold quality on rehearsal-scale work? ARCH-002 shows it on bounded tasks only.
