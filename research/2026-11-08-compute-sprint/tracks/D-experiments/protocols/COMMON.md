# Common method for SPR-D-03..05 (confirmatory, deterministic verification-cost experiments)

- **Fixture.** `indy-init-rehearsal-010` cloned read-only-source to `/home/user/sprint-scratch/D/r010`, start revision
  `95b3ed4df80de0f95afd07be659dbaf6a0e338a6`; solution `Causa.slnx` (13 projects, F# + one C# host).
- **Toolchain.** .NET SDK 10.0.402 (`/root/.dotnet`), `DOTNET_CLI_TELEMETRY_OPTOUT=1`. NuGet cache warm (shared host cache).
- **Runner.** `tooling/bench.py run` (unit-tested). Every measured command runs with `--disable-build-servers` so that
  all compiler / MSBuild / test-host CPU belongs to reaped child processes and is captured by `RUSAGE_CHILDREN`.
- **Primary metric.** CPU seconds (user + sys) of the measured command. **Secondary.** Wall seconds.
  Rationale: the 4-vCPU host is shared with other sprint tracks (load average 4–18 observed in the pilot), which
  inflates wall time unpredictably; CPU time is far less sensitive to contention. 1-min load average is recorded
  before and after each run.
- **Design.** Two arms, 6 replicates each, ABBA alternation with the first block's order drawn from the seed in each
  plan (`bench.schedule`, design `abba`). One independent variable per experiment.
- **Analysis (frozen here, `tooling/analyze_bench.py`).** Effect = ratio of arm medians (treatment / reference) of
  CPU seconds; 95% percentile bootstrap CI resampling runs within arm (10,000 resamples, seed 20261108); exact
  two-sided permutation test of the difference in means over all C(12,6) = 924 label assignments.
  Runs with a non-zero exit (build experiments) are excluded and reported; for test experiments the exit code is
  expected non-zero only if environment-dependent tests are included, so test experiments use counts instead (see
  their protocol).
- **Decision.** The hypothesis is SUPPORTED if the CI lies entirely on the hypothesised side of the stated threshold,
  CONTRADICTED if the CI lies entirely on the other side, otherwise INCONCLUSIVE. Wall-time results are reported
  descriptively only.
- **Threats.** Shared host contention; single fixture; single SDK; page-cache state; results describe this
  machine and repository only.
