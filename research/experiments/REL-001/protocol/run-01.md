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

None at registration.
