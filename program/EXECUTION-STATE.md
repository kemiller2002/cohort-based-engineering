# Execution state

**Updated:** 2026-10-23 (end of first coordination session).
**Coordinator:** a long-running agent session (Claude Code), working on branch
`claude/echelon-constraint-driven-program-mq2d6o` in every repository it touches.

A successor resumes from this file and needs nothing else. Every line points at its evidence.

## Phase

| Mission step | State |
|---|---|
| 1 Inspect and reconcile | **Done.** See CURRENT-STATE.md and `evidence/inspection-2026-10-23/`. The 7 open intake PRs are merged and reconciled (CURRENT-STATE §4) |
| 2 Shared authority/provenance contract | **Drafted and exercised.** CONTRACTS.md C1–C3; schemas validated; B4 composes them across Ordo and Dokimos |
| 3 Smallest operational improvements | **EP-00 and EP-01 done:** CI is green on Praxis and Dokimos main again. Intake for A3, A2a, A2b, A1, A5 and A6a is merged into each owner's inbox |
| 4 Verified-construction slice | **Prototypes implemented and tested locally:** B2 (ordo#105, 69/69) and B3 (dokimos#53, 59/59). Both are experimental |
| 5 Praxis/Ordo/Dokimos integration | **B4 run.** Five frozen outcomes PASS; the Praxis completion step is NOT_RUN (`integration/b4/B4-RESULT.md`) |
| 6 Authorized experiments | **No paid runs.** EXP-3 phase 1 ($0) ran: **H1 contradicted** (recall 38.5%, false-question rate 90.5%), so phase 2 does not qualify. EXP-2 phase 1 ($0) ran: **H1 contradicted** for both policies (selection saves 23.9% with 1 environmental escape; checkpoint CI saves 8.6% with 2 real escapes); A1 stays shadow-only |
| 7 Promote on evidence | Nothing promoted; nothing meets EXPERIMENTS.md §6 yet |

## Pull requests

**Merged by the coordinator** (owner instruction: "approve all merges"). All intake-only. Their CI was red only from
the pre-existing runner drift that is also red on main.

| PR | Merge commit |
|---|---|
| cohort-based-engineering#22 (VC-001) | `af2c7f4` |
| ordo#103 (VAC-002-P3-02) | `1b3ec62` |
| ordo#104 (VC-002) | `9addcbe` |
| dokimos#51 (VAC-002-P3-03) | `9e38a3b` |
| dokimos#52 (VC-004) | `6c8554e` |
| praxis#285 (VAC-002-P3-01) | `914a2f1` |
| praxis#286 (VC-003) | `9704841` |

**Opened and merged by the coordinator:**

| PR | Merge commit |
|---|---|
| ordo#105 (B2 slice) | `d31290c` |
| echelon-registry#90 (EP-A6a intake) | `50c82e4` |
| dokimos#53 (B3 slice, EP-01, EP-A2a/EP-01 intake) | `5988bf0` |
| praxis#287 (EP-00, wave A intake) | `638b2e7` |
| ordo#106 (VC-002 and VAC-002-P3-02 intake completed) | `2df928a` |
| dokimos#54 (audit v2, experimental) | `fc9b31f` |
| echelon-registry#91 (Praxis 3.20.0 registered, not selected) | `83d81ed` |
| conditor#107 (qualify Praxis 3.20.0; released Conditor 0.10.9 from `620f951c`) | `d7e95e6` |
| echelon-registry#92 (echelon-current 1.26.0, owner-approved; Conditor 0.10.9 record) | `3cb34b9` |
| cohort-based-engineering#23 (this record) | merged with this update |

**Open:**
- (praxis#288 merged `24841bb`: CI runs 2363 tests with 0 SKIP, real Dokimos 0.7.0 cases and CLI idempotence contract tests pass. A3 now waits only on R1 (release) and R4 (OD-9 pilot enablement).)
- cohort-based-engineering#23: the living program record, merged when the owner wants a snapshot on main.

**Opened earlier** (the table below is the state at opening; see the merges above):

| PR | Content | Head | Verification |
|---|---|---|---|
| cohort-based-engineering#23 | `program/` (this record), contracts, fixture, B4 evidence, EXP-2/EXP-3 intake | branch head | Schemas and fixture validated; no CI in this repository |
| praxis#287 | EP-00 CI fix (`e9cbfa3f`) plus wave A intake (`9e9e1e6a`) | `9e9e1e6a` | 2358/2358 locally; CI on ubuntu-26.04 pending |
| ordo#105 | B2 slice (`c67afdf`, `aec6a5f`, `7fbc0f8`, `03b0d30`) | `03b0d30` | 69/69 locally, re-run by the coordinator; CI green on `885ae28` |
| dokimos#53 | B3 slice (`9a7ad07`, `2b6537b`, `de1a210`, `8d2849e`) plus EP-A2a and EP-01 intake (`91fd1a2`) | `91fd1a2` | 59/59 locally, re-run by the coordinator |
| echelon-registry#90 | EP-A6a intake (`854ba4c`) | `854ba4c` | CI green |

## Blockers

| ID | Blocker | Effect | Needed |
|---|---|---|---|
| B-1 | ~~The auto-mode classifier denied git fetch/merge after the PR merges~~ | **Cleared** the same session: fetch, merge and push work again | — |
| B-2 | ~~Praxis main red (runner drift)~~ | **Cleared:** praxis#287 merged (`638b2e7`); `validate` green on ubuntu-26.04 | — |
| B-3 | ~~Dokimos site `validate` red~~ | **Cleared:** Playwright upgraded to 1.63.0 in dokimos#53 (`a4fa237`, merged `5988bf0`). OD-5 still open as a policy question | — |
| B-4 | No paid experiment budget | EXP-1, EXP-3 phase 2, R-EXP-1/2 cannot run | OD-1 |
| B-5 | Only the .NET 10 runtime is in this container | Ordo's net8.0 suites ran with `DOTNET_ROLL_FORWARD=Major`; the experiments target net10.0 | Install the net8.0 runtime if net8.0 verification is required locally (CI covers net8.0) |

## Decisions (all decided 2026-10-24)

The owner accepted every recommendation below on 2026-10-24. What each decision set in motion is recorded under **Decision follow-through**.

| ID | Decision | Options | Recommendation | Owner |
|---|---|---|---|---|
| OD-1 | Experiment budgets | (a) authorize EXP-1 qualification $40 plus pilot $120, and EXP-3 phase 2 $60; (b) zero-cost phases only; (c) none | (b) now; decide (a) after EXP-3 phase 1 | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-2 | Rehearsal 3 release set | (a) echelon-current 1.25.0 (Praxis 3.16.0); (b) approve a newer set first via A6a | (a), unless (b) is approved and qualified **before** kickoff | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-3 | Adopt VAC-002-P3-02-R1 (refuse-and-record is an authorized outcome) | accept / reject | Accept; C1 and B2 assume it | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-4 | Amend Rehearsal 3 so live-provider tests run at the first persistence checkpoint | amend / keep | Amend, but only before kickoff | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-5 | Runner-image policy | pin release-gating jobs / always latest | Pin release-gating jobs to a dated image; the rest track latest | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-6 | Four-sentence authority contract in the Praxis brief (R-PRAX-1) | adopt as policy / wait | Adopt, labelled "not a demonstrated control" | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-7 | Home of the C1 schema at 1.0 | Praxis `schemas/` / shared package | Praxis `schemas/` | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-8 | Authority markers in Ordo-generated code? | yes / trace only | Trace only. B4 confirms generated code cannot reach handwritten question mappings | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-9 | Pilot repository for verified completion | dokimos / ordo / praxis | dokimos | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-11 | Use audit v2 owner questions for non-blocking human triage of legacy rules (VAC-002-P3-03-R1)? | yes, non-blocking / wait for v3 | Wait. The held-out false-question rate (25%) would spend owners' attention on about 1 false question in 4 | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |
| OD-10 | B2 interpretation choices: unlisted pairs refused; PartiallyPaid derived from REQ-INV-002; refusal-code names | confirm / change | Confirm. The fixture is synthetic, and these are presentation and interpretation choices recorded in ordo#105 | **Decided 2026-10-24:** recommendation accepted (kemiller2002: "do what you recommend") |

## Decision follow-through

| Decision | Action | State |
|---|---|---|
| OD-1 | Zero-cost experiment phases only; no paid run is authorized | In force |
| OD-2 | Rehearsal 3 uses Registry echelon-current 1.25.0, unless a newer set is approved and qualified before kickoff | **Superseded by the newer set, before kickoff:** the owner approved echelon-current **1.26.0** (Praxis 3.20.0) on 2026-10-24 (kemiller2002: "I approve all"). It is qualified by released Conditor 0.10.9 (REG-RU-007 green) and merged as echelon-registry#92 (`3cb34b9`). Rehearsal 3 has not kicked off, so under DEP-CURRENT-002/006 it freezes on 1.26.0 at kickoff. The Conditor `indy-init` preset already pins Praxis 3.20.0 (conditor#107, `d7e95e6`) |
| OD-3 | Refuse-and-record is an authorized outcome; written into `docs/operating-model.md` §5 | Done |
| OD-4 | Amend Rehearsal 3 so live-provider tests run at the first persistence/authorization checkpoint; amendment goes to Indy-init | **Done:** indy-init#11 (`fc5df1c`), R3-DV-017 |
| OD-5 | Pin release-gating jobs to an explicit runner image; other jobs track latest | **Done:** dokimos#55 (`003204d`), praxis#290 (`1ee496b`). The pinned `ubuntu-26.04` release jobs ran green on #290 |
| OD-6 | Add the four-sentence authority contract to the Praxis implementation brief, labelled policy, with its version in telemetry | **Done:** praxis#290 (`1ee496b`): AGENTS.md `## Authority`, construction handoff brief, `authorityContract` on every execution record. Ships in the next release |
| OD-7, OD-8, OD-10, OD-11 | Recorded; no code change (C1 at 1.0 goes to Praxis `schemas/`; trace only for generated code; B2 interpretations confirmed; audit v2 not used for triage yet) | Done |
| OD-9 | The verified-completion pilot is Dokimos. It needs a Praxis release with `work finish` **and** a Registry-approved set that includes it | **Release and approval done:** Praxis v3.20.0 (`ee6430af`); Conditor 0.10.9 qualifies it (conditor#107, released from `620f951c`); echelon-current 1.26.0 selects it (echelon-registry#92, `3cb34b9`), owner-approved 2026-10-24. **Pilot not enabled yet.** Praxis `docs/verified-completion-rollout.md` gates enablement on seven conditions. Their state for Dokimos: (1) F1, (2) F2 and (3) F3 have test evidence in Praxis and Dokimos, but REL-001 experiment C has not been re-run on the 3.20.0 binaries; (4) REL-001 A–C on released 3.20.0: not run; (5) representative application: the pilot itself would supply it; (6) run-02 reviewed: the report exists (`research/experiments/REL-001/`), and its recommendation must be quoted in the enabling change; (7) trust root: **owner action**, below. **Owner action:** generate a P-256 verifier key on your own machine and store it as an Actions secret in a Dokimos environment restricted to `main`. Send only the public `keyId`. The coordinator then adds the CI `verifier run` workflow and the `ros.json` pin (`requireVerifiedCompletion` and `trustedVerifierKeyIds`) in one reviewed change. The coordinator never holds the key |

## Next executable actions (in order)

1. **praxis#287:** watch CI. When green, mark it ready and merge (owner-approved), which clears B-2. If it is red,
   root-cause it (see AGENTS.md drive-to-green).
2. **Mark the other PRs ready** once green: ordo#105 and dokimos#53 (experimental, outside default paths),
   echelon-registry#90 and cohort-based-engineering#23. Merging an experimental prototype is not promotion
   (EXPERIMENTS.md §6).
3. **Done this session:** B3 v2 merged (dokimos#54); held-out confirmation **contradicted** (recall 80%, false questions
   25%); see EXPERIMENTS.md §4. Any v3 needs a new independent held-out set. The paragraph below is kept as the
   original plan.
   **Typed audit (B3 v2), original plan:** implemented in Dokimos with FSharp.Compiler.Service. It must find:
   - numeric constants of any type;
   - union-case and named-type comparisons;
   - conditions spread over several lines;
   - values matched to accepted decisions' parameters, instead of a question per unmarked line.

   Develop it against the P3 development set only. Then preregister a confirmation on a **held-out** corpus.
   EXP-3 phase 1 showed the lexical audit misses every exemption (`research/experiments/EXP-3/RESULTS.md`).
4. **EP-04 (decided 2026-10-24, owner approved the recommendation):** use GitHub's built-in secret scanning with push protection. It is a repository setting; the coordinator has no tool to change it, so the owner enables it per repository (Settings → Code security). No workflow job is added. Earlier text, kept: add secret-scan jobs; EXP-2 found none in either repository. Also propose splitting Praxis's
   mandatory `validate` steps from the full F# suite, so selection can save more (EXP-2 exploratory estimate:
   29.7%).
5. **EP-02 intake hygiene:**
   - triage the CBE inbox: reject ENGINEERING-RELIABILITY-001 as a duplicate; forward VAC-002-01, -02 and -04;
   - Praxis legacy `input-documents/`: update the README; claim and reject `rfa.md`; claim the ROS-ORDO file;
   - claim the implemented inputs in Forma, Limen and Aegis.
6. **EP-01:** fix Dokimos site validation after OD-5.
7. **A3:** after praxis#287 merges, implement EP-A3-R2/R3 (real-Dokimos CI path, idempotence contract tests). One
   Praxis agent at a time: DEPENDENCIES.md lane L1.
8. **A2a in Dokimos:** promote the slice's validity block and `isReusable` into the released result formats. Then A2b
   in Praxis, then A1 in shadow mode.

## Consolidation session 2026-10-24

Read-only evidence consolidation; no production code changed, no paid runs. Outputs in
`research/consolidation/2026-10-24/` (start with `agent-handoff.md`). New intake, one file each, in
`.praxis/inbox/documents/` of praxis (REQ-PRES-001, R3-PRX-001), echelon-registry (REG-PAIR-001), conditor (SD-1-REL;
creates the canonical intake directory), limen (LIM-HTTP-001) and dokimos (DOK-SDK-001). Delivery of each commit is
recorded in the session's final summary and in the commit messages on branch `claude/engineering-consolidation-2026-10-24`.

| Repository | Commit | Delivery |
|---|---|---|
| cohort-based-engineering | `2957cc2` | fast-forwarded to main (owner: "I approve all merges") |
| praxis | `bf7bf04` | fast-forwarded to main |
| dokimos | `bf6a62b` | fast-forwarded to main |
| echelon-registry | `f14994f` | fast-forwarded to main |
| conditor | `ce40e51` | fast-forwarded to main |
| limen | `c586461` | **branch only** (`claude/engineering-consolidation-2026-10-24`). Not merged: Limen's `validate` rejects changes without a ROS work item and scope manifest. Merge through a work item |

No pull requests were opened: the session's `gh` token was invalid, so merges were direct fast-forwards. CI on those
main commits was not observed from this session.
