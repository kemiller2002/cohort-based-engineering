# ARCH-002 provenance

ARCH-001 files are frozen published evidence and were **read only**. Everything below was copied into `arch-002/`
and then adapted there. Source paths are relative to `research/architectural-correctness/`. Hashes are sha256 of the
source file when it was copied (cohort checkout `5ff2037b0bfe7cbdc99784fe552f4967c3b9d312`, 2026-10-22). Fixture
workers append their own sections.

## Worker H: verifier, harness, analysis

### Verifier (`arch-002/verifier/`)

Source: `verifier/` (src, tests, samples, policy, `Archcheck.slnx`, `global.json`, `.gitignore`, `README.md`; no
`bin/`, `obj/`, `dist/`). Tree digest of the copied files (sorted `sha256sum` list, hashed):
`7cd371a7227871265c3447ff1d41b8a10e05e810e77cb600f400991847212d60`.

| File | Source sha256 | Change |
|---|---|---|
| `src/Archcheck/Domain.fs` | `76b612af1e91dac5d73d159fd4d7995e59c85297b683564a4c60644934300fa8` | `Finding` gains `Scope`, `Context`, `Preexisting` |
| `src/Archcheck/Rules.fs` | `405e777d029ab9068f8aac804aff6c042d7183e06269bef12996c232a0db8a85` | `finding` defaults the new fields; `at scope`; symbol rules record the use's scope |
| `src/Archcheck/Heuristics.fs` | `73e6b3926e621ad1fa89baa01bc7fbb6d7b3e6d33dbaa26e77f284f09af60785` | heuristic findings record their scope |
| `src/Archcheck/Report.fs` | `c63670a31906ec783545a5c509f6d6530b0b5ec72405c7b0ebd1780a30b59581` | schema `arch002.verifier-report/1`; gate ignores preexisting; `findings[].scope/context/preexisting`, `summary.new/preexisting`, `baseline` |
| `src/Archcheck/Verify.fs` | `02196dcd919b7b3c3e13eb5a7e9e3e77dc526b4c19efafc33f96b09b97909102` | `--baseline` read (outside `--repo`), source-line context, marking |
| `src/Archcheck/Program.fs` | `c387762d58d588d7cc282846e65575fa5e7f9fc7084a9d37962d165bdcd5d59e` | `--baseline` option and usage |
| `src/Archcheck/Selftest.fs` | `d2abd4fd62acfcb32aec927ec0f0940322a681aa0c177c198f47d2a0da05b710` | `baselineRepo`, `new`, `preexisting`, `fixed`, `newLines` expectations |
| `src/Archcheck/Archcheck.fsproj` | `a83ea2fbe8f8eb3e676f29cc9549bcbec92e7148e0d5f9e687f2c88f85ca2b07` | version 0.2.0; `Baseline.fs` |
| `tests/Archcheck.Tests/IntegrationTests.fs` | `0b999c4045fd3d7db29da0521cf476e52fbf38582c5af3774fc8a3f8ef4549ee` | `Baseline = None`; `baseline-new-and-preexisting` sample added |
| `tests/Archcheck.Tests/Archcheck.Tests.fsproj` | `4645c433aff9a654aaa231544316b2694fa9e9621866df62323d864ef42d42de` | `BaselineTests.fs` |
| `README.md` | `d2651b8fc943686cd305360dbe7108b6e02371c35e5b791b719dea5ddcb73385` | ARCH-002 section |

New: `src/Archcheck/Baseline.fs`, `tests/Archcheck.Tests/BaselineTests.fs` (10 tests), samples
`baseline-moved-lines`, `baseline-new-and-preexisting`, `baseline-relocated`. Every other file is byte-identical
to its source. Published to `arch-002/verifier/dist/` (git-ignored).

### Harness (`arch-002/harness/`)

| ARCH-002 file | Source | Source sha256 | Change |
|---|---|---|---|
| `lib.sh` | `harness/lib.sh` | `1dedc04ae18c72e0f3c527f5e312f22dc97b3ef312628622ada8ac5f69a0b326` | `ARCH002_`; runs `/home/user/arch002-runs`; sealed `/home/user/arch002-sealed/<fixture>`; run-id grammar with fixture and model; `fixture_paths`, `fixture_field`, `model_id`, `archcheck_cmd` |
| `setup.sh` | `harness/setup.sh` | `1c2018cccf25e3453b82445707c5300089b0dd0f2a5e8e8a4331f569cccb1087` | multi-fixture; visible tests from `task.json .files`; cached gate + scoring baselines of the base commit; arm-D baseline copy; brief fixture values; model in `run.json` |
| `trial.sh` | `harness/trial.sh` | `5f293370fce34a16c923771e3c811a21321d167ae1fd1e54ceb553c4e8c9176e` | fixture brief values; follow-up visible tests from `task.json`; `ARCH002_` variables |
| `launch-agent.sh` | `harness/launch-agent.sh` | `0887753ac074d00e594e589a42c89e0808fb69fc36353fb94c7f02fc93ac5f90` | `--model` from run.json; `ARCH002_` also unset; nonce text |
| `submit.sh` | `harness/submit.sh` | `aa3f78bb0257ca0b93218662557cbbfd4d477d9a14504f9fc52a8f96c28725b2` | arm D: `--baseline` (pristine gate baseline), `--require-clean` pinned (no `--help` detection), new-only failure list, verifier errors verbatim |
| `score.sh` | `harness/score.sh` | `bc2b814285991b9d9793082741bcd01ef0e36d76a7e75a192aa015e3f74a531e` | per-fixture sealed store; `__SRC_ROOT__` / `oracleHostProject`; probes + scoring baseline always |
| `score.py` | `harness/score.py` | `e658e66d30886bd2fb0ab6e6a2f9cb1ac80869df6e5feaf239189bb2922ce5f0` | `arch002.observation/1`; new/preexisting/fixed per phase; acceptance on new; `newSinceS1` multiset; A3 keyed by fixture/task; fixture, model, control, trap metadata |
| `scan.py` | `harness/scan.py` | `f7ba38ab211e7247999105141087218b6769ea16e8f15c7b240d145d23e14cee` | ARCH-001 A1 patterns kept; arch002/arch001 sealed names; ARCH-001 state roots; arch-002 verifier; seeded/remediation/task-private names |
| `randomize.py` | `harness/randomize.py` | `b3e3effb4ad38c2fff672bc5182a32aa17022cf00f113cdf6e79f2a623b0ad6c` | blocks (fixture, task, model, replicate); calibration and pilot orders; seed 20261023 |
| `run-queue.sh` | `harness/run-queue.sh` | `66914fe6abe7b60d2908c24efb57336772e0e7b73ba100ed5e2587b6dd636c0a` | per-fixture concurrency limits, strict order |
| `smoke.sh` | `harness/smoke.sh` | `39a9d971b9e52d88b9108d9c181b605ffb9be4bfb9946701c4b6e7c46306fdf3` | brownfield stand-in, real arch-002 archcheck, baseline-delta summary |
| `smoke-agent.sh` | `harness/smoke-agent.sh` | `2ba3f43619fe8aaa69887ee5fb1c09bdda2a042f97af00a5bbc13063fadc5232` | per-fixture sealed store; synthetic usage priced with the run's model |
| `smoke-live.sh` | `harness/smoke-live.sh` | `8babf010dcca4be9896ab1525053d809141e9400d6f70456c57d73da92c7151d` | one session per model |
| `integrity.py` | `harness/integrity.py` | `48baf3467c2af421a46f5828985382121ad224a91668695c012da8b1754cb1a6` | schema names only |
| `render-brief.py` | `harness/render-brief.py` | `1e91996a9215c9a239eecc04529f46f247b8229980564252234cb10a17879983` | byte copy |
| `review.sh` | `harness/review.sh` | `0b632183b8927c456cb3be94bcb187ab24d37f66c2c2536108eea99c1f218d10` | fixture pack file names; `/home/user/arch002-reviews`; trial's model |
| `review-scrub.py` | `harness/review-scrub.py` | `a79c207d0f98257c0c9fbbdfbdd95b394e7acb92c2a5956c5b43084366872369` | ARCH002 redacted too |
| `agent-config.json` | `harness/agent-config.json` | `fc939640b6ba42f2b2753d72d9aa7ca9d33a0e1b50cbeadee23d8fed860643ff` | `.models {opus, sonnet}`; budget 60 min; wrapper prompt byte-identical |
| `superseded.sh` | `harness/amendments/superseded.sh` | `5d1ba6a5ae568d102dc26b744344b0fd33cac2420fbfd74ee0d7f36c46daa5ea` | every fixture; `superseded.json` keyed `<fixture>/<task>` |
| `briefs/core.md` | `harness/briefs/core.md` | `df4df1c46952fadd842cb9e457cfbe90d7bf83be857a07cf20000947ead43bc0` | app name/description, solution, tests and acceptance dirs as placeholders; `ARCH002-DONE` |
| `briefs/arm-b-architecture.md` | `harness/briefs/arm-b-architecture.md` | `e18ae22b443d74ed247d060ba3da5752713d5298e956842364e090c7165b4e24` | pack file names as placeholders |
| `briefs/arm-c-contract.md` | `harness/briefs/arm-c-contract.md` | `c5944ac87e7ce5cb67c34fd32fa49d9f44441bbcb1aeb4c864c3e7f7cc760499` | byte copy |
| `briefs/arm-d-verifier.md` | `harness/briefs/arm-d-verifier.md` | `8401ab07a9e37a666ab5463d84106d6d6ea90eeed109599bf36911a699bed1b0` | baseline: pre-existing violations named and never gating |
| `oracle-template/Oracle.fsproj` | `harness/oracle-template/Oracle.fsproj` | `9d1d2fd1201809602edc4cae95841b69f51f56052de317772ca2fb35ba37cd41` | byte copy |
| `pricing/anthropic-pricing-2026-10-20.excerpt.md` | `harness/pricing/…excerpt.md` | `7f2fc1f9d14412a5ab139869af9d4ecdacfbf27cd9a3b4fc46bef6ce1f3abd09` | byte copy |
| `pricing/anthropic.price-table.json` | `harness/pricing/anthropic.price-table.json` | `dd58c305821c66ec59c2c567a936885be6833d480c915ad0778b5385ff325b42` | + `claude-sonnet-5-5` entry from the excerpt's "Claude Sonnet 5.5" row ($2 / $10, cache read $0.10, writes $2.50 / $4); `tableVersion` suffix `+arch002-sonnet` |
| `smoke/` | `harness/smoke/` (tree `06ed5467129d8dd14a0eb5e3f6f61c360260c1cdf1c07802879271b543e5513b`) | | brownfield `lending-smoke` fixture (pre-existing `Fees.stampedAt` clock read), real policy restricted to two projects, `fixture.json`, references keep the old violation, trap mirrors it; stand-in Python archcheck dropped (the real verifier is used) |

New: `README.md` (rewritten).

### Analysis (`arch-002/analysis/`)

| File | Source | Source sha256 | Change |
|---|---|---|---|
| `analyze.py` | `analysis/analyze.py` | `dae6642f15180fc7bd586bf1343f5f68cc3bc8408f39ede54103f49c8705247d` | splitmix64, Holm, percentile CI, classification and margins kept; baseline-delta violations; stratified bootstrap (tasks within fixture, replicates within task × model); model-stratified pooling + per-model estimates; H8 (margin 0.5, two-sided); lifecycle cost model; seed 20261023 |
| `power.py` | `analysis/power.py` | `33150db787e77d5cc51c552e2ab6e1a199806586081ec5f6561c6ccbd9593335` | pooled across arms and models; cells = tasks × models; rule max(2, min(needed, cap, 4)); cap USD 600 |
| `selftest.py` | `analysis/selftest.py` | `49aeb62a8cd29ebabc637b8fc4ca259041d5a390a0cc9c79708bf5898d6110a5` | synthetic order from randomize.py; planted model interaction and brownfield deltas; T1–T8 |
| `exploratory.py` | `analysis/exploratory.py` | `b0c2ade50e5516df60cacbd85e467c270280ffd9cfa30b91d412847497b22e2d` | by model and fixture; stratified bootstrap; control from `task.json .control` |
| `review-rubric.md` | `analysis/review-rubric.md` | `34310b05e0c4622443e9f5b87b7327112f92326bf1f52d47a86d7b49b8c56394` | file names generalized; schema name |

New: `remediation_table.py` (lifecycle model input from sealed references).

### External binaries

As ARCH-001 (`harness/PROVENANCE.md`): ordo 1.17.0 `33a37628…0bb1`, .NET SDK 10.0.402, claude-code 2.1.306 (recorded
per run in `run.json .tools`).

### Worker H smoke evidence (2026-10-22)

- Verifier: `dotnet test` 36/36 (34 unit + 2 integration); `archcheck selftest` 25/25 (22 ARCH-001 samples + 3 baseline).
- `smoke.sh` (tag `fin`, real arch-002 archcheck, brownfield `lending-smoke`, baseline 1 pre-existing ARC-SYM-02):
  A good and D good → submits PASS/PASS, accepted 2/2, S1/S2 new 0 / pre-existing 1; D trap → submits FAIL/FAIL
  (the message names only the trap's new line), accepted 0/2, new 1 (ARC-SYM-02); A trap → submits PASS/PASS,
  accepted 0/2 (functional, not architecturally accepted). Oracle 4/4, 3/3, regression 1/1 everywhere; no X4,
  X-integrity or X5.
- `smoke-live.sh` (real K1): opus $0.0664, sonnet $0.0189; recomputed vs reported main-model cost gap 0 / 0.000016
  (agrees), token totals gap 0; final line parsed; no X4. `submit` correctly FAILed (build: acceptance test needs
  unimplemented code).
- `analysis/selftest.py` PASS (T1–T8).

## Fixture F1 `lending-brownfield` (Worker B2, coordinator-recorded)

| arch-002 path | Source | Change |
|---|---|---|
| `fixtures/lending-brownfield/repo/` | ARCH-001 `fixtures/repo/` | Grown to about 1,560 lines of production F#, with 8 seeded violations (sealed `seeded.json`, 14 DET findings at start) and two new ports (`Files`, `Archive`) that the seeded V3/V4 bypass |
| `fixtures/lending-brownfield/pack/FOUR-TIER-ARCHITECTURE.md` | ARCH-001 `fixtures/pack/` | byte for byte (sha256 `725cb3d9…775b`) |
| `fixtures/lending-brownfield/pack/LENDING-ARCHITECTURE.md` | ARCH-001 `fixtures/pack/` | adapted: new §0 on existing violations; rule ids unchanged |
| `fixtures/lending-brownfield/{make-contracts.py,check.sh,policy.json}` | ARCH-001 `fixtures/make-contracts.py`, `fixtures/check.sh`, `verifier/policy/lending.policy.json` | adapted to F1 and baseline-delta scoring |

Self-check: `fixtures/lending-brownfield/check-output.txt`, RESULT: PASS (109 checks).

## Fixture F2 `summa` (Worker S, coordinator-recorded)

| Item | Value |
|---|---|
| Snapshot | Summa at `8b0e93ea`: 395 files, produced by `fixtures/summa/make-snapshot.sh` (reproducible; check S6). Dropped paths are listed in `fixtures/summa/PROVENANCE.md` |
| Copies from ARCH-001 | Listed with sha256 in `fixtures/summa/PROVENANCE.md` (doctrine byte for byte, `make-contracts.py`, `check.sh`, policy schema) |
| Baseline (policy only) | 347 DET findings: ARC-SYM-01 ×190, ARC-BND-01 ×157. Also 93 HEU. Sealed in `summa/baseline/` |
| Self-check | `fixtures/summa/check-output.txt`, RESULT: PASS (53 checks) |

## Scope decision: F3 `signal` deferred

Signal builds at `e19101f` (620/627 tests pass; the 7 failures need `node_modules`). It is deferred for scope: 9 tasks × 2 models over F1 and F2 already, and its trap pattern (System.Text.Json in Engine) duplicates F2's.
