# ARCH-002 experimental harness

Runs one ARCH-002 trial per process: an agent (model `opus` = `claude-opus-5-5` or `sonnet` = `claude-sonnet-5-5`)
in arm A–D implements an initial requirement on a **brownfield** fixture (phase 1), then, in a new isolated session,
a follow-up requirement on the same workspace (phase 2). Scoring uses only pristine harness-side inputs. Binding
contract: `../design/INTERFACES.md`. Adapted from ARCH-001's harness (frozen); sources and hashes in
`../PROVENANCE.md`. ARCH-001 amendments A1–A4 are built in from the start (see "Defects not repeated").

## Arms (cumulative) and what each gets

| Arm | Workspace material | Tools on PATH (outside the workspace) | Brief sections | `submit` checks |
|---|---|---|---|---|
| A | requirement + visible acceptance tests | `submit` | core | clean committed tree, `dotnet build`, visible tests |
| B | + `docs/architecture/` (fixture pack) | `submit` | core + architecture | as A |
| C | + `docs/contracts/T<n>.contract.json` | + `ordo` | + decision contract | + contracts byte-identical to the pristine copy, same `ordo ecir check` verdict |
| D | as C | + `archcheck`, `tools/{policy,contracts,baseline}/` | + verifier | + `archcheck verify` (pristine policy, pristine phase contract, **pristine gate baseline**, `--require-clean`) exits 0 = no **new** DET violation of severity ≥ 2 |

Completion is identical in every arm and model: commit, `submit` (≤ 3 per phase), final line `ARCH002-DONE <gitHead>`.

## Fixtures (one directory per fixture; INTERFACES §4)

`$ARCH002_FIXTURES/<fixture>/` (default `../fixtures`): `repo/`, `pack/`, `policy.json`, `fixture.json`,
`tasks/T<n>/{requirement.md, acceptance/, contract.json, followup.md, followup-acceptance/, followup-contract.json, task.json}`.
Sealed store `$ARCH002_SEALED_DIR/<fixture>/` (default `/home/user/arch002-sealed/<fixture>/`):
`oracle/[Oracle.fsproj, OracleKit.fs …]`, `oracle/T<n>/{InitialOracleTests.fs, FollowupOracleTests.fs, oracle.json, probes.json}`,
`reference/T<n>/{good, trap, followup-good}` (mkref.sh overlays), `task-private/T<n>.json`, `seeded.json`,
optional `remediation-lines.json`.

`fixture.json` (public, read by the harness only, never copied into the workspace; every field optional, defaults =
the ARCH-001 Lending layout):

| Field | Used for | Default |
|---|---|---|
| `appName`, `appDescription` | core brief first paragraph | `Lending`, "a small library-lending application in F# on .NET 10" |
| `solution`, `testsDir` | core brief build/test lines | `Lending.slnx`, `tests/Lending.Tests` |
| `acceptanceDir` | where visible tests go when `task.json .files.visibleTests` is absent; brief | `tests/Lending.Tests/Acceptance` |
| `pack.doctrine`, `pack.instance` | arm-B brief file names; review inputs | `FOUR-TIER-ARCHITECTURE.md`, `<APPNAME>-ARCHITECTURE.md` |
| `oracleHostProject` | `LENDING_HOST_PROJECT_PATH` in a sealed `Oracle.fsproj` (`__SRC_ROOT__` = the exported tree also works) | `src/Lending.Host/Lending.Host.fsproj` |
| `maxConcurrency` | run-queue per-fixture limit (Summa builds are heavier) | the global concurrency |

`task.json .files.visibleTests[]` / `.followupVisibleTests[]` (`{source, target}`, source relative to the fixture)
place visible tests anywhere (e.g. Summa's test projects); `task.json .control` marks control tasks.

## Brownfield baseline (INTERFACES §3)

`setup.sh` evaluates the **base commit** (identical in every arm and model) with the pinned archcheck twice:
`state/pristine/baseline-gate.json` (pristine policy only: used by `submit` and given to arm D as
`tools/baseline/start.report.json`, so no probe content reaches an agent) and `state/pristine/baseline-scoring.json`
(policy + sealed task probes: used by scoring). Cached per (fixture, task, base commit, policy, probes, verifier) in
`$ARCH002_RUNS/.baseline-cache/` under a lock. A base commit the verifier cannot evaluate is X1.
Scoring runs archcheck at S1 and S2 with the full policy, the probes and `--baseline baseline-scoring.json`:
**new** = DET findings (ARC-TRC-01 excluded) not marked `preexisting`; **fixed** = baseline keys left unmatched
(descriptive); **architectural acceptance** = zero new DET findings of severity ≥ 2. Observation fields:
`architecture.p<k>.{detNew, detNewSev2plus, detNewSeverityWeighted, newByRule, detPreexisting, detFixed, fixedByRule,
newFindings, fixedKeys}` (all-findings totals `det*` kept, descriptive) and `architecture.newSinceS1`.

## Files

| File | Role |
|---|---|
| `lib.sh` | configuration (`ARCH002_*`), run-id grammar `ARCH-002-{CAL\|PILOT\|CONF\|SMOKE}-<fixture>-T<n>-<opus\|sonnet>-r<k>-<arm>[-suffix]`, helpers |
| `setup.sh RUNID` | workspace, tools, pristine copies, ordo verdicts, **baseline**, brief values, `run.json`, integrity snapshot |
| `trial.sh run RUNID` | setup → phase 1 → transition → phase 2 → score; resumable, per-run lock, X1 record |
| `launch-agent.sh RUNID K` | K1 headless `claude -p`, `--model` from `agent-config.json .models[<model>]`, fresh HOME/CLAUDE_CONFIG_DIR/session id/nonce, inherited env minus `.environment.unset` and every `ARCH001_*`/`ARCH002_*`/`SMOKE_*`; `timeout` 60 min (X5) |
| `submit.sh` | the completion gate (`tools/bin/submit`), fresh clone of HEAD, ledger; prints archcheck errors verbatim |
| `score.sh` / `score.py` | hidden oracle, visible tests, archcheck (probes + baseline always), diffs, tokens/cost per model → `arch002.observation/1` |
| `scan.py` | X4 scan (sealed stores, other runs, ARCH-001 state, narrowed own-state, cohort, foreign /tmp/claude-0, verifier sources, Echelon repos and `/home/user/kemiller2002/*`, oracle names) |
| `integrity.py` | X-integrity snapshots |
| `randomize.py` | `calibration-order.json`, `pilot-order.json`, `order.json` (seed 20261023) |
| `run-queue.sh ORDER` | `--concurrency N` (default 3) + per-fixture limits (`--fixture-concurrency summa=1`, env, or `fixture.json .maxConcurrency`), strict order, resumable |
| `superseded.sh` | A3 rule: superseded initial-oracle tests from `followup-good` → `superseded.json` (keyed `<fixture>/<task>`) |
| `review.sh`, `review-scrub.py` | blinded K1 review (trial's model), evaluation cost separate |
| `smoke.sh`, `smoke-agent.sh`, `smoke-live.sh`, `smoke/` | no-model brownfield smoke; one real K1 session per model |
| `pricing/` | price table copy + Sonnet 5.5 entry (from the same excerpt) |

## Commands

```bash
H=research/architectural-correctness/arch-002/harness
bash $H/smoke.sh                                   # T0:A T0:D T0:D:trap on the brownfield stand-in (no model cost)
bash $H/smoke.sh T0:A:trap                         # arm A: submit passes, the new violation is not accepted
bash $H/smoke-live.sh                              # one real K1 session per model (about $0.10)
bash $H/superseded.sh                              # after the fixtures freeze, before trials
python3 -I $H/randomize.py $H                      # all three orders from fixtures/*/tasks (or --suite F:T1,T2;G:T1)
python3 -I $H/randomize.py $H --only confirmatory --replicates K   # after power.py
bash $H/run-queue.sh $H/calibration-order.json --concurrency 3 --fixture-concurrency summa=1
python3 -I research/architectural-correctness/arch-002/analysis/remediation_table.py /home/user/arch002-sealed \
        research/architectural-correctness/arch-002/fixtures research/architectural-correctness/arch-002/analysis/remediation-lines.json
python3 -I research/architectural-correctness/arch-002/analysis/power.py arch-002/observations power.json --tasks 10 --cap-usd 600
python3 -I research/architectural-correctness/arch-002/analysis/analyze.py            # confirmatory results.json
python3 -I research/architectural-correctness/arch-002/analysis/selftest.py
```

## Defects not repeated (ARCH-001 §13)

- **A1** contracts, policy, baseline and probes are always outside the evaluated tree (`tools/`, `state/pristine/`,
  sealed store); `submit` prints archcheck's own errors verbatim; scan run-id boundary fix; own-state X4 narrowed.
- **A3** regression excludes superseded tests (`superseded.sh` → `superseded.json`, computed from `followup-good`).
- **A4** no `--help | grep` feature detection anywhere: `--probes`, `--baseline` and `--require-clean` are pinned options.
- Observations go to `../observations/`, git-ignored (`../.gitignore`) until every trial has ended.

## Smoke results

See `../PROVENANCE.md` § "Worker H smoke evidence".
