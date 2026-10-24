# EXP-2 phase 1: preregistration

**What it measures.** How many CI executions and CI job-minutes two verification-scheduling policies would have
avoided on recent Praxis and Dokimos main history, and which historical CI failures they would have missed (escaped)
or caught later (delayed). Requirements EXP-2-R1 and EXP-2-R2
(`.praxis/inbox/documents/2026-10-23-EXP-2-verification-scheduling-replay.md`); program `program/EXPERIMENTS.md` §3;
contract C5 (`program/CONTRACTS.md`); never-deferred gates `program/RELEASE-GATES.md` §2.

**Cost.** Zero. No LLM or provider call. Inputs are GitHub Actions run and job metadata, failing-job logs where a
failure needs classifying, and `git` history.

**Commitment.** This file, `maps/praxis.verification-map.json`, `maps/dokimos.verification-map.json` and
`data/*.window.txt` are committed and pushed before any counterfactual is computed. Results are reported whatever
they are. Any change after this commit is recorded in `RESULTS.md` as amendment A1, A2, … with its timing relative to
the data.

**What the experimenter had seen before this commit.** Workflow definitions, project files and git history of both
repositories; a blinded run listing (run id, workflow name, head SHA, creation time; no conclusions) used to fix the
windows. While checking API access, one run conclusion was displayed: Praxis validation run 40027886321 on the frozen
Praxis head `97048419` concluded `failure`. No other outcome was seen. The maps were not derived from outcomes.

## 1. Repositories and windows

| Repository | Frozen main head | Window (newest → oldest) | Size |
|---|---|---|---|
| kemiller2002/praxis | `9704841925ab8d2540bdc752f2aca7b3f3907cfd` | `97048419` (2026-10-23) → `c9f3a0dd` (2026-10-07) | 60 push-heads |
| kemiller2002/dokimos | `6c8554e89f3684c84fbd305fe9c78b4f0aa24a19` | `6c8554e` (2026-10-23) → `1a20900` (2026-09-26) | 60 push-heads |

- **Population.** The 60 most recent first-parent commits of main that have at least one `push`-event workflow run on
  `main`. These are the push heads: CI runs only on the head of each push. The full list is `data/<repo>.window.txt`.
- **Gaps.** First-parent commits with no push run are not in the population. In Praxis these are the `RELEASE-x-y-z`
  commits, which the release workflow pushes with its own token, so push workflows never ran on them. They are listed
  in the results, never replayed.
- **Changed files per push** are `git diff --name-status <previous push-head> <push-head>`, with renames on both old
  and new path. That is what the push contained.
- **Runs used.** Every `push`-event run on `main` whose head SHA is in the window, of every workflow, and every
  attempt. Jobs come from `list_workflow_jobs` with `filter=all`.

## 2. Maps (C5, `praxis.verification-map/0.1`)

`maps/*.verification-map.json` give path classes (globs), the jobs each class selects, a risk class per job, and the
`mandatory` set. They were derived from project references, embedded resources, the files tests and gate steps read,
and workflow path filters. Rules:

- **Mandatory, never deselected** (RELEASE-GATES §2):
  - Praxis: `Praxis validation / validate`. It carries `praxis validate`, which rejects credential and secret fields
    in telemetry, checks Aegis authorization boundaries and checks registry and frozen-state integrity. It also carries
    the architecture and registry checks and the "tests leave the checkout unchanged" step.
  - Praxis: `pinned-release-validate`, a producer/consumer contract.
  - Praxis: every `Native Praxis release` job (release acceptance).
  - Dokimos: every `Praxis validation` / `ROS validation` job.
  - Dokimos: every `Release` job.
- **Fallback rules.** A changed path that matches no path class selects every job. A historical job that matches no
  map entry is treated as mandatory.
- **Job level only.** A job follows its dependency with `follows`. Example: Dokimos `debounce` runs only when
  `build-test-gate` is selected.
- **Granularity caveat (Praxis).**
  - Praxis runs its whole F# suite inside `validate`, which is mandatory. Selection therefore operates at job level,
    and suites inside the mandatory job are never deselected.
  - The runner does support `PRAXIS_TEST_FILTER`. The matrix jobs already run one filtered suite per step, and they
    all depend on the same build closure (`Praxis.Tests` references every `src` project). A suite-level estimate inside
    those jobs would select the same suites as the job-level one, so none is made.
  - One estimate is exploratory: step-level savings if the mandatory `praxis validate` / `architecture` / `registry`
    steps were split out of `validate` (E1, §6).
- **Secret scan gap.** Neither repository has a dedicated secret-scan job. RELEASE-GATES §2.1 asks for one on every
  commit that adds files. The replay maps §2.1 to the nearest existing carrier above, and the results report the gap.

## 3. Policies

- **Baseline (H0).** What actually ran: every job of every attempt.
- **P-A: A1 dependency-aware selection on every push.**
  - Selected jobs: the mandatory set, plus each job whose `select_when` classes match a changed path (with the fallback
    rules above).
  - A job that did not run historically (path filter, `if:`) cannot be selected. P-A only removes jobs.
- **P-B: checkpoint scheduling.**
  - At a checkpoint push, every job that actually ran is kept (full CI).
  - At a non-checkpoint push, only the mandatory set runs ("cheap checks"). P-B applies no path selection.
- **Checkpoint** (operational, from git only). A push-head is a checkpoint if any of these holds:
  1. it is a two-parent commit whose subject starts `Merge pull request #` or `Merge PR #` (a PR merge);
  2. it is a single-parent commit whose subject ends `(#N)` (a squash merge);
  3. it changes the release version: Praxis `release.json` `"version"`; Dokimos `<Version>` in
     `Directory.Build.props`;
  4. it carries a release tag (`v*` or `dokimos-v*`).

  Every other push-head is a non-checkpoint (direct push).

## 4. Metrics

- **CI job-minutes.**
  - Per job, `completed_at − started_at`, summed over all attempts. Jobs that were skipped or never started count 0.
  - Cancelled jobs count their elapsed minutes, because that time was spent.
  - Secondary measure: GitHub-billable-weighted minutes, with Linux ×1, Windows ×2 and macOS ×10, OS taken from the
    job's runner labels.
- **Minutes avoided by a policy.** The sum over deselected job instances.
- **CI executions avoided.** Workflow runs in which the policy deselects every job, plus the job-instance count.
- **Outcome per (commit, job).** The conclusion of the job's latest attempt on that commit (across all runs of the
  workflow on that SHA). Conclusions `success`, `failure`, `cancelled`, `skipped`, or absent.
- **Failure episode.**
  - An episode is a maximal run of consecutive window commits (oldest → newest) on which job `j` concluded `failure`.
  - Commits where `j` has no `success`/`failure` outcome are transparent: they neither extend nor break an episode.
  - Its start is the first failing commit, and its failing step (from the jobs API `steps`) is recorded.
  - Failures in an earlier attempt that a later attempt on the same SHA turned into `success` are not episodes. They
    are listed as rerun-flaky incidents.
- **Detection of an episode by a policy.**
  - At commit `c'` the episode is detected if the policy runs `j` at `c'` and `j` failed there.
  - It is also detected if the policy runs another job that failed at `c'` at a step mapped to the same check
    (`checks` in the map).
  - Detection is looked for from the episode's first commit onward.
- **Delay.**
  - In commits: index of the detecting commit minus the episode start.
  - In checkpoints: the number of checkpoint commits in (start, detecting commit]. Detection at the start commit is
    0, and detection at the next checkpoint is 1.
- **Escaped episode.** Not detected at or before the first checkpoint at or after its start (the "next merge or
  release"). An escaped episode that some later executed run does detect also gets a delay, reported for H2.
- **Censoring.**
  - An episode whose horizon checkpoint has no observable outcome for `j`, or that starts after the last checkpoint in
    the window, is *unresolved*.
  - It counts as escaped for H1 (conservative) and is listed separately.
- **Delayed episode.** Detected, but not at its start commit.

## 5. Hypotheses and evidence classes

- **H1.** A policy saves ≥ 30% of CI job-minutes against the baseline on the window, with 0 escaped episodes.
  - Tested for P-A and P-B separately, per repository and pooled.
  - Primary escape count is strict: every episode counts, flaky or not. The secondary count excludes episodes
    classified flaky.
- **H2.** The median detection delay over all failure episodes is ≤ 1 checkpoint, per policy, pooled.
  - Episodes detected at their start contribute 0.
  - Episodes never detected in the window contribute +∞.
- **Evidence class per hypothesis and policy.** Uses the program's vocabulary:
  - **Demonstrated:** holds pooled and in both repositories, with ≥ 5 failure episodes pooled.
  - **Preliminary:** holds pooled but fails in one repository, or holds everywhere with < 5 pooled episodes.
  - **Contradicted:** fails pooled, meaning minutes saved < 30% or ≥ 1 escaped episode (H1), or median > 1 (H2).
  - **Inconclusive:** no failure episode at all in the window, for the escape part of H1 and for H2.

## 6. Exploratory (not hypotheses)

- **E1.** Praxis only. Job-minutes P-A would save if the mandatory steps of `validate` (checkout, setup,
  `praxis architecture check`, `praxis registry check`, `praxis validate`, alias check) ran as their own job and the
  build/test steps were selectable like the matrix jobs. Estimated from step timestamps.
- **E2.** P-A and P-B combined: path selection at non-checkpoints, full CI at checkpoints.
- **E3.** Billable-weighted minutes for every policy.

## 7. Flaky failures

Every failure episode is classified. No episode is discarded, and classification never removes an episode from the
primary H1 count. The classes:

- **rerun-flaky:** a later attempt or run of the same job on the same SHA succeeded;
- **environmental:** the failing-job log (or the failing step) shows runner, network, toolchain-download or
  service-outage causes. The same failing step also failed on commits whose changed paths are disjoint from the job's
  selection, or on unrelated commits;
- **defect:** anything else.

Logs are read only for failing jobs, and only to classify.

## 8. Reporting

`RESULTS.md` will report:

- per-repository and pooled numbers for both policies;
- every escaped and every delayed episode individually, with commit, job, failing step and why the policy skipped it;
- every rerun-flaky incident;
- the gap list;
- unknown jobs;
- amendments;
- evidence classes;
- limitations, including that the replay cannot see defects historical CI also missed, that the commits were authored
  under always-run CI, and that the maps are the experimenter's.

Raw run and job JSON is committed under `data/`. Tokens and log bodies are not; only the classification excerpts
are.
