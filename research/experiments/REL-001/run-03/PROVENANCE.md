# REL-001 run-03 provenance

Sources reused by run-03, with the sha256 of each source file at the time it was copied. Nothing in run-02 was
modified; run-02 was read from a read-only snapshot of branch `claude/echelon-reliability-integration-g8x7vn`
at commit `c8da63fe8bad6a1737c4eed101729c3ca3f6ac1b` (`/home/user/wt/cbe-run02-readonly`). run-01 sources are
on this branch's base commit `06630d9bfae8a9df3e9f65f5463a0b62ed56848f`. No run-02 per-trial observation,
score or result file was read; `run-02/observations/protocol-notes.md` and the protocol's amendments A1-A3 were.

## Copied byte for byte

| run-03 path | source | sha256 |
|---|---|---|
| `fixtures/repo/src/Ledger/Domain.fs` | run-02 `fixtures/repo/src/Ledger/Domain.fs` | `5b496b6a51e0ca377ca320c6e1a1094e8afe78361d2f3195f9d128bfafbd288f` |
| `fixtures/repo/src/Ledger/Ledger.fs` | run-02 `fixtures/repo/src/Ledger/Ledger.fs` | `5577b4f7089835aac87cb7c1c1fe6d43704aeda6c9a0173995cb1fc7e068f1f4` |
| `fixtures/repo/src/Ledger/Store.fs` | run-02 `fixtures/repo/src/Ledger/Store.fs` | `349dba5cb31d32fca61434493be68219853caf57c9b0672bce9920c0661327fb` |
| `fixtures/repo/src/Ledger/Ledger.fsproj` | run-02 same path | `b9b6d1256d937147694a174cad03705760e5df02f01aed3152ad9b3a74e5f114` |
| `fixtures/repo/tests/Ledger.Tests/BaseTests.fs` | run-02 same path | `68c19e1c39eae9072ff0bfd2c81cf3dc1b3b0c4c151393d98cc7295cf0332983` |
| `fixtures/repo/tests/Ledger.Tests/Ledger.Tests.fsproj` | run-02 same path | `a35b9d1c8c111a93fd3d17666786032f2f3b42ae4cdbea4e98e727d01bcec61b` |
| `fixtures/repo/{Directory.Build.props,global.json,README.md,Ledger.slnx}` | run-02 same paths | `ce0aa59e…`, `14af9c28…`, `80d18c8a…`, `87dbf5ad…` |
| `harness/briefs/core.md` | run-02 `harness/briefs/core.md` | `51cdc987fa9f97728eb354b9acdb37de853d51084f264b28d868c1b64d28ef50` |
| `harness/briefs/directives.md` | run-02 same path | `a2241ec8143362bf9f2ed78140c7d8616983bcf367cccd46f53d32d0ad4c7b68` |
| `harness/briefs/outcome.md` | run-02 same path | `59c63c70b289eec1e2ae070a039c2e6332ac015661439d735a8ee460e183ea1e` |
| `harness/briefs/workflow-c.md` | run-02 same path | `0ae905e5279bf691ee2d842828fff9c738c7159b4f1997da4a530504a728f30f` |
| `harness/briefs/workflow-d.md` | run-02 same path | `408af284bd0fc20d46985f7b407327c2df1916c03dc088eae56230f5e810a6a2` |
| `harness/render-brief.py` | run-02 `harness/render-brief.py` | `1e91996a9215c9a239eecc04529f46f247b8229980564252234cb10a17879983` |
| `directives/DIRECTIVES.md` | run-02 `directives/DIRECTIVES.md` (its PROVENANCE.md applies) | `1ae15c1f5b398d4c18b39b4a8ff11333c640d3c858cee68c911896fbf92985cc` |
| `pricing/anthropic.price-table.json` | `research/pricing/anthropic.price-table.json` (run-02 branch) | `dd58c305821c66ec59c2c567a936885be6833d480c915ad0778b5385ff325b42` |
| `pricing/anthropic-pricing-2026-10-20.excerpt.md` | `research/pricing/` (run-02 branch) | `7f2fc1f9d14412a5ab139869af9d4ecdacfbf27cd9a3b4fc46bef6ce1f3abd09` |

`harness/briefs/shared-remote.md` (`9ffb12ef…`) was not copied: run-03 has no two-agent task.

## Changed copies

- `fixtures/repo/docs/design/interest.md` (run-02 U7's design note) was removed; `docs/design/standing-orders.md`
  (V5's design note) is new. Every other repository file is a byte-for-byte copy (table above).
- `fixtures/oracle/Oracle.fsproj`: run-02's (`933528c5…`) with the comment's "run-02" changed to "run-03".
- `wrapper prompt` in `harness/agent-config.json`: the run-02 prompt text (`852ca26b…` file), byte for byte; the
  file gains the K1/K0 invocation descriptions. Draft revision R1 (2026-10-21) replaces the `tools` string with a `tools` object
  (`builtIn: Bash, Read, Edit, Write`) that `launch-agent.sh` passes as `--tools`; evidence
  `research/token-efficiency/prefix/PREFIX-COMPOSITION.md`.

## Adapted (derived, not copied)

| run-03 file | derived from (sha256) | what changed |
|---|---|---|
| `harness/lib.sh` | run-02 `harness/lib.sh` (`acf32bc3…`) and run-01 `harness/lib.sh` (`f53820c2…`) | self-contained; `REL003_` prefix; pins read from `pins.json`; `require_pins` gate; dry run |
| `harness/setup.sh` | run-02 `harness/setup.sh` (`db4de9c8…`) | one agent per trial (U6 branch removed); pin and digest gate for pilot/confirmatory runs; cache condition recorded |
| `harness/trial.sh` | run-02 `harness/trial.sh` (`e9793e69…`) | single agent; `launch` (K1); `--timed-out` (X5); session binding for K1 |
| `harness/score.sh` | run-02 `harness/score.sh` (`5a95662e…`) | single agent; dry run; report only when the measurement Praxis exists |
| `harness/score.py` | run-02 `harness/score.py` (`5421ae5c…`, the A2 scorer) | single agent; V7 conflict rubric (R6'); cost/token cross-check (M1); cache measurement and cold-equivalent cost (M2); X5 flag; per-metric eligibility for X3 |
| `harness/smoke-agent.sh`, `harness/smoke.sh` | run-02 (`0692fced…`, `702c9591…`) | single agent; wrong-variant option; real-clock transcript timestamps; cold first request |
| `harness/randomize.py` | run-02 `harness/randomize.py` (`0710c792…`) | same algorithm; V1–V8 × 3 replicates; seed 20261021; pilot V1 × 4 arms + V7 in D |
| `fixtures/check.sh` | run-02 `fixtures/check.sh` (`c6d05a21…`) | V tasks; a wrong solution must *build* and fail (not fail to compile); Ordo optional; runs `check-static.py` |
| `fixtures/make-contracts.py` | run-02 `fixtures/make-contracts.py` (`50d42a36…`) | V tasks; Ordo verdict optional ("pending") |
| `analysis/analyze.py` | run-02 `analysis/analyze-run02.fsx` (`19d4f0ea…`), design only | Python (no .NET needed to analyse); one primary hypothesis; Holm for the secondary family; X3 per metric |

## New

`fixtures/tasks/V1..V8/*`, `fixtures/oracle/V1..V8/OracleTests.fs`, `fixtures/reference/**` (generated by
`fixtures/make-references.py` from `fixtures/repo`), `fixtures/check-static.py`, `harness/launch-agent.sh`,
`harness/pins.json`, `analysis/power.py`, `analysis/selftest.py`, `README.md`, `protocol/run-03.md`.
