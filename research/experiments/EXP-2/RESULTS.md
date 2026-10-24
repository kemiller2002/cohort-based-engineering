# EXP-2 phase 1: results

**Protocol.** `PREREGISTRATION.md`, the two maps and the window files were committed and pushed in `80973f5`
("EXP-2 phase 1: preregistration") before any run conclusion was fetched or any counterfactual computed.

**Cost.** Zero. No LLM or provider call was made.

**Reproduce.** From `research/experiments/EXP-2/`:

```
python3 -I harness/fetch.py    # data/<repo>.runs.json, data/<repo>.jobs.json
python3 -I harness/replay.py   # results/replay.json
```

`replay.py` is deterministic: two runs give byte-identical output. It needs local clones of praxis and dokimos with
`main` fetched to depth 400.

**Data.**
- Praxis: 168 push-to-main workflow runs and 686 job instances (all attempts).
- Dokimos: 144 runs (143 with jobs; see A3) and 269 job instances.
- Logs of the 21 failing jobs were read to classify failures. Only short excerpts are committed, in
  `data/failure-classes.json`.

## 1. Windows

| Repository | Replayed push-heads (newest → oldest) | Checkpoints / direct pushes | Excluded first-parent commits |
|---|---|---|---|
| praxis | `97048419` (2026-10-23) → `e9d3390c` (2026-10-07), 60 | 55 / 5 | 26: the `RELEASE-x-y-z` release and final-checkpoint commits, pushed by the release workflow, with no push CI |
| dokimos | `6c8554e` (2026-10-23) → `4e22cb1` (2026-09-26), 60 | 34 / 26 | 2 (`2aba16f`, `d181958`): no push run of their own (each reached main in the same push as the following commit) |

- **Checkpoint reasons.**
  - Praxis: 50 PR merges and 5 squash merges. 13 of them also bump `release.json`.
  - Dokimos: 30 PR merges and 4 squash merges. 7 of them also bump `<Version>`.
  - No release tag points at a window commit.
- **Direct pushes.**
  - Praxis: 5 docs and licence commits (`c0ab2425`, `0656834b`, `609541c2`, `11bcaa7e`, `cfdaa2f7`).
  - Dokimos: the 2026-09-26/27 development burst plus 4 docs and licence commits.
- **Unknown jobs:** none. Every historical job matched a map entry.
- **Unmapped-path fallback (full selection).**
  - Praxis: 1 push (`tests/fixtures/telemetry/work-start-task-execution.json`).
  - Dokimos: 4 pushes (`.dokimos/accept-next-baseline`, `.github/copilot-instructions.md`).

## 2. Cost

Job-minutes are wall-clock runner minutes, summed over all attempts. Weighted minutes use Linux ×1, Windows ×2 and
macOS ×10.

| | Baseline min | P-A min (saved) | P-B min (saved) | P-A∘P-B (E2) min (saved) |
|---|---|---|---|---|
| praxis | 3696.7 | 2933.0 (763.7, **20.7%**) | 3375.4 (321.3, **8.7%**) | 3436.3 (260.4, 7.0%) |
| dokimos | 1092.1 | 710.3 (381.8, **35.0%**) | 1000.4 (91.6, **8.4%**) | 1042.1 (50.0, 4.6%) |
| pooled | 4788.8 | 3643.3 (1145.5, **23.9%**) | 4375.8 (412.9, **8.6%**) | 4478.4 (310.4, 6.5%) |

| | Weighted saved: P-A | Weighted saved: P-B | Workflow runs avoided: P-A | Workflow runs avoided: P-B | Job instances avoided: P-A | Job instances avoided: P-B |
|---|---|---|---|---|---|---|
| praxis | 28.1% | 11.9% | 11 / 168 | 6 / 168 | 145 / 686 | 56 / 686 |
| dokimos | 35.0% | 8.4% | 38 / 143 | 29 / 143 | 95 / 269 | 39 / 269 |
| pooled | 28.7% | 11.6% | 49 / 311 | 35 / 311 | 240 / 955 | 95 / 955 |

**Where the minutes come from.** From `saved_minutes_by_entry` in `results/replay.json`.

- **Praxis, P-A.** Of the 763.7 minutes saved, 574.2 are `worker-checklists`, 102.4 `local-worker-portability`, 78.2
  `lifecycle` and 9.0 the site deploy.
  - The mandatory `validate` job alone is 1188.8 minutes, 32% of the baseline, and is never deselected.
  - 34 of the 60 pushes touch the CLI or test closure, so the matrix jobs are selected there.
  - Only 9 pushes are governance/docs-only.
- **Dokimos, P-A.** Of the 381.8 minutes saved, 254.0 are `Deploy site / build`, 90.5 the CI `debounce` job, 20.4
  `build-test-gate`, 9.9 the Pages deploy and 7.1 `action-install`.
  - Both the debounce job and the deploy build begin with `sleep 600`. Most Dokimos savings are therefore idle runner
    time, not computation.
- **E1 (Praxis, exploratory).**
  - The F# and browser suites would also be skipped on pushes where P-A deselects the test closure if the mandatory
    steps of `validate` (`praxis validate`, `registry check`, `architecture check`, alias check) ran in their own job.
    That saves a further 278.8 minutes: Praxis P-A becomes 28.2% and pooled P-A 29.7%.
  - This is an estimate: it keeps the build step in the split-out job.

## 3. Failure episodes

There are 6 episodes, all listed. No rerun-flaky incident exists in the window: no job failed in one attempt and
passed in a later attempt on the same SHA.

| # | Repo | Job | Episode commits (start → last) | Start pushed as | Failing step and cause | Class |
|---|---|---|---|---|---|---|
| 1 | praxis | `Praxis validation / local-worker-portability (windows-latest)` | `4a6c8d1f` (1 push) | checkpoint (PR #236) | Durable output spool: "a seal preceding a failed exit append waits for independent journal reconciliation" | defect (Windows timing flake suspected, not shown: no rerun) |
| 2 | praxis | `Praxis validation / validate` | `2f4ce68e` → `97048419` (4 pushes, window end) | checkpoint (squash #282) | F# tests: "git status: outside a repository…", "fence release … millisecond timestamps" | environmental: `ubuntu-latest` moved 24.04 → 26.04 between `64005151` and `2f4ce68e` (a one-file `.praxis/` change) |
| 3 | dokimos | `CI / build-test` | `4e22cb14` → `404dacae` (2) | direct push | Test: `FSharpQualityTests.quality analyzer preserves indicators…` | defect |
| 4 | dokimos | `CI / build-test` | `f9eee0ef` → `0e1f2438` (6) | direct push | Build: FS0025 incomplete match (`CanonicalComparison.fs`), then FS3261 nullness (`Program.fs`) | defect |
| 5 | dokimos | `CI / build-test` | `6b98194e` → `2887e2f7` (6; spans checkpoints `79dc850a` #3 and `2887e2f7` #4) | direct push | Compare with accepted snapshot: `NotSupportedException` (F# union serialization) | defect |
| 6 | dokimos | `Deploy site / build` | `41e721fd` → `6c8554e8` (3, window end) | checkpoint (squash #48) | Site quality gate: "Playwright does not support chromium on ubuntu26.04-x64", after all site tests passed | environmental: the same runner image change as #2 |

### 3.1 Detection per policy

| # | P-A | P-B | P-A∘P-B |
|---|---|---|---|
| 1 | detected at start (selected: `src/` changed) | detected at start (checkpoint) | at start |
| 2 | detected at start (mandatory) | detected at start (mandatory) | at start |
| 3 | detected at start (`src/`, `tests/` changed) | **ESCAPED**: both pushes are direct pushes, `build-test` is not mandatory, and the failure was fixed (`b52ad0a7` passed) before the first checkpoint `79dc850a` | at start |
| 4 | detected at start | **ESCAPED**: six direct pushes, fixed by `d54420d1` before checkpoint `79dc850a` | at start |
| 5 | detected at start | **DELAYED**: 4 commits, 1 checkpoint (first seen at checkpoint `79dc850a`) | at start |
| 6 | **ESCAPED**: the three pushes change only `governance_and_docs` paths, so no path selects `Deploy site / build`. It is not mandatory, and nothing else ran the failing check. No later window push selects the job | detected at start (checkpoint) | at start |

### 3.2 Sensitivity (A3): a failure outside the job-episode model

Dokimos run 36268875495 (`.github/workflows/ci.yml`, conclusion `failure`, zero jobs) is the CI workflow file
failing to load at `86f358d7` (direct push). The next push, `46c83856`, "Fix CI permissions for authorized baseline
promotion", fixed it.

- **P-A** would have run CI there (`ci.yml` is in `dotnet_closure`), so it detects this failure at its start.
- **P-B** would not have run CI (direct push, CI not mandatory), so the failure escapes.

Counted with the episodes, P-B has 3 escapes and P-A still 1.

## 4. Hypotheses

| | H1 per repo (praxis / dokimos) | H1 pooled | H2 median delay (praxis / dokimos / pooled) |
|---|---|---|---|
| **P-A** | 20.7%, 0 esc / 35.0%, **1 esc** | 23.9%, **1 escaped** (strict). Excluding flaky/environmental: 0 | 0 / 0 / **0** checkpoints |
| **P-B** | 8.7%, 0 esc / 8.4%, **2 esc** | 8.6%, **2 escaped** (strict and excluding flaky/environmental) | 0 / ∞ / **0.5** checkpoints |

| Hypothesis | Policy | Class | Basis |
|---|---|---|---|
| H1: ≥ 30% fewer CI minutes with 0 escaped | P-A | **Contradicted** | Pooled 23.9% < 30%, and 1 escaped episode (#6). Only Dokimos clears 30%, and it is the repository with the escape. With the E1 split, pooled savings would be 29.7%, still short |
| H1 | P-B | **Contradicted** | Pooled 8.6% and 2 escaped episodes (#3, #4), both genuine build/test defects |
| H2: median delay ≤ 1 checkpoint | P-A | **Demonstrated** (by the preregistered rule) | 0 in both repositories and pooled, over 6 episodes (≥ 5). The margin is thin: 6 episodes from 5 distinct causes |
| H2 | P-B | **Preliminary** | Pooled 0.5 ≤ 1 and Praxis 0, but the Dokimos median is ∞ (2 of its 4 episodes are never detected) |

## 5. What the data says

- **P-A's savings.** Selection saves about a quarter of CI minutes on these windows. The ceiling is set by job
  granularity. Praxis's whole F# suite rides inside the mandatory `validate` job, and most Praxis pushes touch the
  CLI closure. Splitting the mandatory checks into their own job (E1) is the largest single lever found; it would
  bring pooled savings to 29.7%.
- **P-A's one escape is environmental, not a code defect.** It is still an escape under the preregistered rule.
  - A runner-image change broke the Pages deploy on docs-only pushes. Path selection cannot see this kind of failure,
    because no changed path predicts it.
  - Any policy that skips by path will miss environment drift until something forces a run. In this window nothing
    forced one before the window ended.
- **P-B saves little here.** Almost every push to main is already a PR merge: 89 of 120 pushes are checkpoints.
- **P-B's escapes are real defects.** Both are on direct-push bursts (Dokimos 2026-09-26) that were fixed before the
  next checkpoint. Checkpoint-only CI on `main` hides exactly the red intervals that direct pushes create.
- **P-A∘P-B (E2) had 0 escapes and saved 6.5%.** It is the only policy with no escape on this data, at a quarter of
  P-A's savings.

## 6. Gaps found

- **No dedicated secret scan** runs in either repository's push CI. RELEASE-GATES §2.1 asks for one on every commit
  that adds files. The maps use `praxis validate` (telemetry credential and secret-field rejection) as the nearest
  carrier, and that is not a repository secret scan.
- **Praxis release commits** (26 in the window period) never receive push CI. The release workflow builds them, but
  its runs are `workflow_dispatch`, outside this replay.

## 7. Amendments

- **A1** (clerical, found while writing results, after the data):
  - PREREGISTRATION §1's table named the diff-base commits (`c9f3a0dd`, `1a20900`) as the oldest window commits.
  - The oldest replayed push-heads are `e9d3390c` and `4e22cb1`, as the committed `data/*.window.txt` files (which
    the protocol names as governing) state.
  - No effect on any number.
- **A2** (harness defect, fixed after the first replay output was seen, before this report):
  - The detection scan continued past an episode's last failing commit, so a later, separate episode of the same job
    could count as detecting an earlier one.
  - It now scans only the episode's span, as §4 defines detection: the policy runs the job and the job failed there.
  - Effect: P-B Dokimos episodes #3 and #4 changed from "delayed 22 and 17 commits" to escaped. Pre-fix P-B pooled:
    0 escaped, 3 delayed. P-A was unaffected.
- **A3** (after data): the zero-job workflow-file failure in §3.2 is outside the preregistered job-episode model. It
  is reported as a sensitivity and not added to the primary counts.
- **A4** (naming): exploratory E2 (P-A at non-checkpoints, full CI at checkpoints) is reported as `P-A∘P-B`, `P-AB`
  in `replay.json`.

No map, window, metric or threshold was changed after the preregistration commit.

## 8. Limitations

- **Replay cannot see defects that historical CI also missed.** "0 escaped" means none of the failures CI actually
  observed would have been missed. It says nothing about defects no job checks.
- **Behaviour was not counterfactual.** Every commit was authored under always-run CI.
  - Under P-B, the Dokimos direct-push burst might not have happened, or might have been fixed differently.
  - Under P-A, an author would not have seen red CI on docs pushes.
  - Concurrency cancellations and debounce timing are replayed as they happened, not re-simulated.
- **The maps are the experimenter's.**
  - Each was derived from structure before outcomes, but other defensible maps exist. One example: making
    `Deploy site / build` mandatory or `always` would have removed P-A's escape and cut Dokimos savings by about
    264 minutes.
  - Praxis tests resolve the repository root at run time. The map assumes the filtered matrix suites do not read
    governance and docs paths; that was not verified test by test.
- **Few failures.**
  - There are 6 episodes from 5 causes. Two environmental episodes share one runner-image change at the end of both
    windows (right-censored: still red at the frozen heads).
  - Three Dokimos episodes come from one early-development day.
  - H2 "Demonstrated" for P-A rests on this small set.
- **Granularity is job level.** Suite selection inside the mandatory Praxis job is precluded by the mandatory rule.
  The filtered matrix suites share one build closure, so suite-level selection there would equal job-level selection
  (PREREGISTRATION §2).
- **Minutes are wall-clock runner minutes.** They include idle `sleep 600` debounce time in Dokimos and the elapsed
  time of cancelled jobs. They are not billing records.
- **Flaky classification has limits.** No job was rerun in the window, so rerun-based flakiness could not be
  observed. Episode #1 stays a defect under the preregistered rule, although a timing flake is plausible.
