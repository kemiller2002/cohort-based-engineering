# SPR-D-04 (confirmatory): public-surface edit vs non-surface edit in the root domain project

Preregistered 2026-11-08 before execution. Common method: [COMMON.md](COMMON.md).

- **Question.** After an agent edits the most-depended-on project (`src/Causa.Domain`), does the incremental build cost
  depend on whether the edit changes that project's public surface (forcing dependants to recompile) or not?
  This informs whether F# reference-assembly / up-to-date checks keep per-change verification cheap.
- **Independent variable.** The edit appended to `src/Causa.Domain/Kernel.fs` before the measured build:
  `surface` = a new public module `module SprDProbe<N> = let value = <N>`; `internal` = a comment line `// spr-d probe <N>`.
  `<N>` is unique per run (nanosecond clock mod 10^8, so it fits an int32 literal; a 19-digit literal failed to compile in the pre-run syntax check).
- **Prepare (untimed, both arms).** `git checkout -- src/Causa.Domain/Kernel.fs`, `dotnet build` to reach a fully
  built baseline, then apply the edit.
- **Measured command.** `dotnet build Causa.slnx --no-restore --disable-build-servers -v q -nologo`.
- **Hypothesis H-04.** CPU(surface) / CPU(internal) > 1.5 (a surface change costs at least 50% more to rebuild).
  The opposite outcome (ratio CI including or below 1.5) would mean dependants rebuild either way or neither way.
- **Replicates.** 6 per arm, ABBA, seed 4041.
- **Raw.** `raw/SPR-D-04.jsonl`.
