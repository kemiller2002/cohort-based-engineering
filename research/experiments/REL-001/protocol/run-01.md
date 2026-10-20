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

**A3 (2026-10-20T01:10Z, after the gate re-evaluation on released Praxis 3.16.0, before any Experiment D trial).**
How the D trials are run, fixed before the first trial:
- **Pins:** treatment Praxis **3.16.0** (`praxis-linux-x64.tar.gz`, sha256
  `1dc197367297526e911a8e42e08854f9cc0aa96cf1733414382b1069fafe5bb2`). Baseline Praxis 3.12.0 and
  Dokimos 0.6.0 are unchanged.
- **Agent runtime:** each trial is one fresh Claude Code sub-agent (`general-purpose`, the same model
  and default tool set in both arms). The orchestrating session launches the trials one at a time in
  the preregistered order. The agent configuration is `harness/d/agent-config.json`
  (sha256 `60adeb4389807b0ef40d8ca2979103ae18869be2ed1539b9fbd60289b4c00e83`). The wrapper prompt is
  identical across arms apart from the run's `AGENT_BRIEF.md` path.
- **Deviation from "cold cache":** sub-agents of one session share the provider prompt cache for the
  common system-prompt prefix, so a trial is not fully cold. Both arms are equally exposed. Cache
  reads are reported separately from input and output tokens, and they are not compared as if they
  were fresh input.
- **X4 detection extended:** the hidden oracle is on the same disk as the workspaces. `score.sh` also
  marks a run contaminated when the agent's own transcripts reference the oracle directory or modules.
- **Budget enforcement:** the orchestrator records `logs/agent.json {startedAt, endedAt}`. A trial
  still running at 45 minutes is stopped and scored under X5 (failed, not excluded).

**A4 (2026-10-20T01:15Z, after the first D trial was scored and before any second trial or comparison).**
The first trial (T3-r2-baseline) showed that `praxis telemetry reliability-report` left every one of
the run's provider observations unattributed (`no-execution-for-session`). Sub-agent transcripts carry
the orchestrating session's ID, and the run's execution record has no session binding, so session-window
attribution (R3) cannot separate trials. Each run's `transcripts/` directory holds only that trial's
agent, so `score.sh` now counts every deduplicated observation the report finds there, attributed plus
unattributed, as the run's tokens. The values are Praxis's own measured sums; nothing is estimated.
Tool calls are counted as unique `tool_use` ids in the run's transcripts.
Transcript output tokens are a lower bound, because entries are written before streaming completes. The
orchestrator therefore also records the harness's per-agent figures in `logs/agent.json`
(`subagentTokens`, `toolUses`, `durationMs`) as a secondary measurement. That record is reported, never
substituted for the primary one. Trial 1 was re-scored with the same `score.sh` that scores every later
trial.

**A5 (2026-10-20T13:13Z, regression re-run on released Praxis 3.17.0, before the run-02 preregistration).**
Experiments A, B and C and the evidence-binding gate check were re-run with the treatment arm on released
**Praxis 3.17.0** (tag commit `aea29b4a`, `praxis-linux-x64.tar.gz` sha256
`4c0819aba084387545d5ac72d073abfdfc44c06e2225550e2be8c3babd0da23e`, checked against `native-checksums.txt`;
`praxis-bin` sha256 `a5ec4a14…`), **Dokimos 0.7.0** (`dokimos-linux-x64.tar.gz` sha256
`369917447350acd76b4e7d7a805abd9cfefbefa1922845e301052b9b82430a13`, checked against
`dokimos-checksums.txt`; source commit `04b5f856`) and **Ordo 1.17.0** (release binary, commit `bb43c26c`). The
baseline arm (Praxis 3.12.0) was not re-run. The 3.15.0 and 3.16.0 results are kept unchanged; the new
results are `results/<e>/treatment-v3.17.0.jsonl` and `results/<e>/summary-v3.17.0.json`.

Why the harness changed. Praxis 3.17.0 requires a clean worktree and `HEAD` = the verified commit at
completion, and keeps claims, validation results, receipts and claim-protocol events in the out-of-tree
store `<git-common-dir>/praxis/`. Only what those rules require was changed:
- `harness/lib.sh`: `count_events` reads the tracked log and the store log and takes, per event type, the
  larger of the two counts (the store log mirrors the tracked completion event under another eventId, so
  a sum would double-count; the first A run on 3.17.0 showed exactly that, 2 "verified" events for one
  completion, and was discarded). `REL001_TREATMENT_DOKIMOS` overrides the Dokimos path, and the recorded
  Dokimos version is read from the binary instead of the literal `0.6.0`.
- `harness/{a,b,c}/run.sh`: `REL001_RESULTS_TAG` names the output file (`<arm>-<tag>.jsonl`), so a re-run
  never overwrites a kept result. `harness/summarize.fsx a|b|c [TAG]` summarizes the tagged file.
- `harness/c/run.sh`: C3b's forger now copies and appends the forged `work.validation.observed` event to
  the store log, where 3.17.0 records validation events (it appended to the tracked log before). New
  attested-mode cases (run when the treatment Praxis provides `verifier serve`): a host verifier daemon,
  an authority pinning its key and the policy digest, `ros.json` `requireAttestedEvidence`:
  C8a C3b in attested mode, C8b a self-signed receipt (the genuine receipt's exact format, re-bound to the
  claim and HEAD, signed with an own key; `gate/scripts/forge-receipt.py`), C8c a genuine failing receipt,
  C8d a genuine passing receipt.
- `gate/scripts/gate-evidence-binding-v317.sh` (new; the original script is unchanged). The original is
  refused for every case on 3.17.0 with `PRX.COMPLETION.DIRTY_WORKTREE` because it leaves the authority and
  evidence files untracked inside the repository, so its refusals test nothing. The new script keeps host
  files outside the repository, commits cited evidence files before the verification revision and runs each
  case in a fresh repository. GATE-3 is now the forgery an agent can make on 3.17.0: a forged passed result
  in `<git-common-dir>/praxis/validations` plus a forged event in `<git-common-dir>/praxis/events.jsonl`;
  the original unrecorded shape is kept as GATE-3U. Attested variant: GATE-A1 (forgery as GATE-3), A2
  (self-signed receipt), A2B (own key under the trusted keyid), A3 (genuine failing receipt), A4 (genuine
  passing receipt). Output: `gate/evidence/evidence-binding-repro-v3.17.0.jsonl`.

Results (real counts):
- **A** (17 cases): 0 duplicate active owners, 0 stale completions accepted, 0 lost work; 17/17 match the
  prediction. A6a's second retry is now refused with `ARGUMENT_MISMATCH` (HEAD moved to the metadata commit)
  instead of being replayed; still exactly one completion.
- **B** (12 cases): 0 of 11 invalid accepted; B1-valid verified; 12/12 match.
- **C non-attested** (19 cases): 1 of 17 invalid accepted, **C3b** (forged result + forged event in the
  agent-writable store), as on 3.15.0 and 3.16.0. Every other invalid case is refused; several now with
  `ARGUMENT_MISMATCH` or `HEAD_MISMATCH` (the F3/F4 identity checks run before the evidence checks) instead
  of the earlier evidence code.
- **C attested** (4 cases): 0 of 3 invalid accepted (C8a `RECEIPT_MISSING`, C8b `RECEIPT_UNTRUSTED_KEY`,
  C8c `RECEIPT_NOT_PASSED`); C8d verified with completion identity `consistent`, only
  `.ros/events/events.jsonl` changed, worktree clean.
- **Gate check**: GATE-1, GATE-2 `EVIDENCE_UNRECOGNIZED`; GATE-3U `EVIDENCE_UNRECORDED`; GATE-4
  `EVIDENCE_NOT_PASSED`; GATE-5 verified; **GATE-3 verified (exit 0)**, contradicting the expectation that
  GATE-1..4 are rejected in non-attested mode. Attested: A1 `RECEIPT_MISSING` (derived path:
  `EVIDENCE_MISSING`), A2 `RECEIPT_UNTRUSTED_KEY`, A2B `RECEIPT_INVALID_SIGNATURE`, A3 `RECEIPT_NOT_PASSED`,
  A4 verified with clean completion identity.

The gate is re-evaluated in `gate/gate-report.json` from these results only (see there); conditions that
were not re-measured on 3.17.0 are marked as not re-run, never carried over as PASS. Hypotheses, metrics,
D tasks and the D order of run-01 are unchanged.
