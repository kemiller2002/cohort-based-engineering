# REPORT.md: Track A, software factory economics

> Committed by RD-000 from A-001's final hand-back text. The harness refuses subagent report-file writes (DECISION-LOG D-010). Worker final commit: `61aecbc`.

## Methods
- **Sources** (all read-only; full revisions in `data/README.md`):
  - Praxis execution records (`.ros/telemetry/executions`) in 14 repositories: 626 records.
  - Embedded per-request usage ledger (R8 and praxis): 3,654 requests.
  - Rehearsal telemetry for R3, R7 and R8.
  - GitHub Actions API, GET only: runs, jobs and steps. That covers 4,633 runs across Indy-init and R1–R10, plus the jobs of the 2,191 non-skipped runs created inside the R2–R10 timed windows, with 0 fetch errors.
  - research-documents@`b372a7f`: per-run usage for the controlled pilots CONSTRUCT-008 and time-entry-expanded-01.
  - cohort-based-engineering@`fb280d7`: price table and prior consolidated findings.
  - indy-init-audits@`10aeded` was checked and holds no economics telemetry.
- **Pricing** (ESTIMATE): claude-opus-5-5 list prices.

  | Token type | $ per million tokens |
  |---|---|
  | Input | 4 |
  | Output | 20 |
  | Cache read | 0.20 |
  | Cache write, 5-minute | 5 |
  | Cache write, 1-hour | 8 |

  For R3 and R7, where the 5-minute/1-hour split is unknown, all cache writes are priced at the 5-minute rate. Reasoning tokens are already inside the output count and are not priced twice.
- **Tooling:** pure-function Python in `scripts/econ.py`; entry scripts handle I/O; 18 pytest tests.
- **R8 work-item categories:** assigned by hand for all 56 items, each citing a SCHEDULE-ACTUALS.md or DEVIATIONS.md line.
- **CI measures:**
  - Job queue = `started − created`.
  - Billable minutes = job duration rounded up to whole minutes. This is a compute proxy; public repositories are not actually billed.
  - Step categories come from regular expressions on step names, so they are heuristic.
  - Per-commit latency = from the first run created to the last run settled.
  - Run-level queue time is not informative: `run_started_at` equals `created_at` for almost every run.

## Results

### Token efficiency (`data/rehearsal-tokens.csv`, `analysis/r8-economics.json`)

| Rehearsal | Tokens (measured) | Cost (estimate) | Verified units | Cost per unit (estimate) |
|---|---|---|---|---|
| R3 | 116.8M | $36.01 (matches R3's own figure) | 51/56 criteria | $0.71 |
| R7 | 260.9M | $74.50 | 73/161 P0 | $1.02 |
| R8 | 533.8M | $193.74 | 51/161 P0 fully verified; 266/613 obligations | $3.80 per requirement; $0.73 per obligation |

The units differ and the R8 ledger is INVALID, so this table describes each rehearsal but does not compare them.

**R8 cost structure:**
- Cache reads are 98.0% of tokens.
- Share of cost: cache read 54%, cache write 24%, output 22%.
- Output averages 694 tokens per request. These are final counts; REL-001's output counts were streaming-start lower bounds.
- The first request of each execution carries about 48.7k tokens (system prompt, tools, startup documents, brief). Assuming that prefix stays in context for every later request, it is about 30% of all context processed, or 42% for task agents (ESTIMATE).
- Task-agent context grows from about 57k tokens in the first tenth of a session to about 165k in the last tenth.
- The coordinator's context grows to about 830k, with 2 compactions.
- The coordinator accounts for 44% of tokens and 32% of cost. Its mean context per request is 416,786 tokens, 3.6 times the task agents' 116,721.

### Wall-clock efficiency (R8)
- The 47 task executions with transcripts ran a median of 13.3 minutes (transcript span).
- The first code edit came at a median of 4.1 minutes, so about 25% of agent time passed before any code changed.
- Task agents logged 756.8 agent-minutes over 379 elapsed minutes. Mean concurrency was 2.15 of 6 lanes (36%), with a peak of 5, and there were 34 minutes with no task agent running.
- Praxis's `time.wall_ms` is unreliable as a duration:
  - In 13 of the 47 executions it is below half the transcript span, because agents ran `work start` late.
  - Executions that were never finalized inflate it in other cases.

### CI overhead (`analysis/ci-overhead.json`)

| Rehearsal | CI minutes in failed or cancelled runs | Median commit latency |
|---|---|---|
| R2 | 22% | 325 s |
| R3 | 17% | 239 s |
| R4 | 48% | 218 s |
| R5 | 45% | 404 s |
| R6 | 85% | 476 s |
| R7 | 59% | 520 s |
| R8 | 25% | 173 s |
| R9 | 28% | 867 s |
| R10 | 88% | 2,470 s |

- **Total wasted CI time:** 67% of job-minutes across R2–R10 (10,458 of 15,568) were in failed or cancelled runs; 38% excluding R6 and R10.
- **Runner queueing:** median 3 seconds everywhere except R6, which had a p90 of 912 seconds and 7,612 queued job-minutes.
- **R10:** its build-and-test job hit the 20-minute limit and was cancelled on every PR.
- **Where step time went** (R2–R10, 8,191 step-minutes):

  | Step type | Share |
  |---|---|
  | Browser suites | 28–51% in most rehearsals |
  | Rebuilding the pinned Praxis verifier from source | 688 minutes (8.4%) |
  | Installs, checkout and setup | 1,433 minutes (17.5%) |

- **Recovering from a red run:** a red run was followed by a green run of the same workflow on the same branch after a median of 224 seconds (R8) to about 1,017 seconds (R7, R9). In all 65 such events, recovery came from a new commit, never a re-run of the same one.

### Rework and failure cost (R8; category tokens measured, category assignment is judgement)

| Category | Share of R8 tokens | Notes |
|---|---|---|
| Feature | 28.5% | |
| Coordinator | 44.2% | |
| Defect rework | 5.7% | 9 items, $13.73; 10.1% of task-agent tokens |
| Test back-fill | 5.8% | |
| Review | 4.6% | |
| Cross-lane change requests | 3.3% | |
| Acceptance | 3.4% | |

- All corrective work (defect, change-request and back-fill) is 26.4% of task-agent tokens.
- 53% of merges conflicted, and every one of the 26 conflicts was in Praxis state files under `.ros/` only, never in application code. Conflicted merges took 1,537 of the 2,791 seconds spent on merging.

### Rereads
- 20.4% of R8 file reads (262 of 1,286) re-read a file already read in the same session.
- Some files were re-read across sessions; for example Session.fs was read 48 times across 12 executions.
- Governance documents were rarely re-read: 23 governance reads in total.

### Instructions: benefit vs overhead
- **Controlled pilots** (n=3 per arm):
  - CONSTRUCT-008: protocol arm B used 47% more cumulative tokens than plain arm A, at equal acceptance.
  - time-entry-expanded-01: arm B used 93% more than arm A.
  - Mechanical-first arm C was 12% cheaper than A in CONSTRUCT-008 but 33% more expensive in the expanded task.
- **Prior evidence** from cohort-based-engineering:
  - Four-tier guidance in the brief helps: architecture violations fell from 29/68 to 0/71, and cost per accepted requirement fell from $0.556 to $0.437.
  - The optimized Echelon setup cost 35.5% more than bare Claude.

### Verification cost vs task size
Across 21 R8 feature executions, the number of test runs does not track lines added (Spearman 0.08), while tokens do (Spearman 0.63). This is observational and the sample is small.

## Limitations
- No provider bill was available, so every cost is a list-price estimate.
- Only R3, R7 and R8 have token data.
- 8 R8 executions have no transcript.
- Category assignment, step classification and the fixed-prefix model are heuristics.
- CI windows are cut at T0+420 minutes.
- The time agents spend waiting on CI or approvals is not recorded (`time.blocked_ms` is 0 in every record).
- The token cost of rereads is unavailable.
- No dataset varies the agent count while holding scope fixed.

## Ranked recommendations
All benefits below are estimates derived from the measured shares above.

1. **Make the coordinator cheaper.** Cap its context (for example, refresh from a checkpoint) and send it compact notifications instead of full transcripts. If its context matched a task agent's, its $61 could fall toward about $30 per rehearsal, roughly 15% of R8 cost. Effort: low to medium.
2. **Stop rebuilding the Praxis verifier in CI.** Cache it or use the release binary. Saves about 8% of CI step time (688 minutes across R2–R10). Effort: low.
3. **Fail fast and shard browser suites.** Run cheap gates first and fit suites inside job limits. This targets the 38–88% of CI minutes in failed or cancelled runs, R10's 41-minute latency and R6's queueing. Effort: medium.
4. **Remove `.ros/` state conflicts.** Make Praxis state per-branch, or append-only with a merge driver. This removes the conflict handling on 53% of merges (about 26 minutes in R8). Effort: low to medium.
5. **Fill idle lanes.** Use dependency-aware dispatch. Utilisation was 36%, so there is headroom on elapsed time if dependencies allow it. Effort: medium.
6. **Fix telemetry.** Start the execution clock at the transcript start, require a block reason with a timestamp, and record CI waits. These make the approval and CI waits measurable. Effort: low.
7. **Do not add process protocol by default.** Prefer short guidance in the brief, which has measured benefit, over protocol steps, which measured 35–93% more tokens. Effort: none.

## Reproduction
`PRICE=/home/user/cohort-based-engineering/research/pricing/anthropic.price-table.json`. Then run:

1. `build_executions.py` and `build_transcript_detail.py` over `/home/user` with the repository list.
2. `analyze_r8.py data $PRICE <R8 merges.jsonl> analysis/r8-economics.json`.
3. `build_rehearsal_tokens.py`.
4. `build_controlled_usage.py /home/user/research-documents $PRICE data/controlled-usage.csv`.
5. `fetch_ci_runs.py`, then `build_ci.py`, then `fetch_ci_jobs.py --timed-only`, then `analyze_ci.py`.

Exact command lines are in `experiments.json`.
