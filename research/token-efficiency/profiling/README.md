# Token-overhead profiling (`cbe.token-overhead/1`)

Python 3 standard library only. Pure functions, no network, no clock: the same inputs give the same output bytes.
The record format is [`../overhead-schema.json`](../overhead-schema.json). The findings are in
[`../OVERHEAD-ANALYSIS.md`](../OVERHEAD-ANALYSIS.md).

| File | Role |
|---|---|
| `phases.py` | Rules that put a tool call or provider request into a phase. Rules are data (`SHELL_RULES`, `TOOL_RULES`). A chained shell command takes the phase of its highest-precedence segment (`PRECEDENCE`). |
| `transcripts.py` | Claude Code transcript JSONL to one record per deduplicated request (dedup by `message.id`, last-written usage, the same rule as Praxis `SessionTranscript.requestsOf`), plus findings: duplicate tool calls, repeated reads, test runs with no edit in between, brief reads (bytes and bytes//4). |
| `observations.py` | REL-001 observation JSON (run-01 and run-02 formats) to one measured `run-total` record and `run-phase-estimate` records (turn-equivalent token estimates, measured elapsed time where run-02 records it). |
| `briefs.py` | Byte sizes of the run-02 brief templates, the directives and the task files, and how many cache-read tokens they cost by staying in context (estimate). |
| `profile.py` | CLI: `observations`, `transcripts`, `briefs`, `check` (schema validation with a small built-in checker). |
| `selfcheck.py` | Tests against the tiny fixtures in `fixtures/`: classification, dedup, findings, cost, schema conformance, determinism. |
| `config.json` | The cold-cache trial pairs used to size the runtime's fixed prompt prefix. |
| `run-all.sh` | Rebuilds every file in `out/`. |

## Reproduce

```sh
# from the cohort-based-engineering checkout; RUN02 = read-only snapshot of the run-02 branch at c8da63f
RUN02=/home/user/wt/cbe-run02-readonly research/token-efficiency/profiling/run-all.sh
```

`run-all.sh` runs these commands:

```sh
P=research/token-efficiency/profiling
PRICE=$RUN02/research/pricing/anthropic.price-table.json
python3 $P/selfcheck.py
python3 $P/profile.py observations --dataset run-01-D --label "run-01 Experiment D (complete, analysed); both arms" \
  --root . --glob 'research/experiments/REL-001/observations/*/REL-001-D-*.json' \
  --price-table $PRICE --config $P/config.json --out $P/out/run-01-D.json
python3 $P/profile.py observations --dataset run-02-echelon --label "run-02 ... EXPLORATORY PROFILING, within-arm only ..." \
  --root $RUN02 --glob 'research/experiments/REL-001/run-02/observations/echelon-*/*.json' \
  --arms echelon-original,echelon-optimized --within-arm-only \
  --price-table $PRICE --config $P/config.json --out $P/out/run-02-echelon.json
python3 $P/profile.py briefs --root $RUN02 --profile $P/out/run-02-echelon.json --out $P/out/run-02-context-sizes.json
python3 $P/profile.py transcripts --dataset fixture --label "synthetic fixture (format check only)" \
  --root $P --glob 'fixtures/*.jsonl' --price-table $PRICE --out $P/out/fixture-transcript.json
python3 $P/profile.py check $P/out/*.json   # (context-sizes is not a token-overhead document; run-all checks the other three)
```

When trial transcripts are available (they are in harness state `/tmp/claude-0/rel002/state/<runId>/transcripts/`
on the host that ran the trials, and are not committed), profile them with:

```sh
python3 $P/profile.py transcripts --dataset run-02-transcripts --label "..." --root STATE_DIR \
  --glob '*/transcripts/*.jsonl' --price-table $PRICE --out $P/out/run-02-transcripts.json
```

## Outputs (`out/`)

| File | Contents |
|---|---|
| `run-01-D.json` | 12 run-01 Experiment D trials, both arms (run-01 is complete and analysed, so per-arm figures are given). |
| `run-02-echelon.json` | The 19 committed Echelon-arm run-02 trials at c8da63f. **Exploratory profiling, within-arm only.** With `--within-arm-only`, `byArm` holds composition shares only (no counts, tokens or costs per arm), and `perRun` is cut down. Bare and directives arms are not read. |
| `run-02-context-sizes.json` | Brief, directives and task-file sizes, and estimated carry cost. |
| `fixture-transcript.json` | The synthetic fixture profiled end to end (format check). |

## Rules and models (stated in every record)

- **Measured vs estimated.** `tokens` holds only measured buckets. A phase share that is modelled goes in
  `tokenEstimate` with its method and assumptions. Observations hold run-level sums only, so every measured token of an
  observation is in the `run-total` record with phase `unattributed`.
- **Turn-equivalent model** (observations): a workflow command issued as its own tool call costs one request, and a request
  costs the run's mean context per request, `(input + cacheRead + cacheWrite) / requests`. This is an over-estimate when the
  agent chains commands in one call, and an under-estimate for late commands, whose context is larger than the mean.
- **Fixed prefix** `P`: cache writes of the first trial of a run (cold provider cache) minus those of its warm same-task
  partner (`config.json`). Run-01 gives 40,463 and run-02 gives 40,618 tokens.
- **Suspected prefix miss:** cache writes per agent of at least the dataset median plus `P/2`. This is inferred. Per-request
  data would make it exact (the first request's `cache_creation > cache_read`, which the transcript profiler flags).
- **Output scenario:** transcript output is a lower bound. The scenario uses 120 to 761 output tokens per request, the range
  run-01 measured for real final messages (Praxis `ReliabilityReport.fs:240-246`). It is labelled a scenario, not a measurement.
- **Token estimates for text** are bytes // 4 and are labelled estimates.

## Self-check

```sh
python3 research/token-efficiency/profiling/selfcheck.py   # prints PASS/FAIL per check; exit 0 when all pass
```
