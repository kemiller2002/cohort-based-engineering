# F2 `summa`: provenance

Worker S, 2026-10-22. Everything here is reproducible from the source clone and this directory.

## Source

| Item | Value |
|---|---|
| Repository | `kemiller2002/summa`, local clone `/home/user/kemiller2002/summa` (read only: `git archive`, never modified) |
| Commit | `8b0e93ea7c57934acaa20a7eabd4d67f26efcae4` ("Merge pull request #111 from kemiller2002/codex/summa-forma-090") |
| Snapshot | `repo/`: 395 files, 6.3 MB, a plain tree; the harness git-initialises its own copy |
| Builder | `make-snapshot.sh [CLONE] [OUT]`; `check.sh` step S6 rebuilds it and `diff -r`s it against `repo/` |

## What the snapshot drops, and why

Nothing the F# build or the F# tests need is dropped (the solution builds and every remaining test passes; see
`check-output.txt`).

| Dropped | Why |
|---|---|
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `BOOTSTRAP.md`, `HANDOFF.md`, `.github/` (workflows, `copilot-instructions.md`) | Agent-instruction files and CI. `CLAUDE.md` is loaded automatically by Claude Code and points to the Praxis agent contract; Praxis is held out of every arm (as in ARCH-001). |
| `README.md` | Describes only the ROS/Praxis hub tooling dropped below (`./ros`, `npm run hub`). |
| `.praxis/`, `.ros/`, `praxis`, `praxis-hub`, `praxis.cmd`, `praxis.ps1`, `ros`, `ros-hub`, `ros.cmd`, `ros.json`, `ros.ps1` | Praxis/ROS work-protocol tool and its state. |
| `docs/00-governance/`, `docs/work-protocol.md`, `docs/work-adapter-contract.md`, `docs/work-backlog-guide.md`, `docs/remote-agent-contract.md`, `docs/remote-protocol.md`, `docs/agent-provenance.md`, `docs/development-telemetry.md`, `docs/ordo-observation.md` | Praxis/ROS operating documents and agent process (including an Ordo observation note). |
| `registries/`, `schemas/`, `telemetry/`, `templates/` | Praxis/ROS registries, schemas and telemetry. |
| `.sde/` | The installed SDE distribution, including `architecture/FOUR-TIER-ARCHITECTURE.md`: that doctrine is treatment material for arms B-D only (in `pack/`). |
| `.visual-engineering/`, `.communication-engineering/` | Agent guidance packs. |
| `package.json`, `package-lock.json`, `playwright.config.js`, `tests/browser/`, `tests/color-contract.test.mjs`, `tools/*.mjs`, `tools/pages/`, `deploy/` | Node/browser tooling (npm, Playwright, local servers, Pages assembly). `node_modules` cannot be installed here. |

Kept, although not F#: `app/`, `web/`, `web-hub/`, `web-kernel/` (F# tests read them: binding agreement and
architecture tests), `.echelon/`, `.conditor/`, `conditor.json`, `limen.config.json`, `aegis-boundaries.json`,
`input-documents/`, `release/`, `tools/authorize-clean.sh`, `vendor/nuget/` (the real vendored packages),
`docs/` (the rest), `context/`, `research/decisions/` (the DF-SUMMA records the code and the tasks cite).

## What the snapshot patches

Eleven F# tests whose subject was dropped or is nondeterministic are **skipped** with
`[<Fact(Skip = "ARCH-002 snapshot: …")>]` (their code is unchanged):

| File | Tests | Reason |
|---|---|---|
| `tests/Summa.Web.Tests/ArchitectureTests.fs` | INV-ARCH-005 | reads `.ros/`, `.github/`, `CLAUDE.md` |
| same | INV-ARCH-007 | needs `node_modules` |
| `tests/Summa.Web.Tests/FoundationsConformanceTests.fs` | 4 tests on the installed npm packages | need `node_modules` |
| `tests/Summa.Web.Tests/RoutesTests.fs` | the route inventory against Limen's npm schema | needs `node_modules` |
| `tests/Summa.Tests/GapAnalysisTests.fs` | all 3 (the module reads `.ros/work/queue.json`) | Praxis/ROS state |
| `tests/Summa.Tests/SearchTests.fs` | SUM4-018 "fast enough" | a 1-second wall-clock bound that failed (1,134 ms) in a Debug build under load |

At the source commit, in this environment, the 6 `node_modules` tests already fail (`dotnet test -c Release`:
Contracts 64/64, Ledger 199/199, Storage 151/151, Web 247/253).

## What the snapshot adds

- `tests/Summa.Acceptance.Tests/` (from `snapshot-additions/`): an xunit project that compiles `Kit.fs`, then
  `Acceptance/*.fs`. The harness copies a task's visible tests into `Acceptance/`. `Kit.fs` builds books through
  Summa's own domain commands and drives the accounting engine; the sealed oracle uses the same file renamed
  (`OracleKit.fs`).
- Its entry in `Summa.sln` (nested under `tests`).

## Copied or adapted from ARCH-001 (frozen; never modified)

| Here | Source | Source sha256 | How |
|---|---|---|---|
| `pack/FOUR-TIER-ARCHITECTURE.md` | `fixtures/pack/FOUR-TIER-ARCHITECTURE.md` | `725cb3d9…08775b` | byte for byte (check S1) |
| `pack/SUMMA-ARCHITECTURE.md` | `fixtures/pack/LENDING-ARCHITECTURE.md` | `54fd5ba3…ae23be` | same structure, rewritten for Summa's tier map |
| `policy.json` | `verifier/policy/lending.policy.json` | `6994fdfc…10217b` | SYM-01 symbol sets and HEU-01/02 copied; tiers, exceptions and BND scopes for Summa |
| `make-contracts.py` | `fixtures/make-contracts.py` | `8e75d9b0…469986d8` | same construction; SUMMA ids, DF-SUMMA decisions, no conflict, trap existence private |
| `check.sh` | `fixtures/check.sh` | `d6684382…468e61` | same steps plus baseline-delta, regression, snapshot reproduction and timings |
| sealed `tools/mkref.sh` | `arch001-sealed/tools/mkref.sh` | `d6c4447d…01134` | also skips `tests/Summa.Acceptance.Tests/Acceptance/` |
| sealed `oracle/Oracle.fsproj` | `arch001-sealed/oracle/Oracle.fsproj` | `2f66e9de…9ab8e` | references the trial's `Summa.Web.Application`; pins FSharp.Core 10.1.401; with a `NuGet.config` template for the vendored feed |
