# Track B2 — Pre-T0 governance dry-run replay (SPR-B2-01)

> Committed by RD-000 from B2-001's final hand-back text. The harness refuses subagent report-file writes (D-010).
> - Worker final commit: `550c1a6`.
> - Preregistration commit: `c7088f8`, made before any check ran.
> - Outputs:
>   - `protocols/SPR-B2-01.md`, including a deviations addendum
>   - `harness/`: Python, functional style; 14 unittest tests passing
>   - `raw/`: 11 replay JSON files plus `full-rerun-timing.txt`
>   - `results.csv`, `experiments.json`, `findings.json` (11 findings), `CHECKPOINT.md`

## 1. Headline

| List | CAUGHT / replayable | Rate |
|---|---|---|
| Brief's list (R8 ×2, R9, R10 ×3, Causa ×2) | **4 / 8** | **0.50** |
| Brief's list + R4 | 5 / 9 | 0.56 |
| Extended (adds R8 approvals, R8 MSB1008) | 7 / 11 | 0.64 |

No blocker was NOT REPLAYABLE overall. Within R10-GATE, only the time-budget cause could be replayed.

Two of the brief-list catches are weak:
- **CAUSA-RULES:** the preregistered check also fails on the fixed rules, so it does not discriminate.
- **R10-JOBCAP:** caught under only one of three duration estimators.

Excluding those two, the robust, discriminating catch rate is **2 / 8** on the brief's list (R9-MSB1008, R10-AUTH) and **5 / 11** on the extended list.

Hypotheses:
- **H1** (more than half caught): not supported on the brief's list (0.50 does not exceed 0.5); supported on the extended list.
- **H2** (mechanical defects caught; semantic defects and the cycle not caught): supported.
- **H3** (fixed versions pass): holds for every catching check except the preregistered rules-binding check.

## 2. Per-blocker results

"Pre-T0 commit" is the Indy-init revision unless stated otherwise.

| Blocker | Pre-T0 commit | Outcome | Evidence | Status |
|---|---|---|---|---|
| R4 approvals schema | ad2f1af (06:04:14Z; T0 06:04:39Z) | **CAUGHT** | Pinned `compute-acceptance-verdict.py` with a stub ledger reports "trusted approvals file has unsupported schema". The fixed file at 1ede27f reports 0 approvals problems | VERIFIED |
| R8 command body | 1cb27ec (last main commit before T0; contains plan f85081f) | **NOT CAUGHT** | `requirements-compiler v41 --check` on v4.1.1 passes X01–X20 (exit 0); ContractCheck exits 0; nothing mentions CommandEnvelope | VERIFIED |
| R8 INV-04 vs SM-SAVE | 1cb27ec | **NOT CAUGHT** | All pass. The 4-reads-per-60s cap is already in the frozen INV-04, so the contradiction existed before T0, but surfacing it needs semantic analysis | VERIFIED |
| R8 approvals (terminal INVALID cause) | 1cb27ec | **CAUGHT** | Verifier reports "lacks an immutable authority source" and "invalid change identity". The fixed file at 81b5461 reports 0 problems | VERIFIED |
| R8 MSB1008 | 1cb27ec; tree is the R8 bootstrap 616ec62 | **CAUGHT** | `error MSB1008` on SU-OWN-DOTNET and SU-DOTNET-LIVE; `Project(s) "webkit" not found` | VERIFIED |
| R9 MSB1008 + webkit | bc3c381; tree is the R9 bootstrap 8001e7c | **CAUGHT** | Same three suite failures on SDK 10.0.402. The v4.1.5 plan on the R10 bootstrap shows neither | VERIFIED |
| R10 authorize-implementation | 89f5840; target R10@33fd372 (setup only, no app code) | **CAUGHT** | Exit 4 with 55 causes (37 at step 3, 18 at step 4), identical line for line to the historical log. The repaired r9.fsx at 669fe04 passes (37 items, 890 obligations) | VERIFIED |
| R10 20-min job cap | Bootstrap workflow 314cc8c compared with pre-T0 run history | **CAUGHT (fragile)** | Maximum successful step duration across R2–R9 is 25.7 min, over the 20-min cap. R8–R9 alone gives 18.6; all conclusions give 49.5 | INCONCLUSIVE |
| R10 gate deadlock | 314cc8c | **NOT CAUGHT** | Pre-T0 estimate is 13.3 min, under the 40-min cap. Write-once record, install timeouts, branch-name refusal and cancellations need hosted Actions and were not replayed | SUPPORTED |
| Causa T18↔T20 cycle | dae2347 | **NOT CAUGHT** | See note below | SUPPORTED |
| Causa rules binding | dae2347 | **CAUGHT (non-discriminating)** | Rules require `indy-init-rehearsal-010`, but the lock names `causa`. The fixed rules (8d63637) bind `causa-t0`, the Praxis project id, so the preregistered check fails on them too. A post-hoc variant that also accepts the bootstrap's `ros.json` project id discriminates correctly | VERIFIED |

**Causa T18↔T20 cycle:** no variant contains a T18→T20 edge, and the declared `dependsOn` graph is acyclic. INV-21.spec.js, which needs T20's Connect, was written at T+94 (causa 1a1c7eb), so that dependency is not in any pre-T0 artifact. Separately, test-owner and assertion-needs edges form a cluster of 27–30 slices from cross-cutting `praxis:*` tests. This is an unrelated alarm.

**Extra catch, not counted in the rate:** the dry run also surfaces the FSharp.Core assembly skip ("could not find dependent assembly FSharp.Core 10.1.0") on the R8, R9 and R10 bootstraps. This is the defect behind R8 DEV-R8-04 and R10 SL-T11.

## 3. Cost

Measured on a shared host under load average 11–20.

| Item | Time |
|---|---|
| Tool time, R4 | 0.1 s |
| Tool time, R8 (includes compiling bootstrap stub projects) | 45 s |
| Tool time, R9 (includes compiling bootstrap stub projects) | 39 s |
| Tool time, R10 | 6 s |
| Tool time, Causa | 0.02 s |
| Build: requirements-compiler + ContractCheck | 28 s |
| Build: Praxis 3.25.0 CLI | 152 s |
| Clean end-to-end rerun of all 11 replays, including fixed-version controls | ≈199 s wall-clock; every outcome reproduced |

## 4. Implication for Track B's recommendation

A pre-T0 dry run is cheap: under a minute per rehearsal once the tools are built.

On the real artifacts it would have caught all the format, tool and plan mismatches:
- approvals schema
- MSB1008 and the undefined webkit project
- the 55-cause authorize-implementation refusal
- the FSharp.Core skip

It would not have caught:
- semantic package defects (R8 command body; INV-04 vs SM-SAVE)
- the Causa cycle, whose dependency only appeared in a spec written during the run
- most of R10's gate deadlock, which needs hosted CI

Two parts need specific design:
- The rules-binding check must compare against the Praxis project id the bootstrap writes, not the GitHub repository name.
- Time budgets cannot come from stub runs, because those select zero tests, and historical data predicted them only weakly.

"Every terminal blocker from R8 on was machinery first exercised inside the timed run" holds. But a dry run of that machinery covers only about half of those blockers.

## 5. Limitations and deviations

All of these are recorded in the protocol addendum.

- **Dry-run repositories.** Each replay uses the run's own T0 bootstrap or setup commit, timestamped 2–10 minutes after T0. These commits contain no app code and are determined by pre-T0 inputs. Fresh repositories were not bootstrapped before T0.
- **Praxis source.** Praxis was built from local source (praxis@v3.25.0) because the session's permission classifier refused the release-installer download.
- **R10-AUTH relocation.** The committed suite-preflight report names R10's checkout path; that field was rewritten to the scratch path. The unrelocated run is kept and yields one extra, path-only cause.
- **Post-hoc rules.** These were settled after the first runs, and each is flagged in the raw records and findings:
  - the cycle mechanism-match rule
  - the duration estimator
  - the project-id binding variant
- **Corrected bugs.** Every committed record comes from the corrected runs.
  - The suite classifier first mislabelled runs because the scratch path contained the token "MSB1008".
  - The `v41 --check` ordering was initially wrong.
- **Not attempted.**
  - A purpose-built model check of SM-SAVE against INV-04
  - A hosted-CI replay of the R10 gate
- **Source access.** Sources were read-only: git archive or local clone. A full read-only clone of Indy-init is at `/home/user/sprint-scratch/B2/indy-init-full`.

## Reproduce

```
cd harness
python3 -m dryrun.main causa approvals r10 suites r8sem
python3 -m dryrun.summarize
python3 -m unittest discover -s tests
```

Scratch prerequisites are listed in `experiments.json` under `reproduction`.
