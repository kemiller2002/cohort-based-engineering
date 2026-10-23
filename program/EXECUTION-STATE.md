# Execution state

**Updated:** 2026-10-23. **Coordinator:** a long-running agent session (Claude Code; branch
`claude/echelon-constraint-driven-program-mq2d6o` in every repository it touches).

A successor resumes from this file. A successor needs nothing else; each line points at the evidence.

## Phase

| Mission step | State |
|---|---|
| 1 Inspect and reconcile | **Done.** CURRENT-STATE.md; inspection evidence in `evidence/inspection-2026-10-23/`; 7 open intake PRs merged (§Merged) |
| 2 Shared authority and provenance contract | **Drafted.** CONTRACTS.md C1–C3, schemas and fixture in `contracts/`, all validated (`check_schema` and fixture validation pass) |
| 3 Smallest operational improvements | **In progress.** EP-00 (Praxis CI) is being fixed. A3, A2, A1, A5 and A6a are specified, with intake written or listed |
| 4 Verified-construction slice | **In progress.** B2 (Ordo) and B3 (Dokimos) prototypes are being built locally |
| 5 Praxis/Ordo/Dokimos integration | Not started (B4); needs B2 and B3 |
| 6 Authorized experiments | **None authorized.** Zero-cost phases of EXP-2 and EXP-3 are specified |
| 7 Promote on evidence | Nothing promoted |

## Merged by the coordinator (owner-approved: "approve all merges")

All are intake-only PRs. Each had CI red **only** from pre-existing runner drift that is also red on main
(CURRENT-STATE §1).

| PR | Merge commit |
|---|---|
| cohort-based-engineering#22 (VC-001) | `af2c7f4` |
| ordo#103 (VAC-002-P3-02) | `1b3ec62` |
| ordo#104 (VC-002) | `9addcbe` |
| dokimos#51 (VAC-002-P3-03) | `9e38a3b` |
| dokimos#52 (VC-004) | `6c8554e` |
| praxis#285 (VAC-002-P3-01 R-PRAX-1) | `914a2f1` |
| praxis#286 (VC-003) | `9704841` |

## Active work

| Item | Repository and path | State | Commits |
|---|---|---|---|
| Program documents and contracts | cohort-based-engineering `program/` | Committed locally | see `git log` on the branch; `63941ce` (contracts, pushed) |
| EP-00 Praxis CI green | praxis `src/`, `tests/` | Agent running | — |
| B2 Ordo slice | ordo `experiments/verified-construction/` | Agent running | — |
| B3 Dokimos slice | dokimos `experiments/rule-provenance/` | Agent running | — |
| EP-A6a intake | echelon-registry `.praxis/inbox/documents/2026-10-23-EP-A6a-…` | Committed locally | `854ba4c` |
| EXP-2 / EXP-3 intake | cohort-based-engineering `.praxis/inbox/documents/` | Committed locally | — |

## Blockers

| ID | Blocker | Effect | Needed |
|---|---|---|---|
| B-1 | After the seven PR merges, this session's auto-mode permission classifier denied `git fetch`, `git merge --ff-only` and `git rebase` ("Merge Without Review") | Local branches cannot pick up the merged intake commits or be pushed until permission is granted. Program work is committed locally only | The owner allows git fetch and push for this session (a Bash permission rule), or pushes the branches |
| B-2 | Praxis main red (git 2.55 golden test, timestamp flake) | `validate`, registry check and browser tests are skipped on main and on every PR | EP-00 (in progress) |
| B-3 | Dokimos site `validate` red (Playwright 1.56.1 on ubuntu-26.04) | Site checks skipped; Deploy site red | EP-01 plus OD-5 |
| B-4 | No paid experiment budget | EXP-1, the paid phase of EXP-3, and R-EXP-1/2 cannot run | OD-1 |

## Open decisions

| ID | Decision | Options | Recommendation | Owner |
|---|---|---|---|---|
| OD-1 | Experiment budgets | (a) authorize EXP-1 qualification $40 plus pilot $120, and EXP-3 phase 2 $60; (b) authorize zero-cost phases only; (c) none | (b) now. Decide (a) after B4 and EXP-3 phase 1 | kemiller2002 |
| OD-2 | Rehearsal 3 release set | (a) echelon-current 1.25.0 (Praxis 3.16.0, pre REL-GATE-003/004 fixes); (b) approve a newer set first, with Praxis ≥ 3.19.0 and Dokimos 0.7.0, via A6a | (a), unless (b) is approved and qualified **before** kickoff. Never mid-run | kemiller2002 |
| OD-3 | Adopt VAC-002-P3-02-R1: refuse-and-record is an authorized outcome | accept / reject | Accept. It is already implied by approved VAC-CBE-001-R2 and P2's gap rule. C1 and B2 assume it | finance and decision owners / kemiller2002 |
| OD-4 | Amend Rehearsal 3 to run live-provider tests at the first persistence checkpoint (A4) | amend / keep plan | Amend before kickoff only; R002 evidence supports it | kemiller2002 |
| OD-5 | Runner-image policy | (a) pin `runs-on` to a dated image and revisit; (b) always track the latest image and fix drift | (a) for release-gating jobs, (b) for everything else | kemiller2002 |
| OD-6 | Add the four-sentence authority contract to the Praxis brief (R-PRAX-1) | adopt as policy / wait for powered confirmation | Adopt as a statement of existing policy (+6% cost), labelled "not a demonstrated control" | kemiller2002 |
| OD-7 | Home of the C1 schema at 1.0 | Praxis `schemas/` / shared package | Praxis `schemas/` | kemiller2002 |
| OD-8 | Should Authority markers appear in Ordo-generated code? | yes / trace only | Trace only for generated code; markers for handwritten code | kemiller2002 |
| OD-9 | Pilot repository for verified completion (A3) | dokimos / ordo / praxis | dokimos: its completion-verification is already the verifier | kemiller2002 |

## Next executable actions (in order)

1. Resolve B-1, then push every local branch and open draft PRs:
   - cohort-based-engineering;
   - echelon-registry;
   - praxis (EP-00);
   - ordo (B2);
   - dokimos (B3).
2. Merge `origin/main` into each branch to pick up the intake merged today (merge, not rebase, on pushed branches).
3. When the agents report, record their commits and test results in **Active work**.
4. Write the remaining intake listed in IMPLEMENTATION-PLAN.md "Requirements ingestion record": praxis EP-A3, EP-A2b,
   EP-A1, EP-A5; dokimos EP-A2a, EP-01.
5. Run B4 (integration) and record the five fixture outcomes as PASS, FAIL or NOT_RUN.
6. Run EXP-3 phase 1 and EXP-2 phase 1 (zero cost) after preregistration commits.
7. EP-02 intake hygiene: triage the CBE inbox, clean up legacy Praxis intake, and claim the implemented inputs in
   Forma, Limen and Aegis.
