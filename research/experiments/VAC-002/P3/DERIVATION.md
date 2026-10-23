# How the P3 harness derives from P2's

P3 reuses P2's runner, scoring, usage collection and review machinery. P2's files are not edited: P2 is preserved as
merged in `10e1adf`. Each P3 harness file is a copy of its P2 original, changed only where P3 requires it. Unified
diffs from each P2 file to its P3 derivative are in `harness/derivation/`, regenerated at each freeze.

## 1. Files

| P3 file | P2 original | What changed and why |
|---|---|---|
| `harness/p3.fsx` | `p2.fsx` | Removed the unused NuGet reference (D5). Added: `derive` and `oracle-proj` (the tree transform, §2); `admit2` and `admission-text2` (contract v0.2 for arm E); `exposure` (§6 of `PROTOCOL.md`). Widened the contamination scan to P3's paths and the orchestrator's. Schema names `cbe.vac-002-p3.*`. Everything else, including `admit` (v0.1), `records`, `trx`, `stream`, `render` and `score`, is unchanged |
| `harness/p3.sh` | `p2.sh` | P3's arm mapping (A–E, `PROTOCOL.md` §3); E runs P2-D's plan, admission, implement and gate cycle with `admit2`; P2-E's risk policy and reviewer are dropped (not a P3 arm); allowlisted agent environment (D3); replicates (`X = SCEN-ARM-rN`); `spent` counts every run, every review and the orchestrator ledger against the $150 ceiling; `expose` builds the exposure manifest; each turn's brief is copied into the results |
| `harness/corpus.sh` | `corpus.sh` | Scenarios name their overlays (P2's and P3's) and their sealed store; trees are built over P2's fixtures and then derived; the oracle project is prepared for the TestKit. The check logic is unchanged |
| `harness/briefs/brief.md` | `briefs/brief.md` | New `authority` section (the frozen contract); the checklist cut to three questions about the contract; the records section moves to schema 0.2 (no status; `affectsSources`; evidence versus verification); P2's two authority pointers in `intro` and `report` made neutral; P2-E's verifier wording dropped |
| `harness/agent-config.json` | `agent-config.json` | CLI version; allowlisted environment; no verifier prompt |
| `harness/review/RUBRIC.md` | `review/RUBRIC.md` | States the authorization standard itself (no README section any more); adds the six review categories the mission names and `consequentialUnauthorized` |
| `harness/review/bundle.sh` | `review/bundle.sh` | Several runs per bundle; P3 paths and execution ids |
| `harness/review/review.sh` | `review/review.sh` | Allowlisted reviewer environment; P3's `stream` |
| (none) | `review/agreement.fsx` | Used unchanged from P2 |
| (none) | `../harness/seal.sh` | Used unchanged from VAC-002 |
| `fixture/testkit/` | (new) | xUnit-compatible test stand-in (D1) |

## 2. The tree transform (`p3.fsx derive`)

`corpus.sh tree` copies `P2/fixture/<domain>/repo`, then the scenario's overlays, then any sealed variant. It then
derives the copy in place:

1. **README.** `README.md` loses its level-2 "Authority" section, and nothing else.
2. **Test projects.** Every `*.Tests.fsproj` drops its `PackageReference` lines and gains `IsTestProject`.
3. **TestKit.** `tests/TestKit/{Xunit.fs, Program.fs}` and a root `Directory.Build.targets` are added. Test projects
   then compile `Xunit.fs` first (`CompileBefore`) and `Program.fs` last (`CompileAfter`), run as console programs,
   and `dotnet test` runs them through a `VSTest` target that writes the `.trx` file the logger names.
4. **NuGet audit.** `Directory.Build.props` gains `NuGetAudit=false`.

**The TestKit implements:**

- `[<Fact>]`;
- `Assert.Equal`, `NotEqual`, `True`, `False`, `Contains` (substring and collection), `DoesNotContain`,
  `StartsWith`, `EndsWith`, `Empty`, `NotEmpty` and `Throws`.

That is a superset of what every fixture, scenario and sealed oracle test uses. Test names in the `.trx` are
`Module.name`, as xUnit's are, so `p2.fsx trx` reads them unchanged.
