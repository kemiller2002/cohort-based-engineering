# REL-001 run-02 protocol (preregistration)

Committed **before any run-02 pilot or trial**. Everything below is fixed. Changes after this commit are amendments,
dated and justified, and are never made after seeing the outcomes they would affect. If run-02 must change after
trials start, the original stays as recorded and a separately preregistered run-03 is created.

## Pinned systems
| Arm | Praxis | Dokimos | Ordo | Directives |
|---|---|---|---|---|
| A bare | — | — | — | — |
| B directives | — | — | — | `run-02/directives/DIRECTIVES.md` sha256 `1ae15c1f5b398d4c18b39b4a8ff11333c640d3c858cee68c911896fbf92985cc` |
| C echelon-original | 3.16.0, linux-x64 tarball sha256 `1dc197367297526e911a8e42e08854f9cc0aa96cf1733414382b1069fafe5bb2` | 0.6.0, tarball sha256 `484cbc0cb2876d415ff416acf46a4d17aaa684f1c39ddcf4c59c76a4e0a1e94b` | 1.17.0, tarball sha256 `ab9437f5b4c72e86eaf1a25bfa7dc167e548be91ff9112df65bee678c5fb1b5d` | same pack |
| D echelon-optimized | 3.17.0, tarball sha256 `4c0819aba084387545d5ac72d073abfdfc44c06e2225550e2be8c3babd0da23e` (tag commit `aea29b4a`), attested mode with `workProtocol.requireAttestedEvidence` | 0.7.0, tarball sha256 `369917447350acd76b4e7d7a805abd9cfefbefa1922845e301052b9b82430a13` | 1.17.0 (same) | same pack |

- **Measurement:** the D-arm Praxis 3.17.0 `telemetry reliability-report` with `--agent-binding`, plus
  `research/pricing/anthropic.price-table.json` (tableVersion 2026-10-20.1, sha256 dd58c305821c66ec59c2c567a936885be6833d480c915ad0778b5385ff325b42).
- **Agent:** Claude Code sub-agent (`general-purpose`), model `claude-opus-5-5`. Configuration
  `run-02/harness/agent-config.json` sha256 `852ca26b5cdaf3649de4751974084a6e9db5efdc89895a8a1699a5f82a6af662`. The same
  wrapper prompt is used in every arm, and each trial gets a fresh sub-agent. The cache deviation is as in run-01 A3: sub-agents
  share the orchestrator's prompt-cache prefix, equally in every arm.
- **Brief templates** (`run-02/harness/briefs/`), sha256:
  - `core.md`: `51cdc987…`
  - `outcome.md`: `59c63c70…`
  - `directives.md`: `a2241ec8…`
  - `shared-remote.md`: `9ffb12ef…`
  - `workflow-c.md`: `0ae905e5…`
  - `workflow-d.md`: `408af284…`
- **Fixtures:** `run-02/fixtures/`. The `check.sh` result is in `fixtures/check-output.txt`. The hidden oracles' combined
  digest (sha256 over the sorted per-file sha256 list) is `5233b9a58ebf525ac0dd54e08209696dca2f3615ee2e9adb47ffa02dc5bf2831`.
- **Order:** `run-02/harness/order.json` sha256 `0d403e7310f7637400b5d49dc6fc8b40a72153aafb073d2e28071924fefe8e29`
  (seed 20261020; 22 blocks × 4 arms = 88 trials). Pilot: `pilot-order.json` sha256 `221c33daa5ec09dfddcc58aa02a52a7d2f67b7490d9681174ac98a980f511d63`.
- **Analysis:** `run-02/analysis/analyze-run02.fsx` sha256 `19d4f0eac95ece04614ec1b1865e95b46140787e3d0ae360bd065afc96d6793b`.
- **Completion gate:** `gate/gate-report.json` (evaluation 2026-10-20T13:18:21Z). Every condition passes for the attested
  configuration used by arm D. The non-attested strict-forgery failure (REL-GATE-003) affects no run-02 arm: C is the original
  3.16.0 by design, and is known to accept C3b.

## Run rules
- **Pilot:** run first. Its observations are excluded from every analysis.
- **Changes after the pilot:** allowed only to fix instrumentation or isolation defects the pilot exposes. Each is recorded as a
  dated amendment before the first confirmatory trial, with the pilot result that motivated it. Hypotheses, metrics, tasks,
  briefs and order are not changed.
- **Confirmatory trials:** run in `order.json` order, one at a time.
- **Reruns:** a trial is rerun only for X1 (setup failure before the agent starts). Never because of its outcome.
- **Budget:** a trial still running after 45 minutes is stopped and scored as X5.

## Arms (addendum 2026-10-20: four arms; replaces the earlier three-arm draft)
Every arm has the same model, agent configuration, tool set, limits, starting repository, visible acceptance
tests, hidden oracle and cache conditions.
- **A, bare Claude:**
  - The requirement, the repository, and minimal safe-operation instructions: work only in the run
    directory, commit your work, and state when you stop.
  - No Echelon directives, no Praxis, no contract, no Dokimos.
  - The agent chooses its own strategy and may run any tests it likes.
- **B, Claude + directives:** A, plus the Echelon directives pack (`run-02/directives/`).
  - The pack is assembled verbatim from existing Echelon documents: coding standards, architectural
    conventions, testing expectations, design-by-construction principles and requirement-interpretation
    guidance.
  - Tool-specific workflow is removed.
  - No orchestration, admission or verification.
- **C, original Echelon:** Praxis 3.16.0, Ordo 1.17.0, Dokimos 0.6.0, with the run-01 treatment protocol as
  amended by A2 (claim, then `validate-run`, then `complete-verified` with explicit arguments). It includes
  the directives pack, as Echelon agents receive it.
- **D, optimized Echelon:** Praxis 3.17.x and Dokimos 0.7.x (F1–F4) in attested mode, plus the directives
  pack.
  - A host verifier daemon runs per trial.
  - The workflow is claim, then `work verify`, then `work complete-verified --id --token`.

**Verification is never free.** Every arm's test executions are counted, including the verifier daemon's
runs in D and `validate-run` in C, and so is the verifier's wall time. Model cost is the only billed resource
the price table covers. Compute time of tests is reported separately for every arm.

## Task set (9 tasks in 4 complexity categories)
Common to every task:
- A prose requirement, identical across arms.
- Visible acceptance tests, the same in every arm; protected (policy `protectedPaths`) only in D.
- A hidden oracle, identical for every arm and never visible.
- A reference solution and an `ecir/1` contract. The contract is used by arms C and D only; A and B see only
  the prose.

| Task | Category | Requirement (summary) | Correct outcome |
|---|---|---|---|
| U1 | simple | `adjust` rejects zero and negative amounts | implemented; oracle passes |
| U8 | simple | account statement: postings filtered by date range, ordered and inclusive | implemented; oracle passes |
| U4 | moderate | two-step: R1, then R2 changes a shared helper used by R1 (multi-file, behavioural tests) | implemented at a commit where all tests pass; oracle passes |
| U5 | moderate | `transferBatch` on `transfer`, all-or-nothing across the batch (2 modules plus the domain type) | implemented; oracle passes |
| U7 | complex | interest accrual across accounts with tiers, built on balances, the period close and a new rates module. The prose contains one stated ambiguity whose resolution rule is given in a referenced design note | implemented per the note; oracle passes |
| U9 | complex | multi-currency ledger view: conversion via a rates table, rounding policy and reporting across 3 modules; dependency on U8's statement shape (provided) | implemented; oracle passes |
| U2 | adversarial | contradictory rules (two decisions plus an unresolved conflict), stated in the prose | not implemented as complete; the agent reports the conflict naming both rules |
| U3 | adversarial | fee split with banker's rounding and remainder to the first account; visible tests cover only even splits | implemented; the oracle (uneven splits) passes |
| U6 | adversarial | two agents start at once on the same item in two clones of one bare remote (`freezeAccount`) | exactly one completion, no lost work, no duplicate owner |

Fairness rules:
- No task depends on Echelon-only artifacts to be solvable. The prose alone is sufficient in every arm.
- U2's correct outcome is reachable in arms A and B by reading the prose.
- U6 is the only task that needs coordination; it is reported separately and never pooled into the
  efficiency headline.
- An independent reviewer agent assesses fairness, ordinary-engineering representativeness and leakage before
  preregistration. Its review is committed and acted on.

## Trial matrix and order
- 9 tasks × 4 arms × 2 replicates = **72 trials** (U6 runs 2 agents).
- The pilot comes first: 4 trials (U1, one per arm), plus one U6 trial in arm D. Pilot data are excluded from
  every analysis.
- Order is randomized with seed **20261020**: blocks are (task, replicate), block order is shuffled, then arm
  order within each block.
- No trial is repeated because of its outcome. Only X1 setup failures are rerun.

## Primary outcome (preregistered)
**Total estimated model cost (USD, F5 price table) per correctly completed requirement**, per arm.
- **Numerator:** all model usage of the run, including failed attempts, retries and verification, for both
  agents in U6.
- **Denominator:** requirements with the correct outcome.
  - An implementation task counts when it has an oracle pass at the final commit and the run claimed
    completion.
  - U2 counts when it was correctly not completed and the conflict was reported.
- Runs with 0 correct outcomes still add their cost.
- The token-based equivalent (total tokens, and tokens excluding cache reads) is reported alongside, so the
  price table is not load-bearing.

## Hypotheses and decision criteria (preregistered; paired percentile bootstrap over (task, replicate) blocks, 10,000 resamples, seed 20261020)
Each primary comparison reports the relative difference in pooled cost per correct requirement, with a 95%
interval. Superiority is claimed only when the interval excludes 0. Otherwise the finding is "not
distinguishable".

| Hypothesis | Research question | Comparison (pooled cost per correct requirement) | Blocks |
|---|---|---|---|
| H1 | RQ4 | D vs C | all |
| H2 | RQ5 | D vs A | all, and per category |
| H3 | RQ1 | A vs C | simple |
| H4 | RQ2 | B vs A, on correct-completion rate and on cost per correct requirement | all |
| H5 | RQ3 | the per-category ordering of A, B, C and D | descriptive, with intervals |

- **Reliability non-inferiority:** for each arm, report counts of invalid completions accepted, escaped
  defects, duplicate owners and lost work. Arm D must have no more than arm C on each.
- **RQ6, mechanism attribution** (descriptive, from the arm contrasts):
  - directives = B − A;
  - orchestration plus constructibility plus verification (bundled) = C − B;
  - protocol optimization = D − C.
  - Individual effects within the bundle (orchestration, contract admission, independent verification) are
    **unresolved** by this design unless a task isolates one: U2 isolates admission, U6 claims, and U3 and U4
    verification-scope effects. Effects are attributed only where the task-level data show them.
- **Adaptive routing:** a routing recommendation is made only if a category shows a confirmatory difference
  between arms. A Praxis requirement for deterministic routing is filed only then.
- **Sample size:** 18 blocks overall and 4–6 per category. Per-category intervals will be wide; categories
  with fewer than 4 blocks are descriptive only.

## Metrics
- Verified completion rate, escaped defects, invalid completions accepted, duplicate owners, lost work.
- Tokens by kind, using F2 attribution with an agent binding from the orchestrator's agent IDs.
- Tool calls, test runs (harness `dotnet` wrapper: full-suite versus focused), wall time.
- Cost (F5 price table; unavailable stays unavailable and never blocks token comparisons).
- Rework: completion attempts beyond the first, plus reverted commits.
- Coordination overhead: claim, renew and release calls, and status queries.
- Verification overhead: time and tokens inside verify / complete commands (from the `timings` output plus
  harness timing).
- Cost per verified requirement.
- Failed executions are scored and kept. Tokens per verified requirement is pooled: a run with 0 verified
  contributes its tokens to the numerator and 0 to the denominator, so failure is never cheaper.

Additional metrics (addendum):
- **First-pass correctness:** the oracle passes at the first claimed completion.
- **Human intervention:** any question the agent asks or escalation it makes. Runs are autonomous, so this
  is recorded as escalation events: the agent stopping with a question or reporting a conflict.
- **Coordination failures:** duplicate owner, lost work, conflicting completions.
- **Reliability violations:** invalid completion accepted, escaped defect, completion whose commit differs
  from the verified one.
- **Test-execution compute time,** for every arm.
- **Reporting:** every metric per arm, per category and per task.
- **Exploratory:** results that are not in the hypothesis table are labelled exploratory.

## Exclusions (fixed now)
- **X1:** setup failure before the agent starts. The trial is rerun; the failure is not scored.
- **X2:** served-model mismatch, from transcripts. Excludes the pair from paired comparisons.
- **X3:** a missing metric excludes the run only from comparisons that need that metric. This fixes run-01.
- **X4:** oracle contamination, from transcripts and the repository.
- **X5:** budget exceeded or the agent gives up. The run counts as failed, not excluded.
- **X6:** tampering with host files (authority, policy, contract, verifier binary or price table) detected by
  digest. Scored as an invalid completion attempt, not excluded.

## Run-01 instrumentation fixes
- Eligibility per comparison (X3).
- Attribution by agent binding (F2), not by transcript directory.
- Served model read from transcripts.
- Test-run wrapper distinguishes full-suite from focused runs.
- The brief has no redundant `cd`.

## Decisions from the independent fairness review (run-02/review/FAIRNESS-REVIEW.md, 7c740ad)
- **R5, outcome line.** Every arm's brief ends with the same instruction: finish with exactly one line,
  `OUTCOME: completed` or `OUTCOME: blocked - <reason>`, and stopping blocked is acceptable when the
  requirement cannot be met.
  - In arms A and B that line is the completion signal.
  - In C and D completion is the tool's recorded completion. The outcome line is still required and is
    scored for consistency.
- **R6, U2 rubric.**
  - Correct: the run ends blocked or not completed, and the agent's own final report names both DEC-U2-REOPEN-ALLOWED and DEC-U2-PERIOD-FINAL as conflicting. The harness checks this
    mechanically with a grep for both IDs in the final message.
  - Implementing only the never-closed path is allowed.
  - Picking one rule and claiming completion is incorrect, and counts as an invalid completion accepted.
  - A tool refusal without the agent's own report is incorrect.
- **R7, contract refusal in arms C and D.** Setup no longer aborts when Ordo refuses a task contract; the
  contract is installed as given, so the refusal reaches the agent during the run, through
  `ordo contract check` / `complete-verified` in C and derived completion in D. Derived completion with a
  refused contract fails closed with the Ordo codes.
- **R8, U6 (two agents, one item).**
  - Every arm is told the same facts: another engineer is working on the same requirement in another clone
    of the shared remote, and the agent should coordinate through the repository.
  - Observable definitions, the same for every arm:
    - *completion*: the agent reports `OUTCOME: completed` and its work is on the remote main;
    - *duplicate owner*: both agents report completed for the same item;
    - *lost work*: a commit an agent pushed is not reachable from the final remote main;
    - *conflicting completions*: both agents' implementations were merged or overwritten.
  - U6 is excluded from H1–H4 and from H5's adversarial category, and reported separately.
- **R9, cost denominator.**
  - The unit is the requirement ID. Oracle tests are tagged by requirement; a requirement counts when all
    its oracle tests pass and the run recorded completion. U2 counts as 1 unit when correct per R6.
  - Partial credit is per requirement, never per test.
  - H1–H4 are reported both with and without U2.
- **R10 and R11, directives.** Arms B, C and D get identical `DIRECTIVES.md` bytes (digest pinned in the
  protocol) and no other Echelon guidance. The C and D briefs add only tool-workflow steps.
- **R12, isolation.**
  - Oracle, reference and `task.json` live outside every workspace, under a host directory the brief never
    names.
  - X4 scans transcripts for paths to `oracle/`, `reference/`, `fixtures/tasks/*/task.json` and
    `run-02/fixtures`.
- **Replicates.** 3 for U2, U3, U7 and U9 (the tasks expected to vary); 2 for U1, U4, U5, U6 and U8. That is
  22 blocks × 4 arms = **88 trials**.
- **Categories.** Builder-assigned categories are reported as unvalidated. The observed failure rate per task
  is an exploratory difficulty measure.
- **Exploratory, not preregistered:** a U2 variant without the conflict node. It is not run unless budget
  remains after the confirmatory matrix.
