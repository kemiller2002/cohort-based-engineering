# Token attribution and overhead profile (Echelon, REL-001)

Worker D, Echelon parallel research. Written 2026-10-20 against cohort main 68588a8, the run-02 read-only snapshot
c8da63f, and Praxis main 4ade512 (v3.17.0).

**Status of the numbers.**
- **run-01 Experiment D** is complete and its exploratory analysis is published, so this file reports both arms.
- **run-02** is a confirmatory run still in progress (32 of 88 trials committed). Its figures here are **exploratory
  profiling of the 19 committed Echelon-arm trials, within-arm only**. This file makes no arm-vs-arm comparison of
  cost, tokens, success or cost per verified requirement for run-02, and it does not read the bare or directives arms.
  Pooled figures combine both Echelon arms.

Records and derived values are in `profiling/out/` (schema `cbe.token-overhead/1`, [`overhead-schema.json`](overhead-schema.json)).
Every number below can be rebuilt with `profiling/run-all.sh`.

## 1. Data availability (the main blocker)

| Needed for phase attribution | Available? | Where |
|---|---|---|
| Run-level token sums (input, output, cache read, cache write 5m/1h) | measured | observations (`metrics.*`, `run02.tokens.byKind`) from `praxis telemetry reliability-report --agent-binding` |
| Number of provider requests per run | measured | the `numerator` of each token bucket |
| Tool calls, test runs (agent vs boundary), verify, validate-run and complete-verified calls and their ms, claims | measured (run-02); partly (run-01) | `run02.tests`, `run02.verification`, `run02.coordination`; run-01 `scoring.testRuns`, `scoring.validateRuns` |
| **Per-request usage, tool names and commands** | **unavailable** | Trial transcripts are copied to harness state `/tmp/claude-0/rel002/state/<runId>/transcripts/` (run-02 `harness/lib.sh:17`, `trial.sh:49-55`) on the host that ran the trials. They are not committed and not on this host. |
| Final output tokens | **unavailable** (lower bound only) | Claude Code transcripts record `output_tokens` when a block starts streaming (Praxis `ReliabilityReport.fs:240-262`) |

Without per-request data, measured tokens cannot be split by phase. The profiler therefore writes each run's measured
sums as one `run-total` record (phase `unattributed`). Phase shares come from a stated **turn-equivalent model**
(`tokenEstimate`): a workflow command issued as its own tool call costs one request at the run's mean context per request.
The transcript path of the profiler (`transcripts.py`) does exact per-request attribution. It passes its self-check, and it
ran cleanly on four real (non-trial) Claude Code sub-agent transcripts of this session; those outputs are not committed.

## 2. Phase breakdown

Token shares are **estimates** from the turn-equivalent model (median of per-run shares). Elapsed shares are **measured**
(run-02 records phase ms; run-01 does not). The residual is ingestion, discovery, implementation and reporting, which
cannot be separated without transcripts.

| Phase | run-01 D baseline (n=6) | run-01 D treatment (n=6) | run-02 Echelon pooled (n=19), tokens | run-02 pooled, elapsed (median ms) |
|---|---|---|---|---|
| coordination (claim or start) | 14.6% | 11.1% | 10.0% | not recorded |
| testing (agent-run `dotnet test`) | 14.6% | 11.1% | 10.0% | 12.3% (15.7 s) |
| verification (`verify` / `validate-run`) | 0% | 11.1% | 9.1% | 10.8% (10.6 s) |
| completion (`complete` / `complete-verified`) | 14.6% | 11.1% | 9.1% | 1.0% (1.1 s) |
| residual (unattributed) | 56.3% | 55.6% | 60.7% | 75.7% (80.9 s) |

Sources: `profiling/out/run-01-D.json` `summary.byArm.*.medianPhaseTokenEstimateShares`, and
`profiling/out/run-02-echelon.json` `summary.pooled.medianPhaseTokenEstimateShares` and `medianPhaseElapsedShares`.
Within each run-02 Echelon arm the shares are within ±3 points of the pooled values (`summary.byArm`, shares only).

**Mandated workflow commands** (claim, verify or validate-run, complete) are a median **27%** of tool calls in run-02
Echelon trials and 29% in run-01 D (`medianWorkflowCommandShareOfToolCalls`). Under the turn-equivalent model, that is about **28%** of context tokens. This is an
upper bound if agents chain the commands in one call, which only transcripts can show.

**Why Echelon costs more tokens in run-01 (published comparison, explained).** The treatment's median request count is
9, against the baseline's 7, and the mean context per request is 58.1k against 55.8k tokens. Two extra requests at about
58k tokens each are about 116k tokens per run. The observed difference is (3,244,824 − 2,463,287) / 6 ≈ 130k per run
(`analysis/exploratory-results.json`). At this scale, the protocol's token overhead is extra turns multiplied by the
per-turn context. The treatment's `validate-run` is one of those turns, and the agent's own test run, which it still makes
before `validate-run`, is the other candidate.

## 3. Where the tokens go

### 3.1 Token and cost composition (measured; output is a lower bound)

| | run-01 D (12 runs) | run-02 Echelon (19 runs) |
|---|---|---|
| cache read + cache write share of all tokens | 99.96% | 99.96% |
| cost share: cache writes | 56.7% | 64.7% |
| cost share: cache reads | 42.0% | 33.8% |
| cost share: output (lower bound) | 1.7% | 1.2% |
| mean context per request (median) | 56.6k | 61.8k |

These are pooled medians (`summary.pooled.medianCostShares`), priced with price table 2026-10-20.1 for claude-opus-5-5
(input $4, output $20, cache read $0.20, cache write 5m $5 per Mtok). Uncached input is about 2 tokens per request.

### 3.2 Repeated context loading: the runtime prefix (largest token item)

Every request re-reads a fixed prefix (the sub-agent system prompt and tool definitions). Its size comes from the two
cold-cache first trials:
- run-01: T3-r2-baseline wrote 61,730 cache tokens, against 21,267 for T3-r1-baseline, so P = **40,463**.
- run-02: seq 1, U8-r2-echelon-optimized, wrote 70,819, against 30,201 for seq 2, U8-r2-echelon-original, so P = **40,618**.

A non-trial calibration agrees: four general-purpose sub-agents of this research session read a 36,070-token cached
prefix on their first request.

| | run-01 D | run-02 Echelon |
|---|---|---|
| prefix re-read share of cache-read tokens (median) | 74.5% | 66.9% |
| prefix re-read share of estimated cost (median; range) | 30.8% (16–37%) | 24.0% (9–31%) |

The brief itself is small, so it is not an oversized handoff. The whole prefix is paid again on every turn. Each turn
saved therefore saves about 40.6k prefix tokens plus the run's history, about 62k tokens in all.

### 3.3 Cache misses and avoidable context changes (inferred)

A cold prefix costs about 40.6k extra cache-write tokens per agent, about **$0.195** more than reading the prefix from
cache. Runs are flagged when cache writes per agent reach at least the dataset median plus P/2:
- **run-02 Echelon: 9 of 19 runs flagged.** Warm runs write a median 32.0k per agent and flagged runs 71.2k. The
  inferred avoidable cost is **$2.34 of $9.64 pooled estimated cost (24%)**.
- **run-01 D: 1 of 12 runs flagged** (the first trial), $0.19 of $2.68 (7%).

The flagged run-02 runs cluster in the first trial of the run (U8-r2, seq 1), in the first two block-concurrent blocks
(U9-r1 and U2-r3; 4 agents launched together), and in U6, where two agents start together. The mechanism is consistent
with parallel launches finding no warm prefix, but without per-request data it is not confirmed.

> **Validity note for the run-02 owner (diagnostic, not an outcome).** In the committed subset, flagged runs are not
> spread evenly across the two Echelon arms (`summary.pooled.suspectedPrefixCacheMissRuns`). Cache state then moves
> estimated cost by up to about $0.19 per agent, independently of the arm. The preregistered analysis should treat cache
> state as the protocol requires (for example, as a covariate or a sensitivity analysis). This file draws no conclusion
> from it.

> **Erratum (coordinator, 2026-10-21): superseded by measured data.**
> - The 9-of-19 flag above is a heuristic: per-agent cache writes ≥ median + P/2, without transcripts. It was computed on
>   an early snapshot (c8da63f), and the subset includes U6 two-agent runs.
> - After run-02 completed, its owner checked all 88 confirmatory trials against the retained transcripts. The rule used:
>   an agent's first request wrote more cache than it read; U6 excluded.
> - Cold-prefix counts are balanced: A 2/20, B 2/20, C 2/20, D 3/20.
> - Repricing first-request writes at the cache-read price changes no preregistered decision. D vs A goes from +35.5% to
>   +43.9%, and D vs C from +2.3% to −1.1%.
> - Source: `../experiments/REL-001/run-02/analysis/cache-sensitivity.json` (exploratory).
> - The heuristic over-flags: about 47% here, against 9/80 under the measured rule. Use measured first-request data
>   (REL-TOKEN-001) instead of this heuristic.

### 3.4 Repeated validation and test runs (measured counts)

- **run-02 Echelon:** 27 agent-run full test runs and 17 boundary runs (verifier or validate-run) over 19 runs. The two U2
  runs make none. Every agent run is "beyond the one boundary run the protocol needs". How many ran at the same commit as
  the boundary run cannot be told without transcripts.
- **run-01 D:** the baseline makes 6 agent runs, one per trial as its brief asks. The treatment makes 7 agent runs and 6
  validate-runs. Its brief does not ask for an agent test run, yet in every trial the agent tests before `validate-run`.
- **Cost of a run:** one request (about 62k context tokens) plus its output written to cache. Time is the measured median
  agent test phase of 15.7 s per run.

### 3.5 Briefs and handoffs (bytes; tokens = bytes/4, estimates)

| Item | Bytes | ≈ tokens | Carry: cache-read tokens it costs by staying in context |
|---|---|---|---|
| run-02 brief, echelon-original (core + directives line + workflow-c + outcome) | 2,341 | 585 | ≈5.9k per run |
| run-02 brief, echelon-optimized (workflow-d) | 2,126 | 531 | ≈5.3k per run |
| `DIRECTIVES.md` (all non-bare arms) | 10,904 | 2,726 | ≈24.5k per run, about 3% of cache reads, if read |
| `requirement.md` (U1–U9) | 1,241–4,222 | 310–1,055 | |

The carry column assumes the pooled median of 11 requests (`out/run-02-context-sizes.json`). Neither brief is oversized.
The directives are the largest handoff, but they are about 6% of the runtime prefix. `praxis work verify` returns a
compact JSON (`VerificationJson.fs:35-60`, digest, status and duration per receipt), so verification handoffs are small.

### 3.6 Administrative completion overhead

Execution time is small. `complete-verified` takes a median 1.1 s, and its recorded step timings have these medians:
claim 16 ms, admission 180 ms, receipts 25 ms, Dokimos 621 ms, metadata commit 95 ms. Verification takes a median 10.6 s,
which is a full cold build and test (§4). The token cost of administration is the **turns**, not the execution: about 3
of 11 requests per run.

### 3.7 Not measurable from committed data

Duplicate tool calls, repeated file reads, test runs with no intervening edit, and per-phase output and cache writes
(for example, the share of cache writes due to `dotnet test` output). These are **unavailable**. The transcript profiler
computes them once transcripts or a per-request ledger exist.

### 3.8 Proportions asked for

| Overhead class | run-02 Echelon (pooled) | run-01 D | Basis |
|---|---|---|---|
| Caching (cache read + write) of tokens / of estimated cost | 99.96% / 98.5% | 99.96% / 98.7% | measured; cost uses output as a lower bound |
| Repeated context (prefix re-read) of cache reads / of cost | 66.9% / 24.0% | 74.5% / 30.8% | derived (P from cold pair) |
| Avoidable cache misses, of cost | 24% | 7% | inferred |
| Verification (tokens est. / elapsed) | 9.1% / 10.8% | 4.5% / n.a. | estimated / measured |
| Coordination (tokens est.) | 10.0% | 11.1% | estimated |
| Completion (tokens est. / elapsed) | 9.1% / 1.0% | 11.1% / n.a. | estimated / measured |
| Duplicate calls, repeated reads | unavailable | unavailable | needs per-request data |
| Output-token understatement of cost | +5.6% to +43% | +7.8% to +57% | scenario (120–761 tokens per request) |

## 4. Code paths that explain the measured overhead (Praxis 4ade512)

- **Verification is a cold rebuild every time.** `work verify` goes through `Praxis.Cli/VerifierCommands.fs:67-75` to
  `Praxis.Application/Work/Verification.fs:134-175`, which fences the claim, refuses a dirty worktree (`:149-151`), sends
  the request to the verifier and stores receipts. The verifier, `Praxis.Infrastructure/Work/TrustedVerifier.fs:314-361`,
  makes a fresh `git clone --no-hardlinks --no-checkout` into a temp directory (`:256-264`, `:331-335`), runs every policy
  validation in it (`:279-287`, `:349-355`) and deletes the clone (`:357-361`). Each verify is therefore a full restore,
  build and test (median 10.6 s; run-02 `tests.buildMs`). This is the reason it is independent, so it is not a target.
  The agent's own earlier run is the redundant one.
- **Failure detail is not in the verify output.** The receipt output is stored beside the receipt as `.output.txt`
  (`TrustedVerifier.fs:446-458`), but the CLI prints only status, digest, duration and path (`VerificationJson.fs:35-60`).
  An agent that wants to see failures runs `dotnet test` itself. This is consistent with §3.4 (unconfirmed).
- **Completion is cheap and already derived.** `work complete-verified` goes through `WorkClaimCommands.fs:136` to
  `WorkCompletionCommands.fs:62` and then `DerivedCompletion.fs:210-238`, which records step timings at `:217` (claim),
  `:224` (receipts), `:233` (Dokimos) and `:192` (metadata commit). Arguments are derived from the claim, the receipts and
  the host files (`:98-185`, PRAXIS-REL-012). That is why the D brief's workflow section is 1,071 bytes against C's 1,286,
  and why D's completion command has no `RESULT_PATH` or requirement flags for the model to copy. The remaining overhead is
  that verify and complete are still two separate model turns after the commit.
- **Measurement.** Requests are deduplicated by `message.id` with last-written usage (`SessionTranscript.fs:340-361`), and
  tool calls by id (`:376-389`). Output is downgraded to a lower bound (`ReliabilityReport.fs:240-262`). The session
  summary computes repeated reads, builds and test runs (`SessionTranscript.fs:440-490`), but the report keeps only sums.
  That is why committed observations cannot be phase-attributed. Agent attribution (`AgentBinding.fs:1-40`, PRAXIS-REL-010)
  works: run-02 shows 0 unattributed observations and `conservationBalanced: true`.
- **Harness secondary figure.** `harnessSecondary.subagentTokens` (for example, 73,855 for U4-r2-echelon-optimized)
  matches neither the total excluding cache reads (37,010) nor any bucket, and its definition is not recorded. It should
  be defined or dropped (P1).

## 5. Proposals (only where measured or code-supported)

| # | Priority | Proposal | Evidence | Expected effect |
|---|---|---|---|---|
| 1 | **P1** | Keep a content-free **per-request usage ledger** (request key, buckets, tool names, classified verbs, result bytes) in `telemetry reliability-report`. Draft: `/home/user/wt/worker-d/inbox-drafts/2026-10-20-REL-TOKEN-001-per-request-usage-ledger.md`. | §1. Phase attribution, duplicate detection and cache-miss detection are unavailable today. `SessionTranscript.fs:440-490` already computes the facts. | Makes §2 measured instead of modelled, and makes §3.3 exact. |
| 2 | **P1** | Take **final output tokens** from a non-streaming source (Claude Code OpenTelemetry `api_request` or `token.usage`, or the `claude -p` JSON result). Draft: `REL-TOKEN-002-final-output-usage.md`. | Transcripts show about 18–25 output tokens per request. Run-01 final messages were 120–761 (`ReliabilityReport.fs:240-246`). Cost is understated by 5.6–43% (run-02 median scenario). | Correct cost and cost per verified requirement. |
| 3 | **P1** | **Record cache state per agent** in observations: the first request's cache write and cache read, or a warm-up request before each block. Report cost with first-request cache writes shown separately. Define or drop `harnessSecondary.subagentTokens`. | §3.3: 9 of 19 runs are flagged, with $2.34 (24%) inferred avoidable cost, unevenly spread across arms. | Removes a schedule-driven confound from cost outcomes (for run-03 design, Worker C). |
| 4 | **P2** | Make **`praxis work verify` the agent's final test run**: the brief or directives say so, and verify (or `finish`, item 6) prints a bounded failure excerpt from the stored receipt output. | §3.4: 27 agent test runs plus 17 boundary runs in 19 runs; run-01 treatment agents always tested before validate-run. Code: `VerificationJson.fs:35-60`, `TrustedVerifier.fs:446-458`. | Up to about 1 request (≈62k tokens) and about 15 s per run, but only for runs whose last agent test was at the verified commit (to be measured with item 1). |
| 5 | **P3** | **Minimal tool set for workflow agents**: a custom agent type without unused tool and MCP definitions. This is harness-level, identical across arms. | §3.2: the 40.6k prefix is 67–75% of cache reads and 24–31% of cost. | Each 10k tokens taken off the prefix saves about 110k cache-read tokens per 11-request run (about 4–5% of cost) and $0.048 per cold miss. The prefix's composition is unmeasured, so its size must be checked first. |
| 6 | **P4 + P5** | **`praxis work finish`**: one deterministic command for the dirty check, verify and complete-verified, with compact output. Until it exists, have the brief chain `git commit && praxis work verify && praxis work complete-verified`. Draft: `REL-TOKEN-003-work-finish.md`. | §2: mandated commands are about 27% of tool calls and about 28% of context tokens (estimate). `DerivedCompletion.fs:98-185` already removed argument derivation. | About 1–2 requests per run (about 9–18% of context tokens, estimate), with no change to F1–F3. |
| 7 | **P5** | **Warm, then fan out**: when several agents start together, let one make its first request before the others start. Do this in the orchestrator (fixed rule, no adaptation). | §3.3: misses cluster on concurrent launches. | About $0.19 per avoided cold agent. Confirm with item 3. |

No P6 (adaptive orchestration) proposal is made. Claim pre-issue by the dispatcher (P4) would also save one turn, but it
changes who the claimant is under F2, so it needs design review and is not proposed here.

## 6. Limits

- The turn-equivalent shares rest on two assumptions: one request per workflow command, and the mean context per request.
  Chaining commands inflates the shares, and the larger late-run context deflates them.
- The prefix size comes from one cold pair per run. The two pairs agree to 0.4%, and the non-trial calibration is
  within 11%.
- Cache misses are inferred from run-level cache writes. U6 (two agents, shared remote) and U2 (runs of only 5
  requests) are the least certain.
- The output scenario uses final-message sizes from run-01. Intermediate tool-call messages may be shorter.
- run-02 is a partial, unbalanced subset (19 of the Echelon trials that will exist). Nothing here is a run-02 result.

## 7. Reproduce

```sh
RUN02=/home/user/wt/cbe-run02-readonly research/token-efficiency/profiling/run-all.sh
```

See [`profiling/README.md`](profiling/README.md) for each command, the models and the self-check.
