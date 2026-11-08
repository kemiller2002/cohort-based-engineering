# SPR-A2-02 — What does rebuilding the pinned Praxis verifier cost, and can it be cached safely?

Status: PREREGISTERED before any timing run. Registered 2026-11-08 14:04 EST, commit 300ccae (time corrected from an earlier mistyped estimate).

## Observed before registration
- R2–R10 `.github/workflows/echelon-foundations.yml` call the reusable workflow
  `kemiller2002/praxis/.github/workflows/foundations-verify.yml@<praxis_ref>` with `praxis_ref`
  pinned to a full commit SHA (8 rehearsals: aa7c7ca6a6e2cb270bdccfe117ea35ade7b0945c; 1: 398af6dd…).
  That job checks out Praxis at the pin, runs `actions/setup-dotnet` (10.0.x), then
  `dotnet build src/Praxis.Cli/Praxis.Cli.fsproj --configuration Release` (no cache step), then
  runs `dotnet praxis.dll foundations verify`.
- Track A: step "Build pinned Praxis verifier" = 688 job-minutes across R2–R10 (MEASURED by Track A).
- Separately, `./praxis` (praxis-validation workflow) downloads a published native release
  (`praxis-<rid>.tar.gz` + `native-checksums.txt` from GitHub Releases `v<version>`), i.e. a release
  artifact channel already exists for *versions*, but the foundations job pins a *commit*.

## Hypotheses
- H1: Local cold build of the pinned CLI project (empty NuGet cache, fresh copy) takes >=3x longer
  than a warm incremental build (same copy, no source change).
- H2: Fetching a published release artifact (if one corresponds to the pin) is faster than a cold build.
- H3: A cache keyed on the pinned commit SHA (+ runner OS, SDK version, project path) is correct:
  the build output is determined by the source tree at that commit plus the toolchain.

## Procedure (serial, one dotnet build at a time; host 4 vCPU shared)
1. Shallow-fetch the pinned commit into /home/user/sprint-scratch/A2/praxis-src.
2. Cold: n=3; each run: fresh `git worktree`/copy of the tree, empty `NUGET_PACKAGES` dir,
   `dotnet build-server shutdown`, then `/usr/bin/time` the exact CI command
   `dotnet build src/Praxis.Cli/Praxis.Cli.fsproj --configuration Release`.
3. Warm-restore: n=3; fresh copy but NuGet cache retained (models a CI cache of ~/.nuget/packages only).
4. Warm-incremental: n=3; same copy, rebuilt with no change (models caching the build output).
5. Release fetch: list releases (GitHub MCP, read-only); download the linux-x64 asset for the
   matching version n=3, verify checksum, time download+extract. Record whether any release
   is built from the pinned commit (provenance).
6. Determinism probe: compare SHA-256 of praxis.dll from two cold builds (informs cache safety).
7. Ratio: local cold median vs CI median step duration for the same pin (from Track A ci-steps.csv).

## Metrics / success criteria
- Wall seconds (MEASURED), medians and ranges. H1 supported if cold median / warm-incremental median >= 3.
- Cache-key safety judged by: key includes pin SHA; output identity check (step 6); whether the
  fetched release is provably bound to the pin (tag -> commit).
- Savings estimate (ESTIMATE): 688 min x (1 - cached/CI-cold ratio).
