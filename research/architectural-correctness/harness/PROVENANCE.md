# ARCH-001 harness provenance

Sources reused by the ARCH-001 harness (`research/architectural-correctness/{harness,analysis}/`), with the sha256
of each source file when it was read. REL-001 files were **read only**; nothing under `research/experiments/REL-001/`
was modified, and no REL-001 state root (`/tmp/claude-0/rel003/*`), `REL003_` variable, worktree or pin is used.
The REL-001 run-03 files were read from the cohort checkout at `c1ebb001ba25755ff6fe9ad043e36b1be43ed8f9`
(run-03 harness last changed at `5b2ccb5747e7d7db1b6f104a9b1759d845f82a29`, the coordination pin).
Paths below are relative to `research/experiments/REL-001/` unless absolute.

## Copied byte for byte

| ARCH-001 path | source | sha256 |
|---|---|---|
| `harness/render-brief.py` | `run-03/harness/render-brief.py` (itself run-02's) | `1e91996a9215c9a239eecc04529f46f247b8229980564252234cb10a17879983` |
| `harness/pricing/anthropic.price-table.json` | `research/pricing/anthropic.price-table.json` | `dd58c305821c66ec59c2c567a936885be6833d480c915ad0778b5385ff325b42` |
| `harness/pricing/anthropic-pricing-2026-10-20.excerpt.md` | `research/pricing/anthropic-pricing-2026-10-20.excerpt.md` | `7f2fc1f9d14412a5ab139869af9d4ecdacfbf27cd9a3b4fc46bef6ce1f3abd09` |

The wrapper prompt in `harness/agent-config.json` (`.prompt`) is the run-02/run-03 wrapper, byte for byte
(source `run-03/harness/agent-config.json`, `296c9dc36f150dd7d84a1283b93dece1b77115304a32a7c02bb6a5fc3670692f`).

## Adapted (copy, then changed)

| ARCH-001 path | source | source sha256 | what changed |
|---|---|---|---|
| `harness/lib.sh` | `run-03/harness/lib.sh` | `ad9a5c83e0d18726ef05c56e194cbb7649d038fd2407efb11eb1b51d07119e95` | prefix `ARCH001_`; roots `/home/user/arch001-runs` (outside every repo); run-id grammar `ARCH-001-{PILOT,CONF,SMOKE}-T<n>-r<k>-<arm>`; arms A–D as pack/contract/verifier cumulation; Praxis/Echelon, pin gate and shims dropped; `sha`/`tree_sha`/`utc`/`label_of`/`run_paths` kept |
| `harness/setup.sh` | `run-03/harness/setup.sh` | `cba690698e1c8370fd2f7ee246c9c55858dfa864b39b11982ed1af1050648152` | three-tree isolation kept (workspace / workspace-external tools / harness state); Lending paths; fixed-date base commit identical in every arm, arm material as a second commit; pristine copies; ordo verdicts on pristine contracts; integrity snapshot; follow-up never copied at setup |
| `harness/trial.sh` | `run-03/harness/trial.sh` | `e4d4b7763dc3da549723562e7e3248a0a983005b2771b317ae95c86a0450b0b5` | two phases with a transition commit; brief rendered per phase; integrity re-hash and contamination scan per phase; resumable `run` with a per-run lock; X1 record |
| `harness/launch-agent.sh` (K1) | `run-03/harness/launch-agent.sh` | `c3edbff8c502434f7ba695cf7499b300059579e45825f8c203ccdf15f332bfe2` | per-phase; **inherited environment** instead of `env -i` (auth/proxy come from it) with an unset list (agent-config `.environment.unset`) and every `ARCH001_*`/`SMOKE_*` variable removed; HOME/CLAUDE_CONFIG_DIR under the run's state; transcript copied from the fresh config dir; nonce text |
| `harness/score.sh` | `run-03/harness/score.sh` | `72c7dde88222bf4e0be18b8fd20b32624960d567f467f16272cef08396c7480e` | oracle-outside-workspace pattern kept (`git archive` → state); four oracle runs per trial (initial, follow-up, regression, first-submit); B's sealed `Oracle.fsproj` + `OracleKit.fs` when present, else `oracle-template/`; visible tests at S1/S2; archcheck runs; Praxis report and completion identity dropped |
| `harness/score.py` | `run-03/harness/score.py` | `41109f6a25888c198bfbd3bd0005e7bcecde52669ba55124da7a7b7a51a57906` | kept: `read_json`, `read_jsonl`, `usage_by_message` (message-id dedup, max output), `usage_tokens` (5m/1h split), `price_entry`, `priced`, first-request cache measurement, TRX reader; changed: usage from the session transcript (the stream's assistant events carry the message-start output count only), cross-check against the stream `result` event (`total_cost_usd`, `modelUsage`); new: requirements R1/R2, architecture, diffs/rework, ledger, X4/X5/X-integrity, schema `arch001.observation/1` |
| `harness/scan.py` | `run-03/harness/score.py` `x4_hits` + `X4_PATTERNS` | (as above) | scans tool_use inputs only; ARCH-001 patterns (sealed, other runs, own state, cohort, foreign /tmp/claude-0, verifier source, oracle names) |
| `harness/randomize.py` | `run-03/harness/randomize.py` | `38f56b3a41909066eee16cac802a376fd866ad035e8ff5eee28d8784f4524f8c` | algorithm unchanged; constants (arms A–D, tasks T1–T8, replicates, seed 20261022, run-id format); fixed pilot T1+T8 × A–D |
| `harness/smoke.sh` | `run-03/harness/smoke.sh` | `5706f557a4cecaa403112d16228f510051bb9c34c79c88f3c38d7ec3f3499788` | stand-in fixtures/sealed/verifier by default; summary line for the ARCH-001 observation |
| `harness/smoke-agent.sh` | `run-03/harness/smoke-agent.sh` | `848113e74b95fbbf9ca20e2790612d999af56785fd53fd38f280ad0f62006783` | same interface as launch-agent.sh (RUNID PHASE); applies reference overlays (stand-in and Worker B layouts), runs `submit`, writes a synthetic stream |
| `harness/oracle-template/Oracle.fsproj` | `run-03/fixtures/oracle/Oracle.fsproj` | `ea30f5244e8282828c70b0fbc9eacbde7b3a64a5c50d559c2c334509e2de9546` | placeholders for compile items and one ProjectReference per `src/**/*.fsproj`; used only when the sealed store has no `Oracle.fsproj` |
| `harness/agent-config.json` | `run-03/harness/agent-config.json` | `296c9dc36f150dd7d84a1283b93dece1b77115304a32a7c02bb6a5fc3670692f` | ARCH-001 schema; `maxSubmits`; environment inherit/override/unset policy |
| `analysis/analyze.py` | `run-03/analysis/analyze.py` | `24af63325b0674a796175cd7982deaad95ec45aa99e32bfd40bba52c96057076` | kept: splitmix64 stream per contrast, 10,000 resamples, percentile interval, bootstrap p, Holm, canonical rounding; changed: two-stage cluster bootstrap (tasks, then replicates), ARCH-001 metrics, contrasts H1a–H6, classification with equivalence margins, X5 sensitivity |
| `analysis/power.py` | `run-03/analysis/power.py` | `8ab70df966d5127dfcfea92e67523159db3a87a04e1076604853cc52411df64c` | `Z` constant and the normal-approximation formula kept; ARCH-001 pilot inputs, acceptance-difference and ratio targets, resource cap |
| `analysis/selftest.py` | `run-03/analysis/selftest.py` | `09aee6db9dda1af56026e00b6a396fe9f0f833737e7d4bca7bf623dcd16a376f` | pattern kept (synthetic observations from order.json, planted cases, determinism); ARCH-001 checks T1–T6 |

## New

`harness/submit.sh`, `harness/integrity.py`, `harness/review.sh`, `harness/review-scrub.py`, `harness/run-queue.sh`,
`harness/smoke-live.sh`, `harness/briefs/{core,arm-b-architecture,arm-c-contract,arm-d-verifier}.md`,
`harness/smoke/` (stand-in fixtures, sealed store and `archcheck`, used by smoke runs only),
`analysis/review-rubric.md`, `harness/order.json`, `harness/pilot-order.json` (generated by `randomize.py`).

## External binaries (hashed into every run.json and integrity snapshot)

| Tool | Path | sha256 |
|---|---|---|
| ordo 1.17.0 (tarball) | `/home/user/.tools/ordo/ordo-linux-x64.tar.gz` | `ab9437f5b4c72e86eaf1a25bfa7dc167e548be91ff9112df65bee678c5fb1b5d` |
| ordo 1.17.0 (binary) | `/home/user/.tools/ordo/ordo-linux-x64/ordo` | `33a37628439f32a2dbe2b465d3623b80cd0a2bd24a23b1317507047640780bb1` |
| claude-code 2.1.306 | `/opt/node22/bin/claude` | recorded per run (`run.json .tools.claudeCode`) |
| .NET SDK 10.0.402 | `/home/user/.tools/dotnet` | recorded per run (`run.json .tools.dotnet`) |
