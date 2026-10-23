# Echelon research inventory (read-only inspection, 2026-10-23)

> Agent-generated inspection report, kept as the evidence CURRENT-STATE.md cites. `kemiller2002/research-documents` is
> private: for it this report gives paths and conclusions only, not its data.

This is a read-only inspection. Nothing was modified, committed or pushed.

Repos inspected:
- `/home/user/cohort-based-engineering` (CBE), main `9531430`, deepened to 179 commits.
- `/home/user/research-documents` (RD), main `b372a7f`.
- `/home/user/{praxis,ordo,dokimos,conditor,echelon-registry,causa-data}`.
- Clones in `scratchpad/clones/`: `Indy-init` (`734c4bd`), `indy-init-rehearsal-001`, `indy-init-rehearsal-002` (`6379358`), `construct-010-trials`.
- GitHub PR metadata via MCP.

Path abbreviations: `CBE/` = `/home/user/cohort-based-engineering/`, `RD/` = `/home/user/research-documents/`, `INDY/` = the Indy-init clone.

---

## 1. VAC-001: verified agent continuity

**Location**
- Analysis and deliverables: `CBE/research/verified-agent-continuity/`. Its README lists 15 deliverables: evidence-baseline, research-protocol, metrics-schema(-2), experiment-manifest, pilot-results, hallucination-evaluation, error-propagation-results, agent-longevity-analysis, verified-continuity-design, engineering-recommendations, publication-readiness, r-exp-1/2 protocols, `analysis/r-exp-plan.json`.
- Harness and data: `CBE/research/experiments/VAC-001/` (harness `vac.sh`/`vac.fsx`, briefs, arm-files, faults, directives, `results/`).
- RD summary: `RD/research/verified-agent-continuity/FINDINGS.md`.
- PRs: CBE#14 (merged 2026-10-22) and RD#17 (merged 2026-10-22).
- Commits: protocol preregistered at `05b3cf2`; P1 `4ffd200`; R1/F1 `7bcecfc`; Layer 3 and publication readiness `669831b`.

**Design**
- 96 chained units: 11 chains of 8 changes on the REL-001 run-03 F# Ledger fixture (tasks V1–V8; V7 descoped by A1).
- Model claude-opus-5-5, medium effort. Scored by a hidden cumulative oracle outside the workspace.
- Arms:
  - A: fresh agent per change, with an agent-written handoff.
  - B: one continuous agent.
  - C: B plus Ordo admission, VAC-RULES and decision records.
  - D: C plus the Praxis protocol, an independent gate and verified state.
  - DR: D with a fresh agent per change, rebuilt from verified state.
- Runs: P1 pilot, R1 replication, F1 fault injection (20 false premises).
- Layer 3: blinded decision adjudication, κ 0.905.
- Amendments: A1–A4.
- K0 cache condition: sub-agents shared the orchestrator's prompt-cache prefix.

**Results** (README table)
- B vs A: **−40.9% cost per accepted requirement** (CI −48.1% to −33.0%, 16 blocks). Replicated at −38.1% in F1.
- Controls on top of continuity: C +14.1% vs B; D +16.8% (no faults) and +31.0% (F1).
- DR: +86% vs D and +51% vs A.
- Correctness, drift and fault rejection were at ceiling in every arm:
  - 0 regressions, 0 false completions, 0 architecture violations;
  - 0/20 injected premises accepted;
  - 0 fabricated premises in 441 decisions.
- 8 of 202 adjudicated decisions were unsupported scope additions presented as settled.

**Status:** complete (2026-10-21) within scope. The reliability hypotheses are untested because everything was at ceiling.

**Limitations** (`publication-readiness.md`)
- One fixture, one model, 8-change chains, 0 compactions, K0 cache sharing.
- Run-level analysis code was written during the runs.
- Transcripts are not committed; a content-free `requests.jsonl` ledger is committed instead.
- Output tokens are a lower bound (A4).
- Verifier and agent share a uid.
- Orchestrator cost is not attributed.
- Claims C8 and C9 ("verified state makes reliability independent of session length", "controls prevent hallucination") are marked **must not be claimed**.

**R-EXP-1 and R-EXP-2: preregistered designs, NOT RUN**
- Sources: CBE README; `operating-model.md` §9; `r-exp-plan.json` label "PLANNING ESTIMATE; no R-EXP-1 or R-EXP-2 trial has run".
- R-EXP-1 (= VAC-003, `r-exp-1-protocol.md`)
  - Design: a fixture whose baseline fails; tests H3, H5, H6; 5 arms; 16-unit chains.
  - Qualification ceiling: **$80 hard**, with a stop file at $65.
  - Confirmatory: about $2,300 at a 20% baseline (up to about $4,700 at 40%). Needs an explicit owner ceiling, which has not been given.
- R-EXP-2 (= VAC-004, `r-exp-2-protocol.md`)
  - Design: K1 chains of 24 or more units past compaction, cross-family Layer 3, H2; arms A, B, D and BX.
  - Ceilings: calibration $60 hard; pilot **$110 hard** (stop at $90).
  - Confirmatory: about $3,600. No ceiling has been given.
- Naming collision to watch:
  - VAC-001 has a recommendation also labelled "R-EXP-3" (a measurement practice).
  - VAC-002 uses "R-EXP-4" for its second pilot.
  - P3 uses "R-EXP-3" for corpus design.

## 2. VAC-002 (pilot P1), P2 and P3

All three live under `CBE/research/experiments/VAC-002/`. Summaries are in `RD/research/agent-reliability/` (`VAC-002-long-horizon-reliability-pilot.md`, `VAC-002-P2-decision-authority-pilot.md`, `VAC-002-P3-minimal-authority-contract.md`).

**VAC-002 / pilot P1: long-horizon reliability and adaptive enforcement**
- PRs: CBE#18 (merged 2026-10-22), RD#21. FREEZE commit `0011132`.
- Design: six arms A–F, K1 isolated CLI, Lending fixture, 12-unit chain (L01–L12), sealed oracle, Layer 3 review.
- Status: **checkpoint, not complete.**
  - The 25-, 50- and 100-change confirmatory runs were not run. No ceiling was given; the projection was about $4,000–4,500 (`BUDGET.md`).
  - The pilot failed its discrimination check (72/72 accepted).
  - Pilot ceiling was $120 hard, with a stop at $95. The pilot cost about $43.82 (cli-estimate).
- Results:
  - 0 automated failures in every arm.
  - Layer 3 found one consequential error the oracle missed: arm B silently exempted staff from the L04 5.00 money-owed refusal (`RESULTS.md` §1).
  - Continuity was 32% cheaper. Full controls cost +13%. Adaptive enforcement (arm E) saved nothing (`ADAPTIVE-ENFORCEMENT.md`).
- Intakes in `CBE/.praxis/inbox/documents/2026-10-22-VAC-002-0{1..4}-*.md`:
  - 01: verified state binds to executed checks;
  - 02: session-aware cost telemetry;
  - 03: discriminating corpus and second pilot;
  - 04: adaptive verification deferred.

**P2: unauthorized-decision prevention and verified decision authority**
- PRs: CBE#20 merged into the #18 *branch* after #18 had landed, so it reached main only via #21; RD#23.
- FREEZE commit `2bdc929`. Results commit `fe43f62`.
- Design: 12 scenarios × 5 arms = 60 executions. Arms: natural language, checklist, typed records, executable authorization, adaptive independent review.
- Budget: $57.50 of $150.
- Results:
  - 0 of 80 opportunities produced an unauthorized decision. The pilot failed its discrimination check.
  - Control costs: 1.76× (D) and 3.25× (E).
  - The controls caused all 3 functional or consistency failures, through false rejections.
  - Contract v0.1 had 5 defects, which v0.2 fixes.
  - Confound: every arm received the README "Authority" section.
  - Root cause of the original L04 error, reconstructed from the agent's records (`P2/ROOT-CAUSE.md`): the agent invented a precedence rule ("specific overrides general") and applied ownership inconsistently. It was neither hallucination nor drift. The oracle tested only one side of the case.
- Docs: `P2/README.md`, `ROOT-CAUSE.md`, `DECISION-AUTHORITY.md` (contract v0.1/v0.2), `RECOMMENDATIONS.md`.
- Intakes: `2026-10-22-VAC-002-P2-0{1,2}-*.md`.

**P3: minimal authority contract (authority ablation)**
- PRs: CBE#21 (merged 2026-10-23T13:23Z, merge commit **`9531430`**), RD#25 (merged).
- Freezes: Stage 1 `766351a`; round 2 `4e98d3d`; Stage 2 CR-1 `78026ea`. S2 results commit `a9e6d0d`.
- Design:
  - The README authority section was removed from every arm (exposure manifest 27/27).
  - The frozen four-sentence contract (`P3/AUTHORITY-CONTRACT.md`) was varied across 5 arms: none, contract, + checklist, + typed records, + executable authorization (contract v0.2).
  - Stage 1 discovery: round 1 1/40 (did not qualify); round 2 11/15 (qualified). Sizing run: B 1/15.
  - Stage 2 confirmatory: C01–C06 × 3 replicates × 5 arms = 90 executions, sealed oracles, double-blinded review.
- Budget: $92.31 of $150, hard stop at $140 (`P3/BUDGET.md`).
- Results:

| Hypothesis | Result | Class |
|---|---|---|
| H1 (contract reduces errors) | 3/18 vs 7/18, RD −0.22 [−0.56, 0], p = 0.125 | **Inconclusive** |
| H2/H3 (checklist and records add value) | Identical to the contract | Inconclusive |
| H4 (executable authorization adds prevention) | 7/18, 0 prevented | **Contradicted** in direction |
| H5 (contract cheapest per accepted requirement) | B/E = 0.40 [0.15–0.63]; B $0.158, E $0.395 | **Demonstrated** |

**P3 failure mechanisms** (`P3/README.md`; `CONFIRMATORY-RESULTS.md` §§3, 5; `BLINDED-REVIEW.md` §§3–4; `results/S2/e-rejections.json`; intakes `CBE/.praxis/inbox/documents/2026-10-23-VAC-002-P3-0{1,2,3}-*.md`):

1. **Inherited, code-embedded rules: all 36 of 36 confirmed unauthorized decisions.** Each reused a rule in existing code that no accepted decision or requirement supports. Three kinds:
   - superseded rate or horizon: C01 24 h → 48 h; C02 30 → 21 days; D17 fee at the superseded rate;
   - unrecorded exemption: C05 nonprofits; C06 the k2 "walk-in" slots;
   - silent 0 / 0.00 default for an unlisted case: C03 visit fee; C04 shipping; D19.
2. **Announced temptations are declined, embedded ones are not.** D05 as a note: 0/2. D19, the same default inside a helper: 3/3. Announced temptations with no instruction at all: 1/40.
3. **C06 defeated every control (15/15).** It is an exemption framed as an operational fact inside the function that carries the accepted rule. Only post-hoc blinded review flagged it.
4. **Control-induced harm from executable authorization (arm E).**
   - Admission and the gate rejected 10 authorized or harmless decisions in 10 of 18 executions: tie-breaks (3), keeping accepted behaviour (2), recorded unresolved questions (4), one correct refusal.
   - 4 of those caused harm: three unauthorized 0.00 defaults (C03-r1, C04-r1, C04-r3), because no refusal was built and the helper's default reached the output; and one crash (C03-r3), where a correct refusal was rejected under A5 self-citation and the repair turn replaced it with an exception.
   - E's cost was +67% and its median wall time 2×.
5. **Implementer-written tests lock errors in.** In D19 and D21 the agent added tests asserting the unauthorized default.
6. **Scope changes outside any oracle probe.** In C01-E-r3 an existing command was changed without being asked; only review caught it. Review category counts per arm are in `BLINDED-REVIEW.md` §4, including scope additions and 2 false completion claims in E.

**P3 recommendations**
- R-PRAX-1: adopt the contract in the Praxis brief, as policy rather than as a proven control.
- R-ADM-1..3: fix checker defects.
- Remove executable authorization from defaults; do not adopt the checklist; defer typed records and blocking review.
- Next: R-PROV-1 (rule-provenance audit), R-REV-1 (targeted non-blocking review), and a powered confirmation (28–39 blocks of A and B, about $35–45).
- Intake requirement IDs: VAC-002-P3-01-R1..R4, -02-R1..R4, -03-R1..R3.

## 3. ARCH-001, ARCH-002, CONSTRUCT-0xx

**ARCH-001**
- Location: `CBE/research/architectural-correctness/` (PROTOCOL, REPORT, RESULTS.json, SCORING, ARCHITECTURE-RULES, verifier, sealed oracle). CBE#16, merged 2026-10-21. Preregistration freeze `6dc596a`.
- Design: 64 trials (8 tasks × 4 arms × 2 replicates) on the F# Lending four-tier fixture. Arms: A core; B guidance (SDE-DOCTRINE-003); C + Ordo contracts; D + archcheck enforcement.
- Results:
  - Complete ceiling: 128/128 accepted, 0 violations. H1, H2, H3 and H6 not supported.
  - Cost vs A: B +15.3%, C +19.9%, D +24.7%. Enforcement adds +48% wall time.
  - Exploratory: guidance improved blinded review scores (+0.59/6, p = 0.013).
- Intake: `CBE/.praxis/inbox/documents/2026-10-21-ARCH-001-04-violation-prone-replication.md`.

**ARCH-002**
- CBE PR **#17**, "violation-prone replication", is **OPEN** (head `48434ff`, created 2026-10-22). Not on main.

**CONSTRUCT-008: mechanical-first construction, time-entry timer**
- Location: `RD/research/construction-by-design/CONSTRUCT-008/` (preregistration frozen `0907939`, results.md, recommendation.md, Chrona/Summa validation). RD#11, merged.
- Implementation changes: ordo#73, praxis#257, dokimos#33.
- Results: n = 3 per arm, directional only (figures are in the private research-documents repository and are not repeated here).
- Recommendation: mechanical-first for cohorts expressible as approved decision records, with revisions.
- Program synthesis (`RD/.../echelon-foundry-program/SYNTHESIS-AND-RECOMMENDATION.md`, EF-SYN-001): **selective adoption, not a general default**.
  - No reliability gain.
  - Cheaper only where the vocabulary generates most of the slice.
  - The consistent gain is decision control: open questions become typed obligations.

**CONSTRUCT-010: reduce construction cost without sacrificing correctness**
- Records exist only on the **unmerged** RD branch `research/construct-010` (head `9137220`, 2026-10-14): preregistration, baseline, ecir, decisions, harness, vocabulary-coverage, idempotency-defect-analysis.
- Preregistration status: "draft (not frozen)". Arms A, C, C2, A+; 4 slices; target Indy Init 2026-11-07.
- RD#16 (Chrona decision inputs) merged.
- Trial repository `kemiller2002/construct-010-trials` (public) has only main plus `trial/smoke/test/000` and `001`. **No scored trials were found.**
- CONSTRUCT-010 phases are implemented in Ordo and Dokimos (decision classification, refusal codes, coverage report, `ordo/research/decisions/DF-SDE-2026-0022..0025`; Dokimos decision-completeness checks).

**Other CONSTRUCT IDs**
- 001: ordo#64/#67, typed construction vocabulary (DF-SDE-2026-0018).
- 002: ordo#65, construction engine.
- 007: `RD/.../time-entry-timer-01`.
- 009: Ordo ledger work items.
- 004–006: single mentions only.

## 4. CBE PRs

| PR | Title | State | Notes |
|---|---|---|---|
| #21 | VAC-002-P3: minimal authority contract (authority ablation); brings P2 onto main | **Merged** 2026-10-23T13:23Z, merge commit `9531430` (head `ea36618`) | 31 commits, 2,223 files; also brings P2 (`10e1adf`) onto main |
| #22 | VC-001: compare typed construction against post-hoc enforcement | **OPEN**, mergeable clean, head `0a294f9`, base `9531430` | Adds one 19-line file `.praxis/inbox/documents/2026-10-23-VC-001-verified-construction-experiment.md`. Not superseded; no later PR exists |
| #17 | ARCH-002 violation-prone replication | **OPEN** | |
| #20, #19, #18, #16, #14 … | | Merged | The MCP `merged` field reads false, but `merged_at` is set; get on #21 confirms merged: true |

Companion PRs opened in the same minute (2026-10-23 13:35), all **OPEN**:
- ordo#104 "VC-002: prototype provenance-backed F# construction";
- praxis#286 "VC-003: preserve decision authority across Praxis ingestion";
- dokimos#52 "VC-004: prototype provenance checks and targeted review".

Other open PRs:
- RD#24, CAUSA-REQUIREMENTS-CONSOLIDATION-001;
- praxis#141, A022 setup.

## 5. CBE operating model

**`CBE/docs/operating-model.md`**: "Status: proposed method, 2026-10-22". It covers:
- §1 lifecycle;
- §2 roles;
- §3 decisions: agent records enter as `proposed`; "verified" is computed;
- §4 continuity by default, with event-triggered restarts (VAC-CBE-001-R1);
- §5 extensions of a rule are assumptions (R2);
- §6 controls in proportion to evidence;
- §7 measurement: cost per accepted requirement; missing values are `unavailable`;
- §8 not adopted;
- §9 open experiments.

**`CBE/requirements/VAC-CBE-001.md`**: `status: implemented`, with a human `approved` contribution by kemiller2002 (2026-10-22). Source input: `.praxis/processed/INPUT-29db4a38cf86a56b/`. Landed in CBE#19 (`4c21527`).

**Status reading:** the overall method is still a proposal (README: "Research and design proposal, 2026-10-14"). The VAC-CBE-001 R1/R2 rules are owner-approved requirements written into that proposal document.

**Broken README links.** The README links three files that do not exist and never existed in history (checked with `git log --all`):
- `docs/cohort-planner.md`;
- `research/experiment-plan.md`;
- `docs/roadmap.md`.

## 6. "Previously proposed verified-construction requirements"

No file on any local main branch contains "verified construction", "verified-construction", "constrained construction" or "provenance-backed". GitHub code search returned 0 results, and `git log --all` with grep/-S also found nothing. The requirements exist **only in open PRs** (2026-10-23):

| ID | Where | Status | Gist |
|---|---|---|---|
| VC-001 | CBE#22, `.praxis/inbox/documents/2026-10-23-VC-001-verified-construction-experiment.md` | Open PR, intake only | Preregistered 4 arms: A TS, B strict TS with discriminated unions, C F#, D F# with requirement/decision-provenance construction. At least 2 fixtures (money-owed exemptions, unauthorized defaults, conflicting rules, transitions, persistence permissions); qualify the baseline; frozen functional and authority oracles; blinded review; budgeted pilot; no defaults change; keep four tiers; output to `research/experiments/VC-001/` |
| VC-002 | ordo#104, `2026-10-23-VC-002-provenance-backed-typed-construction.md` | Open | Versioned IR with requirement and decision IDs, supersession and unresolved questions; never infer authority from code; F# DUs and validated constructors; refusal and deferral remain valid; avoid R-ADM-1..3; traceability manifest |
| VC-003 | praxis#286, `2026-10-23-VC-003-authority-preserving-ingestion.md` | Open | IR distinguishes accepted requirements, authorized decisions, unresolved questions and observed legacy behaviour; code rules are observations; keep the four-sentence contract; deterministic handoff to Ordo |
| VC-004 | dokimos#52, `2026-10-23-VC-004-mechanical-provenance-verification.md` | Open | Static provenance checks; missing or stale provenance vs violation; block only on a validated formal invariant; targeted non-blocking review; measure precision, recall and false rejections |

Older related records (merged):
- `ordo/research/requirements/RQ-SDE-2026-0003--design-by-construction.md` (draft);
- `ordo/research/decisions/DF-SDE-2026-0018--constrain-construction-to-a-typed-vocabulary.md` (draft);
- the P3 intake requirements VAC-002-P3-03-R1..R3 (rule provenance) and the P2 contract v0.2.

## 7. Causa Rehearsals 1 and 2, and the Rehearsal 3 plan

**Rehearsal 1 (EX-INDY-INIT-2026-R001)**
- Locations:
  - repo `kemiller2002/indy-init-rehearsal-001` (PR #1; `evidence/MISSION-RESULT.md`);
  - full report `RD/research/construction-by-design/indy-init-r001/RESULT.md` with `ERRATA.md` (RD#18, RD#19).
- Result: **PASS** against the frozen criteria (AC-01–AC-14; at least 80% of functional requirements Verified).
  - T0 2026-10-21T16:26Z; stopped at **T+261.8 of 420 min**.
  - First green CI at T+88.
  - Final release `dffaf08`. CI 226/226; deploy accept job 72/72; 56/62 functional (90.3%).
  - Integration and verification took about 150 min against a 90-minute budget.
- Defects: 25 in `run/defects-and-rework.md`. Key ones:
  - R-21: the coordinator treated RC2–RC5 as Accepted while the deploy accept job was red (ER-2);
  - R-14 → R-18: forged-history class fixed per instance three times;
  - R-01/R-02: guessed ID grammars;
  - R-22: http without redirect.
- Unverified: real iPad, OAuth, live GitHub (mocked), no live LLM.
- Tokens: about 300M cache reads; no dollar cost available.
- Lessons (§11):
  - gate Accepted on the exact-SHA deploy accept job;
  - class-level fixes on recurrence;
  - adversarial review from the start, which was the best detector (28 findings);
  - pre-provision human prerequisites;
  - branch worktrees from HEAD.
- Follow-on in the same repo: CAUSA-REHEARSAL-INTEGRATION-001 (PRs #8–#10), **PARTIAL** (`evidence/causa-integration/RESULT.md`); the provider gate is incomplete (AC-PROV-03/04/05).

**Rehearsal 2 (causa-rehearsal-002)**
- Location: repo `kemiller2002/indy-init-rehearsal-002`, `docs/REHEARSAL-002-REPORT.md`, `evidence/acceptance/{run.json,ledger.json}` (PR #5, merged `6379358`).
- Run: 2026-10-23, start 12:14Z, using the stack `echelon-current` 1.25.0.
- Milestones:
  - first build 12.3 min;
  - first screen 44.4 min;
  - first green CI 104.3 min;
  - first verified remote write 176 min;
  - deployed and accepted build at **296.8 min**.
- Result: **Accepted: no.** G7 (defect-class closure) is BLOCKED because fixes were merged before the fourth independent review reported (UD-4). 72 requirements: 65 PASS, 6 NOT_RUN, 1 BLOCKED.
- Defect classes DC-001–006. Four recurred after a claimed fix. The real GitHub provider found DC-004 and DC-005, which mocks could not reach.
- Tokens were unavailable.
- Lesson: run the live provider suite from the first write onwards.

**Rehearsal 3 plan**
- Location: `INDY/docs/REHEARSAL-003-DEFERRED-VERIFICATION-EXPERIMENT.md`, commits `5e94e92` and `734c4bd` (2026-10-23 09:19–09:20 -0400, author Kevin Miller).
- Header: "Status: APPROVED EXPERIMENT DESIGN; NOT EXECUTED."
- Contents: requirements R3-DV-001..016 (all P0):
  - stack preflight and freeze first (`REHEARSAL-DEPENDENCY-LOCK.md`, DEP-CURRENT-001..008);
  - **420 min hard maximum, not a target**;
  - commits every 10–20 minutes, labelled UNVERIFIED;
  - defer noncritical tests, except security, data loss, authorization and contract-blocking issues;
  - a defect ledger;
  - event-driven phase exits;
  - a rolling latest-safe cutoff;
  - exact-SHA deployed acceptance;
  - stop on success or at 420 min;
  - compare with R001 and R002.
- Gates come from `INDY/docs/REHEARSAL-ACCEPTANCE-LEDGER.md` (G0–G10, acceptance predicate G0–G9).
- Preflight status: `INDY/docs/NEXT-REHEARSAL-PREFLIGHT-STATUS.md` lists several BLOCKED items (Forma 0.9 compatibility, F# interface freeze).
- **Not found:** a document with an explicit phase list, a named release set, or approval evidence beyond the "APPROVED" header and the owner-authored commit. There is no approval PR or record. The dependency-lock policy says to select the newest approved stable set at kickoff; R002 used `echelon-current` 1.25.0, the registry's current channel (`echelon-registry/channels/echelon-current/*.json`).

## 8. Praxis reliability and completion-gate research

**Praxis grouping and continuity experiments** (`/home/user/praxis/research/experiments/`)

| ID | Question | Status | Result |
|---|---|---|---|
| EX-ROS-2026-A021 | Grouped vs independent | completed | $9.48 vs $21.51; 61 vs 112 min |
| A021-R2 | Blind replication | done | Same direction |
| A022 | Affinity by execution mode | **blocked**; praxis#141 open | Sealed and withheld because of a blinding leak |
| A023 | Affinity across repository blocks | **proposed** | |
| A024 | Continuity vs resets vs handoffs | completed | $8.27 / $15.30 / $17.43; 36/36 frozen acceptance criteria in each; architecture 5/10/8 |

**REL-001** (`CBE/research/experiments/REL-001/`)
- Run-01: MODIFY.
- Run-02: 88 preregistered trials (`a00eba0`). Optimized Echelon D cost **+35.5%** vs bare (+24.9% to +49.5%), with all arms at ceiling 39/39.
- Run-03: draft, not preregistered.
- Completion gate (`gate/README.md`, `gate-report.json`):
  - first FAIL on evidence binding (REL-GATE-001);
  - later PASS attested / FAIL non-attested;
  - REL-GATE-003 resolved in v3.18.0;
  - REL-GATE-004 (trust root, policy and key pinning) resolved in **v3.19.0** (GATE-A5 `POLICY_CHANGED`, GATE-A6 `UNTRUSTED_AUTHORITY`).

**Readiness and coordination**
- `CBE/research/reliability/README.md` (2026-10-20, v3.17.0): optimizedWorkflowReady false. F6 rollout gate FAIL; PROBE-3/4 trust-root holes, later fixed in 3.19.0.
- `CBE/research/coordination/FINAL-REPORT.md`: Echelon has not been shown to be more efficient than bare Claude.
- **Registry gap:** `echelon-current` 1.25.0 still pins Praxis 3.16.0 (pre-REL-GATE-003/004 fixes). R002 listed Praxis 3.19.0 and Dokimos 0.7.0 as "newer but unapproved".

## 9. Prior protocols resembling the proposed EXP-1..4

| Proposed | Closest prior art |
|---|---|
| EXP-1 typed construction (TS / strict TS / F# / F# + provenance) | **VC-001 in CBE#22 is exactly this design (open, intake only).** Related: ARCH-001 (F# only, ceiling); CONSTRUCT-008/010 (mechanical-first F#); VC-002 (ordo#104). No TypeScript arm has ever been run |
| EXP-2 verification scheduling | Rehearsal 3 deferred verification (R3-DV-*); VAC-002 arm E adaptive enforcement (saved nothing; intake VAC-002-04 deferred); REL-001 F4 single verifier run (null, +2.3%); P2 arm E adaptive review (3.25×) |
| EXP-3 rule provenance | VAC-002-P3-03-R1..R3 / R-PROV-1, R-REV-1; VC-004 (dokimos#52); P3 C01–C06 corpus as ready fixtures |
| EXP-4 agent continuity | VAC-001; VAC-002 pilot; R-EXP-2 (VAC-004, preregistered, not run); A024 |

**Conventions used by prior experiments**
- Preregistration is committed in a "FREEZE" commit before any run, with frozen hashes (`harness/FROZEN*.sha256`). Amendments A1..An are logged in `PROTOCOL.md` with timing relative to the data. Confirmatory freezes are recorded separately (CR-1).
- Oracles are sealed: an encrypted store, `sealed/SEAL.json`, and the key published after scoring. There is an exposure or contamination scan (X4), and the oracle is self-checked (for example 119/119 or 43/43) before the freeze.
- Evidence classes:
  - VAC-002: Demonstrated / Supported but preliminary / Inconclusive / Contradicted;
  - ARCH-001: Not supported;
  - Rehearsals: PASS / FAIL / BLOCKED / NOT_RUN, and missing evidence is never PASS.
- Budgets: a hard ceiling per phase, a stop file at about 80–85%, and a reserve for review. Past ceilings and spend: VAC-002 pilot $120; P2 $150 ($57.50 spent); P3 $150 ($92.31 spent, hard stop $140); R-EXP-1 qualification $80; R-EXP-2 pilot $110. Confirmatory phases always require an explicit owner ceiling.
- Pricing: `CBE/research/pricing/anthropic.price-table.json` (`praxis.price-table/1`, version 2026-10-20.1). claude-opus-5-5: input $4, output $20, cache read $0.20, cache write 5m $5 and 1h $8 per MTok. The excerpt sha is pinned. An ARCH-001 copy is in `harness/pricing/`.
- Cost measure: cost per independently accepted requirement, from cli-estimate or transcript usage.
- Frozen acceptance criteria: A024 used 36/36 frozen criteria; R001 used `baseline/acceptance-plan.md` (AC-01–AC-14 plus ≥ 80% Verified), with errata appended, never edited.

## 10. Cross-system program document

- **No cross-system PROGRAM.md, roadmap or CURRENT-STATE for the Echelon toolchain exists** in any inspected repo.
- `CBE/docs/roadmap.md` is linked from the CBE README but does not exist and never existed in history.
- Per-repo documents exist:
  - `conditor/docs/roadmap.md` (Conditor slices);
  - `ordo/context/CURRENT-STATE.md` (2026-09-07, stale);
  - `conditor/` and `echelon-registry/context/CURRENT-STATE.md` (initialization placeholders);
  - `ordo/Notes/roadmap-to-review.md` (SDE v0.2, Sept).
- Nearest cross-system artifacts:
  - `CBE/research/coordination/FINAL-REPORT.md` and `manifest.json` (a prioritized backlog, 2026-10-20/21);
  - `RD/research/construction-by-design/echelon-foundry-program/{COORDINATION.md,SYNTHESIS-AND-RECOMMENDATION.md,optimization-backlog.md}`;
  - `RD/research/echelon-platform/EX-ECHELON-STACK-COMPATIBILITY-2026-001.md` (PROPOSED, NOT STARTED, 2026-10-23).

## Not found

- Any merged or main-branch "verified construction" requirement. They exist only in the open VC-001..004 PRs.
- CONSTRUCT-010 results; there are only smoke trial branches.
- An explicit Rehearsal 3 phase table, a named release set, or a formal approval record beyond the doc header and the owner commit.
- Dollar costs for R001 and R002; token usage for R002.
- The README-linked `docs/cohort-planner.md`, `research/experiment-plan.md` and `docs/roadmap.md`.
