# Track A datasets: provenance and columns

All files are derived by the scripts in `../scripts/` from read-only sources. Re-run commands are in
`../REPORT.md` §Reproduction. Values are MEASURED unless the column name ends in `ESTIMATE` or
`LOWERBOUND`. An empty cell means **unavailable** (not recorded by the source); `0` means a recorded zero.

## Source revisions

| Source | Revision |
|---|---|
| kemiller2002/indy-init-rehearsal-001 … 010 | 001 `dd63ab4`, 002 `b053d1d`, 003 `59cf4d2`, 004 `78a1b15`, 005 `b972cb4`, 006 `41fb6d6`, 007 `f61493f`, 008 `fd8fba9`, 009 `0e76050`, 010 `95b3ed4` |
| kemiller2002/praxis, mercatus, ordo, signal | praxis `12bf995`, mercatus `a841f30`; ordo and signal at their checked-out heads (see `../../../inventory/starting-revisions.tsv`) |
| kemiller2002/Indy-init | `dae2347` |
| kemiller2002/cohort-based-engineering (price table) | `fb280d7`, `research/pricing/anthropic.price-table.json` tableVersion 2026-10-20.1 |
| research-documents (private, frozen store) | `b372a7f` |
| GitHub Actions API | fetched 2026-11-08 ~18:40–19:30Z (see `raw/ci-fetch-manifest.json`) |

**Pricing (ESTIMATE basis).** claude-opus-5-5 first-party list price per million tokens: input 4.00, output 20.00,
cache read 0.20, cache write 5m 5.00, cache write 1h 8.00 USD. Provider-billed cost is unavailable everywhere.
Where the 5m/1h cache-write split is unknown (R3, R7), all cache writes are priced at the 5m rate.
Reasoning tokens are inside output and are not priced twice.

## Files

### `executions.csv` (626 rows): one row per Praxis/ROS execution record
Source: `<repo>/.ros/telemetry/executions/*.json` in R1–R6, R8–R10, mercatus, praxis, ordo, signal (R7 and
Indy-init have none). Script: `build_executions.py`.
- `repo, file, executionId, workItemId, status, startedAt, finalizedAt` — record identity; `status=active` means never finalized.
- `agentId` (`claude-code/<role>` in R8), `model`, `runtimeVersion`, `sessionId`.
- `commits, filesAdded, filesModified, linesAdded, linesDeleted` — `repository.changeSummary` (git diff over the execution).
- `tokens.*`, `model.requests`, `tool.*`, `context.*`, `time.*` — metric values by id (see `<repo>/telemetry/metrics.json` for definitions). `time.wall_ms` is ROS wall time from `work start` to finalization; `time.agent_wall_ms` is first-to-last transcript entry.
- `agentStartedAt, agentEndedAt, distinctFilesRead, apiErrors, retries` — from the embedded transcript summary (`rawTelemetry[].payload`, schema `praxis.claude-session-summary/2`).
- `tokens.total4` — input + output + cache read + cache write; empty when any bucket is missing.
- `costUsdListPriceESTIMATE` — list-price cost (see above); empty when tokens or model are missing.
- `duplicateMetricIds` — metric ids that appeared more than once in the record (none in this corpus).

### `requests.csv` (3,654 rows): one row per provider request
Source: the `requestLedger` in transcript summaries (R8: 3,100 requests, 49 executions; praxis: 554). Script:
`build_transcript_detail.py`. Columns: `input, output, cacheRead, cacheWrite, cacheWrite5m, cacheWrite1h, reasoning`
(provider usage per request), `contextTokens` = input + cacheRead + cacheWrite (the request's context), `seq` =
position in the execution's ledger, `costUsdESTIMATE`. Sum over requests equals the execution totals for all 49
executions (checked; 0 mismatches).

### `rereads.csv`, `tool-calls.csv`
Files read more than once inside one session (`reads` = count, `governance` = also listed as a governance read) and
tool-call counts by tool name, from the same transcript summaries.

### `r8-workitem-categories.csv`
Hand classification of the 56 R8 work items into coordinator / infrastructure / feature / cross-lane-CR / review /
defect-rework / test-backfill / acceptance, each with the line of `evidence/SCHEDULE-ACTUALS.md` or
`evidence/DEVIATIONS.md` that justifies it. This is a judgement; see REPORT limitations.

### `r8-by-category.csv`
Output of `analyze_r8.py`: per category counts, tokens, list-price cost ESTIMATE, agent minutes, requests,
repeated reads, test and build executions.

### `rehearsal-tokens.csv`
Rehearsal-level timed-window token buckets (R3, R7, R8 only; others `unavailable`), list-price cost ESTIMATE,
outcome counts with source lines, tokens and cost per verified unit. **Units differ by rehearsal** (R3 criteria,
R7/R8 P0 requirements), so rows are not directly comparable.

### `controlled-usage.csv` (21 rows)
Per-run provider usage from research-documents `research/construction-by-design/{CONSTRUCT-008,time-entry-expanded-01}/results/*/usage.json`.
`outputLowerBound` is the transcript's streaming-start count; `outputEstimateChars4` is the experiment's own
characters/4 estimate. `costUsdListPriceLOWERBOUND` uses the former, `costUsdListPriceESTIMATE` the latter.

### `rehearsal-windows.csv`
T0 and window end per rehearsal with the file that states them (R1 not found).

### CI files
- `raw/ci-runs-<repo>.jsonl` — trimmed `GET /repos/kemiller2002/<repo>/actions/runs` records (Indy-init + R1–R10, 4,633 runs).
- `raw/ci-jobs-timed.jsonl` — `GET .../actions/runs/{id}/jobs?filter=all` for every non-skipped run created inside a timed window.
- `ci-runs.csv` — one row per run. `queueSeconds` = run_started_at − created_at (GitHub sets these equal for almost all runs, so run-level queue is **not** informative; use job-level). `spanSeconds` = updated_at − run_started_at, an upper bound on run duration (includes re-attempt gaps). `inTimedWindow` = created inside the rehearsal window.
- `ci-summary-by-repo.csv`, `ci-summary-timed-by-workflow.csv` — run-level aggregates (`summarize_ci`).
- `ci-jobs.csv` — job rows: `queueSeconds` = started_at − created_at (runner wait), `durationSeconds` = completed_at − started_at.
- `ci-steps.csv`, `ci-step-categories.csv` — step durations, classified by name regex (`econ.STEP_CATEGORIES`; heuristic).
- `ci-commit-latency.csv` — per head SHA: first run created → last run updated (time until every workflow on that commit settled).
- `ci-red-then-green.csv` — a red run followed by the next green run of the same workflow on the same branch.
