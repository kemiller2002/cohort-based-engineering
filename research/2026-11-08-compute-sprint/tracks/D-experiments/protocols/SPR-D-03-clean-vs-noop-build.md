# SPR-D-03 (confirmatory): clean build vs no-op incremental build

Preregistered 2026-11-08 before execution. Common method: [COMMON.md](COMMON.md).

- **Question.** How much of a verification step's build cost is avoided when the agent's workspace keeps `obj/`/`bin/`
  (long-lived workspace) versus a clean checkout (fresh sandbox per change), when no source changed?
- **Independent variable.** Build-output state before `dotnet build`: `clean` (`git clean -xfdq src tests` then
  untimed `dotnet restore`) vs `noop` (immediately after a successful build, nothing changed).
- **Measured command (both arms).** `dotnet build Causa.slnx --no-restore --disable-build-servers -v q -nologo`.
- **Hypothesis H-03.** CPU(noop) / CPU(clean) < 0.20 (no-op build costs under 20% of a clean build).
- **Replicates.** 6 per arm, ABBA, seed 3031.
- **Raw.** `raw/SPR-D-03.jsonl`.
