# V1-001 independent verification report (compute-utilization sprint, 2026-11-08)

> Committed by RD-000 from V1-001's final hand-back text. The harness refuses subagent report-file writes (D-010).
>
> - **Worker final commit:** `6408b8f`.
> - **Outputs:** `verdicts.json` (10 entries); `scripts/` (own functional code; tests run with `python3 -I scripts/tests/test_v1lib.py` and `python3 -I scripts/tests/test_analyze.py`, both passing); `data/` (recomputation outputs and about 10 MB of raw Actions API samples); `CHECKPOINT.md` (reproduction commands).
> - **Independence:** no other track's scripts or derived numbers were used as inputs. Track A's data was opened only to compare results afterwards.

## Summary

| Claim | Verdict | Claimed | Recomputed | Independence |
|---|---|---|---|---|
| A-F-01 | **VERIFIED** | R8 533,823,102 tokens; $193.74; R3 $36.01 | 533,823,102; $193.7366; R3 $36.0064 | Full |
| A-F-03 | **VERIFIED** | Coordinator 44% of tokens / 32% of cost; mean context 416,786 vs 116,721 | 44.24% / 31.53%; 416,786.09 vs 116,721.03 | Full |
| A-F-07 | **PARTIALLY VERIFIED** | All 26 conflicts `.ros/`-only; no application-code conflicts | 26 PR-merge conflicts all `.ros/`, confirmed. But 4 branch-side merges conflicted in 6 application, test or CI files | Full |
| A-F-08 | **PARTIALLY VERIFIED** | 2.15 of 6 lanes (36%), peak 5 | 2.15/5 holds only on a 350-minute window counting agents. To merge freeze (T+379): 2.01 (33.6%). Peak distinct lanes 4. Praxis spans: 1.57 (26%) | Full |
| A-F-12 | **VERIFIED** | 67% of 15,568 job-minutes red | 65.6% (95% CI 56.5–71.9%) of about 13,722 (CI 11,225–16,401) | Sample |
| A-F-13 | **PARTIALLY VERIFIED** | 688 min, 8.4% of step time | Rebuild from source confirmed; about 607 min (CI 580–632), about 7.4–8.0% | Sample + workflow YAML |
| A-F-11 | **VERIFIED** | Median queue 3 s; R6 7,612 queued min | Median 3.0 s in all 9 repos including R6; R6 about 8,093 min (CI 3,500–13,629) | Sample |
| G-F-07 | **VERIFIED** | Praxis 3.25.0 says mandatory verified completion is not enabled | Statement present at praxis@12bf995; 0 of 90 `ros.json` files enable it | Full |
| G-F-08 | **VERIFIED** | Every arm 39/39; $0.1555 vs $0.1147 (+35.5%) | 39/39 in all 4 arms; $0.1555 vs $0.1147; +35.54% | Partial |
| G-F-10 | **VERIFIED** | Site claims 40%+ / 80% with no evidence packet | Claims present in the repo and on the live site; no supporting evidence found | Full |

None are CONTRADICTED. Two Track A statements inside the partially verified claims are wrong:
- **A-F-07:** "no application-code conflicts occurred in this rehearsal" is false.
- **A-F-13:** "688 min for the Praxis verifier" includes a step that does not build the verifier.

## Details

### A-F-01: R8 tokens and cost (VERIFIED, fully independent)
- **Method:** my own parser over `indy-init-rehearsal-008@fd8fba9/.ros/telemetry/executions/*.json`.
- **Records:** 56 in total. 48 carry `tokens.*`; 8 carry none (T10, CR2, CRT16, CRT23, CRT28, PAGES, CICOUNTS, CILIVE).
- **Buckets:**

  | Bucket | Tokens |
  |---|---|
  | Input | 6,445 |
  | Output | 2,151,093 |
  | Cache read | 523,097,086 |
  | Cache write | 8,568,478 |
  | **Total** | **533,823,102** |

- **Cross-check:** all 3,100 requestLedger rows across the 48 ledgers sum with 0 bucket mismatches.
- **Cost:** with `cohort-based-engineering/research/pricing/anthropic.price-table.json` (tableVersion 2026-10-20.1) and the 5m/1h cache-write split, $193.7366. Pricing request by request gives the same figure.
- **R3:** the `evidence/telemetry/tokens-final.json` timed bucket, with all cache writes priced at 5m, gives $36.0064.
- **Discrepancies:**
  - A's README says 49 ledgers; there are 48. Totals are unaffected.
  - Pricing every cache write at 5m gives $190.51.
  - The total is a lower bound: coordinator turns after its 23:50:44Z ingest are missing.

### A-F-03: coordinator share (VERIFIED, fully independent)
- **WI-R8-COORD:** 236,176,431 tokens (44.24%) and $61.09 of $193.74 (31.53%).
- **Requests:** 566 coordinator vs 2,534 task-agent.

| Measure | Coordinator | Task agents |
|---|---|---|
| Mean context per request (input + cache read + cache write) | 416,786 | 116,721 |
| Peak context | 897,198 | — |
| Cost per request | $0.108 | $0.052 |

### A-F-07: R8 merge conflicts (PARTIALLY VERIFIED, fully independent)
- **Method:** `git merge-tree --write-tree` on all 86 two-parent merge commits, in a fresh scratch clone.
- **Confirmed:** exactly 26 of the 49 PR merges conflict on replay. They are the same 26 PRs listed in `merges.jsonl`, each conflicting only in `.ros/context/current.json` and/or `.ros/events/events.jsonl`.
- **Not confirmed:** 60 of the 86 merge commits conflict overall. Four "Merge origin/main into r8/…" merges conflicted in non-state files:

  | Branch (PR) | Conflicted files |
  |---|---|
  | cr-t22b (#36) | `src/Causa.App/Program.fs` |
  | t21 (#19) | `.github/workflows/live.yml` |
  | t15 (#12) | `tests/Causa.Invariants/Negative/INV22.fs` |
  | t19 (#10) | `src/Causa.Persistence/Classify.fs`, `GitHubRequests.fs`, `tests/Causa.TestSupport/StatefulFake.fs` |

- **Corroboration:** git's own `# Conflicts:` blocks list the same 6 paths, and `git show --cc` shows real hand resolutions.
- **Why the log differs:** `merges.jsonl` records only the coordinator's PR-merge step.
- **Rates:** 53% of PR merges conflicted (26/49), vs 70% of all merge commits (60/86).

### A-F-08: lane utilisation (PARTIALLY VERIFIED, fully independent)
- **Reproduces:** 47 transcript spans sampled at 350 one-minute points give a mean of 2.151 and a peak of 5 (35.9%).
- **Window:** those 350 samples end at 23:21:24Z, but merge freeze was 23:50:28Z (T+379; `SCHEDULE-ACTUALS.md:54`). Through freeze the mean is 2.01 (33.6%).
- **Agents vs lanes:** the peak of 5 counts agents; two agents shared one lane. Peak distinct lanes is 4, and mean distinct lanes is 2.11 (350 samples) or 1.97 (379 samples).
- **Idle time:** 41 zero-activity minutes, not 34.
- **Praxis spans:** mean 1.57 (26%), peak 4.
- **Plausible range:** 1.6–2.15 lanes, 26–36% utilisation.

### A-F-12: red CI minutes (VERIFIED, sample)
- **Fetch:** own read-only Actions API fetch (curl GET through the session proxy; the gh token was invalid). All runs created in [T0, T0+420) were listed.
- **Sampling:** stratified random sample, seed 20261108, 100 runs per repo (a census for R7 and R9). Jobs fetched with `filter=all`. 2,000 bootstrap resamples.
- **Result:** 65.6% red (CI 56.5–71.9%). A replicate draw of 40 per repo gives 58.2% (CI 42–70%).

| Repo | V1 | Claimed |
|---|---|---|
| R2 | 22.0% | 22% |
| R3 | 19.4% | 17% |
| R4 | 46.5% | 48% |
| R5 | 39.8% | 45% |
| R6 | 81.2% | 85% |
| R7 (census) | 58.7% | 59% |
| R8 | 30.0% | 25% |
| R9 (census) | 28.0% | 28% |
| R10 | 89.2% | 88% |
| Excluding R6 and R10 | 36.8% | 38% |

- **Window definition:** every T0 matches the documented start, and in-window run counts equal Track A's exactly. But a fixed T0+420 window does not match each run's actual activity:
  - R2 ran to T+721, with 87 runs in the 17 h after the window.
  - R3's timed phase ended at T+127, and it had 35 preflight runs before T0.
  - R4 had 249 runs after the window.
  - R5's T0 was defined after the fact.
- **Sensitivity to definitions:**

  | Definition | Red share |
  |---|---|
  | Rounded-up job-minutes, attributed by run conclusion | 65.6% |
  | Unrounded seconds | 76.4% |
  | Only jobs that themselves failed | 54.3% |

### A-F-13: Praxis verifier rebuild (PARTIALLY VERIFIED)
- **Confirmed:** R2–R6 and R8–R10 call `kemiller2002/praxis/.github/workflows/foundations-verify.yml` (aa7c7ca; R6 at 398af6d). It checks out the pinned Praxis and runs `dotnet build` without a cache. The build step ran in 197 of 197 sampled foundations runs.
- **Estimate:** about 1 minute × 594 foundations runs, giving 607 min (CI 580–632; replicate 618), about 7.4–8.0% of step time.
- **Source of the error:** Track A's 688 = 604.0 min of "Build pinned Praxis verifier" + 84.5 min of R5's "Build the candidate and the plan verifier". The second step builds the application and Indy-init's requirements compiler, not Praxis.
- **Caveats:**
  - "Every run" means every foundations run, which is about 27% of in-window runs.
  - R6 has a fingerprint cache gate, but it never skipped in the sample.
  - R7 builds Praxis in `praxis-autonomy.yml` (about 33 min) under a step name the claim does not count.

### A-F-11: runner queue (VERIFIED, sample)
- **Median:** 3.0 s in all 9 repos, including R6.
- **R6 tail:** p90 1,189 s; about 8,093 queued minutes (CI 3,500–13,629; replicate 7,352).
- **Others:** 3–95 queued minutes. R10's p90 is 49 s (claimed 31).

### G-F-07: verified completion not enabled (VERIFIED, fully independent)
- **Statement:** `docs/verified-completion-rollout.md:3` at praxis@12bf995, last edited 2026-10-21 and carried into 3.25.0.
- **Default:** `RequireVerifiedCompletion = false`.
- **Scan:** 90 `ros.json` files, none enabling it (`data/g-f-07-config-scan.tsv`). Coverage is limited to repos checked out here, at HEAD.

### G-F-08: REL-001 run-02 (VERIFIED, partial recomputation)
- **Method:** each trial's token buckets priced from 93 observation files. With pilot and U6 trials excluded, that is 80 confirmatory trials, 20 per arm.
- **Correctness:** every arm 39/39, by oracle-scored units.
- **Cost per correct requirement:**

  | Arm | Cost |
  |---|---|
  | Bare | $0.1147 |
  | Directives | $0.1390 |
  | Original Echelon | $0.1520 |
  | Optimized Echelon | $0.1555 |

  Optimized vs bare: **+35.54%**.
- **Why partial:** raw transcripts were not available and the oracle was not re-run.
- **Caveats:**
  - Output tokens are a transcript lower bound (about 22 per request) in all trials, so output is only 1.3–1.7% of computed cost. True costs are higher, and the gap could move if true output differs by arm. This is disclosed at report line 237 but not in the headline.
  - 39/39 is a ceiling, so the experiment cannot show a quality difference.

### G-F-10: site claims (VERIFIED, fully independent)
- **Present in the repo** at echelon-foundry@8c6b453:
  - `src/pages/index.html:14` "40%+ throughput gains"; `:15` "Hours to minutes";
  - `src/data/case-studies.json:41` (published) "Reconciliation times reduced 80%";
  - `about.html:16` "exceeding 40%".
- **Present on the live site:** echelonfoundry.com served all three strings today.
- **No evidence found:** `research/evidence` is empty, and the strings appear nowhere else except copies under `ext/forma` and sprint files.
- **Internal inconsistency:** the organizational-throughput case study itself says "deployment frequency doubled; unplanned work reduced 50%".
- **Scope:** these are consulting-engagement claims about unnamed clients. Client records may exist outside these repos.

## Process notes
- **Stray fetch:** one `git fetch` was run by mistake in the read-only `/home/user/praxis` checkout. It added objects and FETCH_HEAD only; no refs or worktree changed. The Director confirmed HEAD is still `12bf995` and the worktree is clean (D-018).
- **Raw samples:** about 10 MB of raw Actions API samples are committed under `data/ci-sample*` for reproducibility.
