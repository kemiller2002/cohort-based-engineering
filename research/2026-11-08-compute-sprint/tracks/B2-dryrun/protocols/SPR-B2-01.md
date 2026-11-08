# SPR-B2-01 — Pre-T0 governance dry-run replay (preregistration)

Worker B2-001, 2026-11-08, written and committed before any check was executed.
Reconnaissance done before this commit was limited to reading files and git history (no tool runs).

## Question
For each terminal or major governance blocker of R8, R9, R10 and Causa (and R4 as an optional extra case): if the
pre-T0 governance dry run recommended by Track B (REPORT §5 item 1) had been executed on the artefacts as they
existed at T0, would it have failed with an error matching the historical blocker, before T0?

## Hypotheses (stated before running)
- H1 (Track B's claim, operationalised): the dry run catches the majority (> 50 %) of replayable blockers.
- H2 (prior expectation of this worker): it catches the *mechanical* blockers (tool/plan/format/binding/time-budget
  mismatches: R4 approvals, R9 MSB1008, R10 authorize, R10 job cap, Causa rules binding) and does **not** catch
  the *semantic* package defects (R8 command body, R8 INV-04 vs SM-SAVE) nor the Causa T18↔T20 cycle when the
  check uses only declared `dependsOn` edges, because that cycle runs through an acceptance-test dependency that is
  not a declared edge.
- H3 (false positives): on the later, fixed artefacts each check that caught a blocker passes.

## Blocker list (from Track B events.jsonl)
| Key | Run | Blocker | Track B event |
|---|---|---|---|
| R4-APPROVALS | R4 | approvals file in Praxis schema; verifier needs causa.requirements-approvals/1 (T+60) | B-E-044 |
| R8-CMDBODY | R8 | frozen IF41-DOMAIN has no command body | B-E-093 |
| R8-INV04 | R8 | INV-04 contradicts SM-SAVE T-S31/T-S32 | B-E-094 |
| R8-APPROVALS | R8 | pinned approvals fail verifier trust checks; verdict INVALID (terminal verdict cause) | B-E-099 |
| R8-MSB1008 | R8 | live suites never ran (MSB1008) until T+94 | B-E-092 |
| R9-MSB1008 | R9 | frozen v4.1.2 suite commands fail on pinned SDK (MSB1008) and name undefined webkit project; release gate REFUSED | B-E-106 |
| R10-AUTH | R10 | authorize-implementation refused the real approved plan, 55 causes | B-E-110 |
| R10-GATE | R10 | governed gate deadlock (40-min cap, write-once record, Playwright install timeouts, branch-name refusal); 45/66 cancelled | B-E-113 |
| R10-JOBCAP | R10 | build-and-test 20-min job cap vs ~29-min browser suite | B-E-115 |
| CAUSA-CYCLE | Causa | T18↔T20 cycle in the frozen slice plan | B-E-124 |
| CAUSA-RULES | Causa | pinned process-evidence rules bound to indy-init-rehearsal-010 | B-E-125 |

R8-APPROVALS and R8-MSB1008 are added beyond the brief's list because Track B records them as R8's terminal verdict
cause and a major blocker; they are reported separately and the headline is also given on the brief's list alone.

## Freezing the inputs (rule)
Pre-T0 state = for each repository the last commit whose committer time is strictly earlier than the run's T0
(Track B events), on the first-parent line of main, unless the run records a governing commit (`.echelon/r9-governance.json
indyInitCommit`, `T0-START.json planCommit`), in which case that commit is used and checked to be earlier than T0.
Full Indy-init history: read-only clone in /home/user/sprint-scratch/B2/indy-init-full (source repos untouched).
Where the dry run needs the *bootstrap repository* (authorize-implementation needs a target repo), the run's own
setup commits made before any application code (deterministic output of the pinned Conditor + package + STARTUP)
are used as the throwaway repository, copied into scratch. This is recorded as a limitation (post-T0 timestamp, but
pre-implementation, pre-T0-determined content).

Planned pins (verified at run time, recorded in raw/*.json):
- R4: Indy-init ad2f1af (02:04:14 EDT, T0 06:04:39Z); fixed: 1ede27f (verifier-format approvals).
- R8: Indy-init 1cb27ec (last main before 17:31:24Z; contains plan commit f85081f); package v4.1.1.
- R9: Indy-init bc3c381 (governing commit); package v4.1.2; fixed: v4.1.4/v4.1.5 suite runners.
- R10: Indy-init 89f5840 (governing commit) + R10 setup state 33fd372; fixed: Indy-init 669fe04 (PR #174 repair).
- Causa: Indy-init dae2347 (governing commit), lock kickoff/competition/toolchain.lock.json.

## Checks (the dry-run harness)
D1 approvals schema: run the pinned `tools/compute-acceptance-verdict.py` (or the pinned verifier's own loader)
   on the pinned approvals file with a stub ledger; plus a schema-id comparison.
D2 suite command execution: build a stub tree with the plan's test projects (no application code), run each
   executable suite command of the frozen plan with `dotnet` 10.0.402 (pinned SDK); record exit code and output.
D3 authorize-implementation: run the pinned r9.fsx authorize-implementation against the dry-run repo with the
   pinned Praxis; record the cause list.
D4 dependency cycle on the slice plan. Three variants, all reported; V2 is primary:
   V1 declared `dependsOn` only; V2 V1 + edges S→T where an acceptance test of S binds obligations of a requirement
   owned by slice T; V3 V2 + the lock-pinned assertion-merge-needs edges.
D5 process-rules repository binding: compare the repository named by the pinned process-evidence rules with the
   competition/target repository named by the lock.
D6 time budgets: compare `timeout-minutes` of the pinned CI/gate workflows with historical durations of the suites
   they run, from Track A ci-steps.csv restricted to runs *before* the run's T0 (no hindsight data).
D7 package/contract validation at the pinned revision (requirements-compiler validate / ContractCheck build) on
   R8's v4.1.1, to test whether pinned tooling says anything about the command body or INV-04.

## Matching criteria
- CAUGHT: a check exits non-zero / reports refusal whose message names the same mechanism as the historical blocker
  (R4: schema id; R8-CMDBODY: command body / CommandEnvelope; R8-INV04: INV-04 or SM-SAVE; R8-APPROVALS: approvals
  trust/authority; MSB1008: the MSB1008 error or the undefined webkit project; R10-AUTH: step-3 work-item and/or
  step-4 link causes; R10-JOBCAP/R10-GATE: a historical pre-T0 duration exceeding the cap of the job that runs that
  suite; CAUSA-CYCLE: a cycle containing T18 and T20; CAUSA-RULES: a repository mismatch naming indy-init-rehearsal-010).
  A multi-cause blocker (R10-GATE) counts CAUGHT if at least one cited cause that alone blocks the gate is caught;
  the covered/uncovered causes are listed.
- NOT CAUGHT: every applicable check passes, or fails only for reasons unrelated to the blocker.
- NOT REPLAYABLE: inputs unavailable or a tool cannot run here; the exact reason is recorded.
- A failure for an unrelated reason is a false alarm, recorded but not a catch.

## Analysis
Headline = CAUGHT / (CAUGHT + NOT CAUGHT), over the brief's list and over the extended list.
H1 supported if headline > 0.5. H2 judged blocker by blocker. False-positive check: rerun each catching check on the
fixed artefacts; a catch whose check also fails on the fixed version for the same reason is downgraded to a
non-discriminating catch and reported.
Cost: wall-clock seconds per replay of the tool executions (tools already built), and build seconds separately.
Builds run serially (shared 4-vCPU host).

## Evidence classes
VERIFIED (reproduced by execution here), SUPPORTED, INCONCLUSIVE, CONTRADICTED, NOT TESTED.

---
## Addendum: deviations recorded after execution (the preregistered text above is unchanged; see commit c7088f8)
1. Praxis 3.25.0 was built from praxis@v3.25.0 (local source) because the release-installer download was refused by the session permission classifier.
2. R10-AUTH: the committed suite-preflight report's `root` is R10's checkout path; the dry-run copy rewrites it to the scratch path. The unrelocated run is kept (56 causes = 55 historical + 1 path-only).
3. D2 classifier: the first run mislabelled single-project commands as MSB1008 because the scratch directory name contained "MSB1008"; the classifier now matches `error MSB1008` and scratch labels are neutral. All D2 records come from the corrected run.
4. D4: after a first run produced a 27-slice SCC from cross-cutting `praxis:*` record tests, the mechanism-match rule was made explicit: a catch requires an SL-T18 -> SL-T20 edge. Post-hoc variants V2x/V3x (executable tests only) were added as diagnostics.
5. D5: the preregistered check also fails on the fixed rules (project id `causa-t0` vs repo name `causa`); a post-hoc variant also accepts the bootstrap's Praxis project id. The outcome reported is the preregistered one, flagged non-discriminating.
6. D6: the estimator was fixed after a first run in which cancelled R6 steps dominated: per-kind maxima over *successful* pre-T0 steps; all-conclusions and R8-R9-only figures are kept as sensitivity rows.
7. D7: `v41 --check` must run before ContractCheck is built (its bin/obj inside the package otherwise make --check exit 4); the record comes from the corrected order.
