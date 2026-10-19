# REL-001 run-01 protocol (preregistration)

**Registered 2026-10-19, before any Experiment A, B, C or D case was run.**
Machine-readable copy: [`../analysis/preregistration.json`](../analysis/preregistration.json)
(`minimumEligibleRunsPerArm: 6`, read by `analysis/analyze.fsx`). Changes after this
commit are amendments: they are dated, appended below and never rewrite this text.

## Scope

Run-01 has four parts. A, B and C are deterministic, scripted conformance experiments
(no model in the loop) that test the rollout gates of `design.md` directly. D is the
agent-trial experiment for H1-H3; run-01 only **prepares** D (fixtures, harness, smoke
check). No D trial is run under this protocol until the lead researcher starts it.

## Arms and pinned versions

| Arm | Praxis | Ordo | Dokimos |
| --- | --- | --- | --- |
| baseline | v3.12.0 (`6e2d1f9`), asset sha256 `59d1f09f...2c2f3f` | not used | not used in the control workflow (scoring only, D) |
| treatment | v3.15.0 (`73f95ec`), asset sha256 recorded at download | `e6fe390`, `sde` built from source; `ecir/1` | dokimos-v0.6.0 (`828208f`), sha256 `484cbc0c...a1e94b` |

Every binary is downloaded from its GitHub release, checked against the release
checksum file, kept under `/tmp/claude-0/rel001/bin` and never committed. Each result
records the sha256 of the executable it ran. Fallback: if v3.15.0 is not published by
2026-10-19T22:10Z, A and B use v3.14.0 and C is reported BLOCKED (3.14.0 fails gate P4).

## Hypotheses

Targets, not results (`design.md`, RES-REL-007/008):

- **H1** treatment reduces total tokens per independently verified requirement by >= 20%.
- **H2** treatment reduces rework frequency by >= 30%.
- **H3** treatment does not increase escaped defects.
- **HA** (A) treatment: zero duplicate active owners, zero stale completions accepted,
  zero lost work. Baseline: more than one process reports ownership of the same item.
- **HB** (B) treatment: every invalid contract/decision case is refused before a
  completion is recorded; the valid contract proceeds. Ordo's `sde ecir check` refuses
  every contract-intrinsic invalid case; **any invalid case Ordo admits is a finding**,
  reported, never hidden. Baseline: every input reaches a recorded completion.
- **HC** (C) treatment verifies only validate-run-backed, in-lease, revision-matching
  evidence; missing, forged, replayed, stale and mis-bound evidence are refused.
  Baseline: `work complete --evidence` accepts every case.

Rollout targets: zero duplicate active claims; zero invalid decisions accepted; zero
unverified completions; >= 20% fewer tokens per verified requirement; >= 30% less
rework; no increase in escaped defects.

## Experiments A, B, C (deterministic)

Each case runs in a fresh directory `/tmp/claude-0/rel001/runs/<runId>`, prints one JSON
line to `results/<exp>/<arm>.jsonl` (case, arm, binaries' sha256, expected, observed,
pass/fail against the hypothesis, wall ms, or `blocked` with a reason) and each
experiment writes `results/<exp>/summary.json`. A case that cannot execute is recorded as
blocked; no result is manufactured.

- **A, concurrent ownership.** K = 8 processes race on one item with the local file store;
  4 independent clones race through the git-ref store against a bare origin; retries;
  short lease expiry and recovery; SIGKILL during `validate-run` and during
  `complete-verified`, then recovery; delayed completion by the stale owner. Baseline:
  K = 8 concurrent `work start` on one item, and 4 clones each `work start` then push.
  Metrics: duplicate active owners, stale completions accepted, lost work (item neither
  completed nor recoverable).
- **B, contracts.** Valid contract; nonexistent decision; incorrect decision node type;
  unsupported version; unresolved dependency; contradictory decisions (fixtures authored
  where Ordo's corpus lacks one). Each case is checked by Ordo `sde ecir check` and
  Praxis `ordo contract check`, and driven through `work complete-verified
  --ordo-contract`. Baseline: the same inputs through `work start` / `work complete`.
  Metric: invalid accepted.
- **C, completion verification.** Valid (`validate-run` passing); missing; forged result
  document; replayed (same packet again; consumed packet straight to Dokimos); stale
  (lease expired; result observed before the claim; commit after the run = revision
  mismatch); commit-to-evidence binding valid vs invalid. Baseline: `work complete
  --evidence` with the same files. Metric: unverified completions accepted.

## Experiment D (agent trials; prepared, not run)

Fixture: a small F# ledger solution (`fixtures/d/`), pinned as files; each run gets a
fresh `git init` copy.

| Task | Class | Requirements | Notes |
| --- | --- | --- | --- |
| T1 | low | LEDGER-T1-R1 | reject non-positive posting amounts |
| T2 | medium | LEDGER-T2-R1..R3 | atomic transfer, no overdraft, conservation |
| T3 | medium | LEDGER-T3-R1..R2 | idempotent period close; design decision DEC-T3-IDEMPOTENCY-KEY |

Prose acceptance criteria (`tasks/Tn/requirement.md`) are identical in both arms; their
sha256 is the observation's `acceptanceCriteriaDigest`. The treatment additionally gets
`tasks/Tn/contract.json` (`ecir/1`), which Ordo and Praxis must both admit. Hidden oracle
tests (`oracle/Tn/`) are never copied into a workspace.

- **Replicates:** 3 tasks x 2 arms x 2 replicates = 12 runs; minimum 6 eligible runs per arm.
- **Randomization:** seed `20261019`, `harness/d/randomize.py` (blocks = (task, replicate),
  block order shuffled, then arm order within a block). Resulting order:
  `T3-r2-baseline, T3-r2-treatment, T1-r2-baseline, T1-r2-treatment, T2-r2-treatment,
  T2-r2-baseline, T1-r1-baseline, T1-r1-treatment, T2-r1-treatment, T2-r1-baseline,
  T3-r1-treatment, T3-r1-baseline`.
- **Controls:** same model, configuration digest, tool set, 45-minute budget and at most
  3 completion attempts in both arms; cold cache (fresh session per run); 1 agent.
- **Metrics and sources:** tokens and cost from `praxis telemetry reliability-report` over
  the run's provider transcripts (`reports/<sha256>.json`); verified requirements,
  escaped defects from `harness/d/score.sh` (hidden oracle at the final commit);
  completion attempts and rejections from the run's `.ros/events/events.jsonl` (treatment)
  or `work complete` invocations (baseline); validate-runs from
  `work.validation.observed`; test runs from the harness `dotnet` wrapper log; rework =
  completion attempts beyond the first + reverted commits; elapsed time from the harness.
- **Exclusion rules (fixed now, before scoring):** X1 setup failure before the agent
  starts -> aborted, superseded by a rerun, not scored. X2 served-model mismatch -> pair
  excluded from paired comparison, both reported. X3 incomplete instrumentation ->
  excluded from token/cost comparisons only, never imputed. X4 oracle contamination ->
  excluded. X5 budget exceeded or agent gives up -> **failed, not excluded** (0 verified,
  ratio null).
- **Scoring oracle:** a requirement is verified when its oracle tests all pass at the
  final commit and the run recorded a completion; an escaped defect is a requirement the
  run recorded as completed whose oracle tests fail. Same oracle for both arms.
- **Analysis:** per-trial table; per-arm medians; paired difference per (task, replicate)
  block (treatment - baseline). A percentile bootstrap 95% CI (10,000 resamples, seed
  20261019) is computed **only if there are >= 6 eligible pairs**; otherwise the result is
  descriptive only and says so. With 12 runs, one excluded pair already makes D
  descriptive only. A, B, C are deterministic case tables with counts, no inference.

## Amendments

**A1 (2026-10-19, after A/B/C treatment binaries were downloaded, before any treatment case
ran).** The v3.15.0 tag points to `df6a8cbe23c2cd4d22980bded3cff4da2a0141cf` ("final checkpoint
and completion", the child of the `73f95ec` release commit registered above); asset
`praxis-linux-x64.tar.gz` sha256 `bf135fa626be82c3e5fc0c2220005ae87aacf93d427eaee45780cfde1d2336cc`,
checked against `native-checksums.txt`. It was published 2026-10-19T21:41Z, inside the
fallback deadline, so the fallback did not apply.

**A2 (2026-10-19, before any D trial).** D fixtures (`fixtures/d/`), contracts and harness were
authored after this preregistration and before any D trial; their digests are pinned per run
in `run.json` (`fixtureDigest`, `oracleDigest`, `acceptanceCriteriaDigest`). Contract digests
(Ordo and Praxis agree): T1 `sha256:d3984004...`, T2 `sha256:040a4e2b...`, T3 `sha256:d2dc5040...`.

**A2 (2026-10-19T23:00Z, after A/B/C results on Praxis 3.15.0, before any Experiment D trial).**
Experiment B (findings B5b, B6a) showed that contradictory decisions and unresolved conflicts reached
verified completion. The completion gate was re-evaluated to FAIL (condition O2), and the fix
REL-GATE-002 (ordo PR, praxis PRAXIS-REL-008) makes completion require execution *readiness*
for the completed requirements. Decisions in scope must be authorized by the **host authority
file** (`RequiredDecisionIds`), never by the agent's packet. The treatment binary therefore
changes from Praxis 3.15.0 to **3.16.0**, pinned by release asset sha256 once it is published.
Harness changes, applied to the treatment arm only, because the baseline (3.12.0) has no
authority input:
- `lib.sh`: the default authority authorizes the contract's decision nodes (`contract_decisions`),
  and `t_complete` cites each authorized decision with `--decision`.
- `fixtures/b/cases.json`: B1-valid now has `requiredDecisionIds: ["DEC-CONFIRM"]`. This is what
  makes it valid in the deployed protocol. Every invalid case keeps its original inputs and
  expectation.
- `d/setup.sh`, `d/smoke-agent.sh` and the agent brief: the authority authorizes the task
  contract's decisions, and the completion command cites them.
- `gate/scripts/gate-evidence-binding.sh`: the authority authorizes DEC-CONFIRM, and completions
  cite it.
Experiments A, B and C are re-run for the treatment arm on 3.16.0. The 3.15.0 results are kept,
not overwritten, as the pre-fix observation (the run ids differ). Hypotheses, metrics,
randomization, the D task set and the D order are unchanged.
