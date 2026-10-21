# ARCH-001 experimental harness (Workstream D)

Runs one ARCH-001 trial per process: an agent in arm A–D implements an initial requirement (phase 1), then, in a new
isolated session, a follow-up requirement on the same workspace (phase 2). Scoring uses only pristine harness-side
inputs. Binding contract: `../design/INTERFACES.md`. Reuse of REL-001 run-03: `PROVENANCE.md`.

## Arms (cumulative) and what each gets

| Arm | Workspace material | Tools on PATH (outside the workspace) | Brief sections | `submit` checks |
|---|---|---|---|---|
| A | requirement + visible acceptance tests | `submit` | core | clean committed tree, `dotnet build`, visible tests |
| B | + `docs/architecture/` (fixtures/pack) | `submit` | core + architecture | as A |
| C | + `docs/contracts/T<n>.contract.json` | + `ordo` | + decision contract | + every contract byte-identical to the pristine copy and `ordo ecir check` verdict unchanged |
| D | as C | + `archcheck`, policy copy in `tools/policy/` | + verifier | + `archcheck verify` (pristine policy, phase contract) exits 0 |

Completion is identical in every arm: commit, run `submit` (≤ 3 per phase; stop after PASS or the third), end the final
message with `ARCH001-DONE <gitHead>`. Briefs: `briefs/core.md` + arm sections in fixed order (B, C, D), rendered by
`render-brief.py` (run-03 byte copy); template and brief sha256 go to `run.json .phases[k].brief`.

## Files

| File | Role |
|---|---|
| `lib.sh` | configuration (`ARCH001_*` overrides, below) and helpers |
| `setup.sh RUNID` | builds `$ARCH001_RUNS/RUNID/{repo,tools,brief,state}`; base commit (fixed date: identical hash in every arm), arm-material commit, pristine copies, ordo verdicts, `run.json`, integrity snapshot |
| `trial.sh run RUNID` | setup → phase 1 → transition → phase 2 → score; resumable (skips done / X1 / interrupted runs), per-run lock |
| `launch-agent.sh RUNID K` | K1: one headless `claude -p` per phase, fresh `HOME`/`CLAUDE_CONFIG_DIR`/`--session-id`, nonce, `--tools Bash,Read,Edit,Write`, no MCP, inherited env minus `agent-config.json .environment.unset` and all `ARCH001_*`; `timeout` 45 min (exit 124 = X5) |
| `submit.sh` | the completion gate (installed as `tools/bin/submit`); checks a fresh clone of HEAD; ledger `state/submit-ledger.jsonl` |
| `integrity.py` | snapshot/compare of harness scripts, run tools, verifier dist, policy, ordo, sealed store, pristine copies (X-integrity) |
| `scan.py` | X4 scan of every tool_use input (sealed store, other runs, own harness state, cohort repo, foreign `/tmp/claude-0`, verifier source, oracle names); advisory: other local repos |
| `score.sh` / `score.py` | hidden oracle, visible tests, archcheck, diffs, tokens/cost → `arch001.observation/1` (`state/score/observation.json`; non-smoke also `../observations/RUNID.json`) |
| `review.sh RUNID` | blinded K1 review (rubric `../analysis/review-rubric.md`) of scrubbed change sets (`review-scrub.py`); result `state/review/result.json`, evaluation cost separate |
| `randomize.py` | `order.json` (96 confirmatory trials, seed 20261022) and `pilot-order.json` (T1, T8 × A–D) |
| `run-queue.sh ORDER.json` | runs an order with `--concurrency N` (default 3), resumable |
| `smoke.sh`, `smoke-agent.sh` | no-model end-to-end smoke (stand-in agent applies a reference solution) |
| `smoke-live.sh` | one real minimal K1 session (stream capture, submit, cost extraction) |
| `smoke/` | stand-in fixtures, sealed store and `archcheck` for smoke only (`task.json .standIn`; setup refuses them for non-smoke ids) |

## Configuration (`ARCH001_*`)

`ARCH001_FIXTURES` (default `../fixtures`), `ARCH001_SEALED_DIR` (`/home/user/arch001-sealed`; plaintext needed at
scoring time), `ARCH001_SEALED_ARCHIVE` (hashed for integrity if set), `ARCH001_ARCHCHECK` (`../verifier/dist/archcheck`;
`.dll` and `.py` entries are wrapped), `ARCH001_POLICY` (`../fixtures/policy/lending.policy.json`), `ARCH001_ORDO`,
`ARCH001_DOTNET_ROOT` (`/home/user/.tools/dotnet`), `ARCH001_NUGET_PACKAGES`, `ARCH001_CLAUDE`, `ARCH001_RUNS`
(`/home/user/arch001-runs`), `ARCH001_REVIEWS` (`/home/user/arch001-reviews`), `ARCH001_OBSERVATIONS`, `ARCH001_PRICE_TABLE`,
`ARCH001_DOCTRINE`, `ARCH001_AGENT_CMD`, `ARCH001_MODEL`, `ARCH001_BUDGET_MINUTES`, `ARCH001_MAX_SUBMITS`,
`ARCH001_CONCURRENCY`. The paths a run was set up with are stored in `run.json .config` and reused by `score.sh` and
`review.sh` unless overridden.

## Commands

```bash
H=research/architectural-correctness/harness
bash $H/smoke.sh                       # T0 in A and D with the stand-in agent (about 4 min, no model cost)
bash $H/smoke.sh T0:D:trap             # the architecturally invalid reference: submit FAIL, R1/R2 not accepted
bash $H/smoke-live.sh                  # one real K1 session (about $0.05)
python3 -I $H/randomize.py $H          # regenerate order.json / pilot-order.json (deterministic)
bash $H/run-queue.sh $H/pilot-order.json --concurrency 3
bash $H/review.sh ARCH-001-PILOT-T1-r1-D
python3 -I research/architectural-correctness/analysis/analyze.py              # confirmatory results.json
python3 -I research/architectural-correctness/analysis/analyze.py OBS out.json --label pilot
python3 -I research/architectural-correctness/analysis/power.py OBS power.json --cap-usd 2000
python3 -I research/architectural-correctness/analysis/selftest.py
```

## Per-run layout (`$ARCH001_RUNS/RUNID/`)

`repo/` (agent workspace, cwd) · `tools/bin/{submit,ordo,archcheck}`, `tools/policy/` (agent-visible copies) ·
`brief/AGENT_BRIEF-phase{1,2}.md` · `state/` (never named to the agent): `run.json`, `pristine/` (policy, contracts,
ordo verdicts, task.json, price table, agent config), `submit-ledger.jsonl`, `submit/p<k>-a<n>/`, `phase<k>/`
(`launch.json`, `stream.jsonl`, `transcripts/`, `final-message.txt`, `home/`, `config/`, `integrity*.json`,
`contamination.json`), `score/`, `review/`, `done`.

## Phases and commits

- Base commit (fixed date, same hash in every arm) → arm-material commit (B–D) = phase-1 start.
- Phase 1 → **S1** = last submitted commit of phase 1 (HEAD if none); F1 = first submitted commit.
- Transition: `git checkout -f -B main S1`, `git clean -fdx`, follow-up requirement, follow-up acceptance tests and
  (C/D) follow-up contract copied and committed by the harness (**follow-up commit**). The follow-up never exists
  anywhere an agent can read before this step.
- Phase 2 (new session) → **S2** = last submitted commit of phase 2 (HEAD if none); F2 likewise.

## Scoring (score.sh → score.py)

- **Functional**: R1 = every InitialOracle test passes at S1; R2 = every FollowupOracle test and every regression-subset
  InitialOracle test passes at S2. Regression subset: `oracle/T<n>/oracle.json .regression` (names or prefixes), else
  tests whose name contains "regression", else all InitialOracle tests. Hidden tests run in `state/score/oracle-*`
  from `git archive` of the commit; the tree copy and build output are deleted afterwards; observations carry outcomes
  per test name only.
- **Architectural acceptance** at S_k: the verifier evaluated the commit (exit 0/1) with the full pristine policy
  (+ `--probes oracle/T<n>/probes.json` when this `archcheck` advertises `--probes`) and reported zero DET findings of
  severity ≥ 2 (ARC-TRC-01 excluded). C/D also get the contract (ARC-TRC-01) and S2 is re-checked with the initial
  contract (decision preservation).
- **Requirement accepted** = functional AND architectural. **Completed task** = a phase-2 PASS submit.
- **Diffs**: phase 1 base→S1, phase 2 follow-up commit→S2: files modified/added/deleted, lines ±, pre-existing files
  rewritten (deleted lines > 50% of the file's lines), rework = lines changed in pre-existing files; pre-existing visible
  tests broken (passed at S1, not passing or gone at S2); new DET violations (S2 minus S1 by ruleId+symbol).
- **Cost/tokens per phase**: tokens from the session transcript, one usage record per message id (max output), priced
  with the copied price table; cost = the stream `result` event's `total_cost_usd` (includes background models such as
  haiku); cross-check: recomputed main-model cost vs `modelUsage[model].costUSD` (agrees when within 1%), token totals
  vs `modelUsage`; cold-equivalent cost; first-request cache read/write (`firstRequestCold`); tool calls by name; test
  executions (Bash commands with `dotnet test`); ordo/archcheck/submit invocations; wall time (launch → last event).
- **Ledger**: attempts, verdicts, first-pass correctness (first submit PASS and oracle pass at that commit).
- **Exclusions**: X1 setup failure (no observation; rerun with a fresh id), X4 contamination, X-integrity tamper
  (observation `.excluded`); X5 timeout flagged per phase, scored as is.

## Gates before a pilot / confirmatory run

1. `smoke.sh` A and D PASS end to end; `smoke.sh T0:D:trap` separates (done, see below).
2. `smoke-live.sh`: stream captured, cross-check agrees, no X4 (done).
3. Worker B: every `fixtures/tasks/T<n>/` has `task.json`, `contract.json`, `followup-contract.json`; `fixtures/policy/`.
4. Worker C: `verifier/dist/archcheck` exists; `archcheck selftest` passes; `--probes` / `--require-clean` decided.
5. `analysis/selftest.py` PASS; `randomize.py` order committed with its seed before trial 1.

## Smoke results (2026-10-21)

- `smoke.sh T0:A T0:D T0:D:trap` (stand-in fixtures, real dotnet/ordo/submit): A and D good → R1/R2 accepted 2/2,
  submits PASS/PASS, oracle 4/4 + 3/3 + regression 1/1, cost cross-check agrees, no X4/X-integrity/X5; D trap →
  submits FAIL/FAIL (archcheck ARC-SYM-02), R1/R2 functional but not architecturally accepted (0/2).
- Worker B's real T1 fixtures and sealed oracle, arm A, `good`/`followup-good` reference (stand-in verifier):
  oracle 12/12 initial, 6/6 follow-up, regression subset 1/1, submits PASS/PASS, rework 23 lines.
- `smoke-live.sh` (real K1, claude-opus-5-5): stream and transcript captured, agent ran `submit` (correct FAIL: the
  acceptance test needs unimplemented code), final line parsed, cost $0.044, recomputed vs reported main-model cost gap
  0.001%, first request not cold (3,324 cache-read tokens of shared prefix), no X4.
