# Track A2: Factory waste remediation prototypes (A2-001)

> Committed by RD-000 from A2-001's final hand-back text. The harness refuses subagent report-file writes (D-010). The worker's final commit is `8a9a1f4`.
>
> - **Outputs:** `experiments.json`, `findings.json` (A2-F-01..10), `CHECKPOINT.md`, `protocols/` (preregistrations plus disclosed amendments), `raw/`, and `tools/` (`ros-merge-driver/`, `replay/`, `verifier-timing/`, `failfast/`).
> - **Scratch:** under `/home/user/sprint-scratch/A2/`. No original repository was modified.
> - **Status:** everything is EXPERIMENTAL. Nothing was applied to a real repository.

## Summary

- **Merge driver for `.ros/` state (SPR-A2-01): VERIFIED for R8 and R10.**
  - A small F# driver resolved every `.ros/` state conflict in replays of all 86 two-parent R8 merges and the 34 conflicted R10 merges. That is 92 merges and 170 conflicted file paths; all now merge without conflict.
  - No record was lost or duplicated. The pinned `praxis validate` passes on all 92 driver results.
  - In one R10 merge the team's own resolution had dropped a live work item, and `validate` fails on that commit. The driver's result keeps the item.
- **The driver cannot remove application-code conflicts.** Nine replayed merges still need a person: 4 in R8 and 5 in R10.
- **Verifier rebuild (SPR-A2-02): SUPPORTED.**
  - The cold build is compile-bound, so a NuGet cache alone saves only about 4%.
  - Release v3.9.1 is 2 commits after the pin, with no changes under `src/`. Its signed bundle downloads in about 4.5 s, and its output is byte-identical to the source-built verifier in every case tested.
  - A cache keyed on the pinned commit is safe if the key is complete.
  - About 550 of roughly 604 CI minutes are avoidable (ESTIMATE).
- **Fail-fast ordering (SPR-A2-03): INCONCLUSIVE.** The saving is 23.7% of failed-run minutes under the preregistered "cheap gate" definition, but only 5.9% under a stricter one.

## SPR-A2-01: semantic `.ros/` merge driver

Preregistered at `3e11073`. Amendment 1 was added after the first replay.

### Prior state

- Praxis has `praxis work history merge --apply` (`docs/work-history-merge.md`, `src/Praxis.Domain/Work/HistoryMerge.fs`). It is run by hand after Git has stopped on a conflict, in an exclusive checkout.
- Praxis does not document any `.gitattributes` merge driver.
- In R8, agents made the merge commits locally (committer "Claude"), so a local driver would have run.
- R8's DEV-R8-08 records two things:
  - Praxis 3.24.0's resolver refused merges, citing "divergent identity actor" and "changed Git history".
  - The coordinator then fell back to an ad hoc rule: union work items by ID, keep the later `updatedAt`, and append theirs' new event lines after ours.

### Prototype

The pure merge logic is in `tools/ros-merge-driver/RosMerge.fs`. The Git driver wrapper is `ros-merge.fsx`, run via `dotnet fsi`. It follows Praxis's own merge rules:

| State | Merge rule |
|---|---|
| Work items (`current.json`) | Three-way merge by `id`. A record changed differently on both sides, or deleted, makes the driver refuse and leave a normal conflict |
| Events (`events.jsonl`) | Union by `eventId`, keeping the original line bytes |
| `updatedAt` | The later value |
| `actor` | Taken from the side with the later `updatedAt` (a preregistered policy choice) |

Tests: 26 F# unit tests and 5 harness tests pass.

### First version: strict ordering

- It resolved 16 of the 26 logged R8 PR merges.
- It refused 10, because ancestor events appeared in a different order on one side.
- 5 of those 10 were merges Git's plain text merge would have succeeded on, so the driver added conflicts that did not otherwise exist. That is a regression.
- **Cause:** the team's DEV-R8-08 fallback had already reordered older events on branches. Praxis's strict ordering rule does not fit these real histories (A2-F-05).

### Second version: relaxed ordering (post hoc, disclosed in Amendment 1)

- If the older events are all present and unchanged but in a different order, the driver writes ours' order followed by theirs' new events.
- It still refuses removed, rewritten, duplicated or divergent records.

### Results with the second version (MEASURED)

| Population | Merges | Result |
|---|---|---|
| R8 logged PR merges | 26 | 46 conflicted `.ros/` paths before, 0 after; 0 records lost, 0 duplicated |
| R8, all 86 merges | 26 clean | Still clean; no new conflicts |
| | 56 `.ros/`-only | All 56 fully resolved |
| | 2 mixed `.ros/`+app | `.ros/` part resolved; app files still conflicted |
| | 2 app-only | Unchanged |
| | R8 total | 105 `.ros/` paths before, 0 after; 0 refusals |
| R10 | 29 `.ros/`-only | All resolved |
| | 5 mixed | `.ros/` part resolved; app files still conflicted |
| | R10 total | 65 `.ros/` paths before, 0 after |

### Correctness against the team's actual merges

- **Records:** in all 168 R8 files, the record-ID set and every record's content equal the team's commit. R10 matches in 67 of 68 files; the exception is the team error below.
- **Byte-for-byte match:** in R8, `current.json` matches 32 of 84 and `events.jsonl` 76 of 84. The differences are only item or event order, plus the top-level `actor` field in 17 files.
- The team was inconsistent on these points: R10 mostly sorted items by ID and always kept ours' `actor`.

### `praxis validate`

Native release bundles, checksum-verified: 3.24.0 for R8, 3.25.0 for R10.

| Rehearsal | Team commits pass | Driver results pass |
|---|---|---|
| R8 | 58/58 | 58/58 |
| R10 | 33/34 | 34/34 |

- The failing team commit is R10 `d8447ed1` (SL-T12 into SL-T19). It kept one side of `current.json`, dropped the active work item WI-0003, and fails `validate`. The driver's result keeps WI-0003 (A2-F-03).
- **Checking `validate` itself:** it detects a deleted work item and deleted events. It does **not** detect a duplicated event line, so the harness's own duplicate check is the only guard against that.

### Other rehearsals

- R3 (3 conflicts) and R5 (15 conflicts) conflict only in application files.
- R1, R2, R4, R6, R7 and R9 have no merge conflicts.

### Application-code conflicts (Director update D-019)

**A `.ros/` driver cannot remove these.** They still need a person:

| Rehearsal | Files still conflicted |
|---|---|
| R8 | `.github/workflows/live.yml`; Classify.fs, GitHubRequests.fs and StatefulFake.fs; Program.fs; INV22.fs |
| R10 | InvestigationList.fs with investigation-list.html (3 merges); Classify.fs with GitHubRequests.fs (2 merges) |

Share of conflicted merges made conflict-free: R8 56 of 60 (93%); R10 29 of 34 (85%).

### Replay artifact found and fixed

- The local R8 clone was shallow. One merge (`538eab03`, PR #1) therefore had no common ancestor, which looked like lost records.
- I unshallowed the scratch clone from GitHub (read-only) and re-ran all 86 merges.
- `raw/replay-r8-all86-unshallow-v2.jsonl` is the authoritative file. The earlier shallow-clone file is marked SUPERSEDED.

### Limitations

- The driver works per file, so it cannot tie both history files to the same commits the way Praxis's resolver does.
- It applies only to local merges, and each clone needs it registered in `.git/config`; `.gitattributes` alone is not enough. GitHub's merge button does not run custom drivers.
- `dotnet fsi` startup makes each merge take a median of 6–8 s. A compiled driver was not tested.
- Some merges had several common ancestors. Git built a combined ancestor, and the driver still succeeded.
- For scale: Track A found agents spent 1,537 s handling the 26 logged conflicts.

## SPR-A2-02: verifier rebuild cost

Preregistered at `300ccae`.

### How CI builds the verifier

1. Each rehearsal's `echelon-foundations.yml` calls `praxis/.github/workflows/foundations-verify.yml` at a pinned commit: `aa7c7ca6` in 8 rehearsals, `398af6dd` in R6.
2. That job checks out Praxis and runs `actions/setup-dotnet`.
3. It builds with `dotnet build src/Praxis.Cli/Praxis.Cli.fsproj -c Release`, with no cache.
4. It then runs `dotnet praxis.dll foundations verify --json`.

### Local timings

MEASURED, n=3 each, using the exact CI command, on a shared host at load average 7–11 with 4 vCPU.

| Mode | Runs (s) | Median (s) |
|---|---|---|
| Cold (fresh tree, empty NuGet cache) | 93.0, 93.1, 93.3 | 93.1 |
| Warm NuGet cache, fresh tree | 94.3, 84.2, 89.4 | 89.4 |
| Incremental (same tree, no change) | 5.8, 4.6, 4.2 | 4.6 |
| Release fetch (v3.9.1 linux-x64, 37 MB: download, checksum, extract) | 3.0, 4.5, 4.7 | 4.5 |

- **CI comparison:** the CI median for this step is 61 s (n=425, pin `aa7c7ca6`, successful runs, excluding R6). R6's median is 80 s. Local cold is 1.53× the CI time.
- **H1 supported:** a cold build takes about 20× as long as an incremental one.
- **H2 supported:** fetching the release is much faster than building.

### Release and provenance

- None of the 35 releases is tagged at the pinned commit.
- v3.9.1 (tag commit `607d058`) is 2 commits after the pin. The differences are only `.ros` state, one telemetry record and `release.json`; nothing under `src/` changed.
- Its asset checksum matches GitHub's digest. The release notes state the assets carry build-provenance attestations, but those attestations were not verified.
- The release bundle and the source-built verifier produced byte-identical `foundations verify --json` output on the R2, R5, R8 and R10 head commits.
- On a deliberately broken input, both failed identically with exit code 3.

### Is caching safe?

- `praxis.dll` differs across builds made in different directories, but a clean rebuild in the same directory is byte-identical. The output is path-dependent but reproducible at a fixed path.
- A cache key of {pinned commit, runner OS/arch, SDK version, project path}, with a fixed checkout path, keeps the cached binary bound to its pinned source.
- Alternatively, pin a released version and verify its checksum or attestation.

### Savings (ESTIMATE)

- About 550 of roughly 604 verifier minutes across R2–R10 are avoidable.
- The 604 is Track A's corrected step figure; V1 measured 607 (CI 580–632), which agrees. The earlier 688 is not used.
- The estimate assumes a cache restore or fetch on a GitHub runner takes about the 4–5 s measured locally. The local fetch was timed through the sandbox proxy, not from a GitHub runner.

## SPR-A2-03: fail-fast ordering (counterfactual ESTIMATE)

Preregistered at `fad75d3`, with one disclosed amendment.

### Data

- Track A's timed job data: 2,191 runs and 11,968 job-minutes, of which 5,418 job-minutes came from 317 failed runs.
- My job-minute total reproduces Track A's 11,967.7.

### Model

- Cheap gates run before browser steps within a job, and browser jobs wait for the cheap-gate jobs.
- The failure is assumed to be caught at the same step.
- Cancelled jobs are excluded.

### Results

| "Cheap gate" definition | Minutes saved | Share of failed-run minutes | Share of all minutes |
|---|---|---|---|
| Broad (preregistered; Track A's build/test/static-gate categories) | 1,287 | 23.7% | 10.8% |
| Strict (live, acceptance, provider, mutation and aggregate "fail when…" steps are not cheap) | 317 | 5.9% | 2.6% |

- R6 dominates the broad figure.
- R10's 20-minute timeouts were cancellations, so the model credits them with no saving.
- **Latency cost (ESTIMATE):** about 56 s added to each green run, at the median.

## Findings

| ID | Class | Finding |
|---|---|---|
| A2-F-01 | VERIFIED | All `.ros/` conflicts removed in R8 and R10 replays |
| A2-F-02 | VERIFIED | No records lost; `validate` passes on 92/92 driver results |
| A2-F-03 | VERIFIED | A team merge in R10 dropped WI-0003; the driver keeps it |
| A2-F-04 | VERIFIED | Application-code conflicts are out of a `.ros/` driver's reach |
| A2-F-05 | VERIFIED | Praxis's strict ordering rule fails on real histories |
| A2-F-06 | VERIFIED | Praxis has no merge driver; its resolver is manual and runs after the conflict |
| A2-F-07 | SUPPORTED | The cold verifier build is compile-bound |
| A2-F-08 | SUPPORTED | The attested release is source-equivalent and behaves identically |
| A2-F-09 | SUPPORTED | A pinned-commit cache key is safe with a complete key; about 550 min saved (ESTIMATE) |
| A2-F-10 | INCONCLUSIVE | Fail-fast savings depend on how "cheap gate" is defined |

## Not tested

- The `EchelonFoundry.Praxis` dotnet tool package.
- `gh attestation verify` on the release assets.
- A compiled (non-`fsi`) merge driver.
- The R6 pin `398af6dd`.
- Server-side and rebase merge flows.

## Reproduction

- **Driver tests:** `tools/ros-merge-driver/`: `dotnet fsi tests.fsx`.
- **Merge replays:** `tools/replay/`: run `python3 -m unittest test_replay_merges`, then `replay_merges.py`, `summarize.py` and `validate_replays.py` with the targets in `raw/`. Requires an unshallowed scratch clone.
- **Verifier timings:** `tools/verifier-timing/time_builds.sh <git dir> aa7c7ca6… <workdir> out.jsonl 3`.
- **Fail-fast estimate:** `python3 tools/failfast/failfast.py <TrackA>/scripts <TrackA>/data/raw/ci-jobs-timed.jsonl raw/failfast-counterfactual.json`.
