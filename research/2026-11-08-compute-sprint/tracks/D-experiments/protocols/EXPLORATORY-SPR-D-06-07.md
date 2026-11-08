# Exploratory SPR-D-06 and SPR-D-07 (not confirmatory; no hypothesis test is claimed)

Common setup as in [COMMON.md](COMMON.md); 4 replicates per arm, ABBA; written before execution.

- **SPR-D-06.** Build servers (MSBuild node reuse / compiler server) left enabled vs `--disable-build-servers`,
  for the incremental build after a non-surface comment edit to `src/Causa.Domain/Kernel.fs`. Metric: **wall time only**
  (with servers enabled, server-process CPU is not attributable to the measured command). Seed 6061.
- **SPR-D-07.** A whole verification step after the same non-surface edit: `full-step` = solution build + full offline
  test suite vs `scoped-step` = build and test only `tests/Causa.Domain.Tests` (which builds Causa.Domain transitively).
  Metric: CPU and wall. Seed 7071. Note: scoped selection is a cost measurement, not a safety claim — every test project
  depends on Causa.Domain, so a real impact-analysis selector would have to justify skipping them.
