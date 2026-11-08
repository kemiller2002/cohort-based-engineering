# SPR-D-05 (confirmatory): affected-project test selection vs full offline suite

Preregistered 2026-11-08 before execution. Common method: [COMMON.md](COMMON.md).

- **Question.** For a change confined to one test project's subject, what fraction of test-execution cost does
  running only the affected test project save, versus running the whole offline suite?
- **Independent variable.** Test scope (both `--no-build` after one untimed build):
  `full` = `dotnet test Causa.slnx --no-build --disable-build-servers --filter "FullyQualifiedName!~.Live."`;
  `affected` = `dotnet test tests/Causa.Domain.Tests --no-build --disable-build-servers`.
- **Known environment failures.** Live GitHub tests (no `CAUSA_GITHUB_TOKEN`) are excluded by the filter; a small number
  of Acceptance tests that require `node_modules` (npm packages unavailable here) fail identically every run. The
  exit code is therefore not used for exclusion; per-run passed/failed/total counts are recorded and must be
  identical across replicates of an arm (otherwise the run is flagged).
- **Hypothesis H-05.** CPU(affected) / CPU(full) < 0.25.
- **Replicates.** 6 per arm, ABBA, seed 5051.
- **Raw.** `raw/SPR-D-05.jsonl`.
