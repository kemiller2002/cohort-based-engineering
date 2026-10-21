# ARCH-001 shared interfaces (coordinator-owned, v0.1 draft)

This file fixes the contract between Workstream B (fixtures and hidden oracles), Workstream C
(verifier) and Workstream D (harness). Change it only through the coordinator. Everything here is
**pre-registration draft** until PROTOCOL.md freezes it.

## 1. Authority

- Architecture authority: **SDE-DOCTRINE-003 "Four-Tier Architecture" v0.2.1** (`ordo/doctrine/FOUR-TIER-ARCHITECTURE.md`
  at ordo `bb43c26`; byte-identical in summa/signal `.sde/architecture/`). Ambiguity resolutions A1–A11 from
  `inventory/architecture-spec-inventory.md` §7 are adopted for this experiment, notably:
  - A1: an explicit tier mapping is declared per repository.
  - A2: any downward edge is legal; only upward edges violate.
  - A5: the composition root lives in Tier 4.
- **No secret rules.** Every rule the verifier scores is an instance of a rule in the architecture
  pack that arms B, C and D receive (§3). Only test *data* and per-task trap *probes* are hidden.
  Arm A receives the same repository but not the pack: that contrast is H1.

## 2. Fixture repository: `Lending` (library lending domain, F#/.NET 10)

```
Lending.slnx
global.json                      { "sdk": { "version": "10.0.100", "rollForward": "latestFeature" } }
Directory.Build.props            net10.0
README.md                        what the app does; how to build/test. No architecture guidance.
docs/decisions/DEC-*.md          the app's own accepted DOMAIN decisions (visible in every arm)
src/Lending.Semantic/            Tier 1  namespace Lending.Semantic
src/Lending.Transition/          Tier 2  namespace Lending.Transition    refs: Semantic
src/Lending.Application/         Tier 3  namespace Lending.Application   refs: Transition, Semantic
src/Lending.Host/                Tier 4  namespace Lending.Host          refs: Application (+ lower)
    Persistence/*.fs             Lending.Host.Persistence   adapters (in-memory store, JSON file store)
    Cli/*.fs                     Lending.Host.Cli           presentation: parse command text, render text
    Composition.fs               Lending.Host.Composition   composition root: clock, store, wiring
tests/Lending.Tests/             visible tests (xunit 2.9.2, Microsoft.NET.Test.Sdk 17.11.1)
    Acceptance/                  task acceptance tests given to the agent are copied here
```

Production code is idiomatic, functional F# (records, unions, pure functions, `Result`); ports are
records of functions defined in Tier 3 (`Lending.Application.Ports`), implemented in Tier 4.
The repo is a git repository, and each trial starts from the same commit.

## 3. Architecture pack (arms B, C, D; never A)

`pack/` is copied into the workspace as `docs/architecture/` for arms B–D:

1. `FOUR-TIER-ARCHITECTURE.md`: the SDE-DOCTRINE-003 v0.2.1 file, byte for byte (sha256 recorded).
2. `LENDING-ARCHITECTURE.md`: the tier map (§2) and allowed dependency directions, plus
   responsibility placement for this app. It restates as instances only; it adds no new principle.
   Its rules are numbered with the verifier rule ids below.

## 4. Rule ids (policy `arch001.policy/1`)

Classes: **DET** = decided from compiler-resolved project/symbol structure; **HEU** = heuristic, reported
as a finding, never a gate failure; **REV** = scored by the blinded independent reviewer only.

| Rule | Class | Sev | Statement (instance of) |
|---|---|---|---|
| ARC-DEP-01 | DET | 3 | No upward ProjectReference (FT:103; AR-02) |
| ARC-DEP-02 | DET | 3 | Tier 1/2 projects reference no package and no assembly beyond FSharp.Core and the BCL (FT:109; AR-03) |
| ARC-SYM-01 | DET | 3 | Tier 1/2 code uses no symbol from `System.IO`, `System.Net`, `System.Text.Json`, `System.Data`, `System.Diagnostics.Process`, `System.Console`, `System.Threading.Tasks` effects, `System.Environment` (FT:45, FT:109; AR-04/05) |
| ARC-SYM-02 | DET | 2 | No code outside the Tier 4 composition root reads the clock, randomness or GUID generation: `DateTime.Now/UtcNow/Today`, `DateTimeOffset.Now/UtcNow`, `System.Random`, `Guid.NewGuid`, `Stopwatch` (FT:78; AR-06/08; A5) |
| ARC-SYM-03 | DET | 2 | Tier 3 uses no symbol from `System.IO`, `System.Net`, `System.Text.Json`, `System.Console` (effects go through ports; FT:78; AR-08/29) |
| ARC-BND-01 | DET | 2 | `Lending.Host.Cli` (presentation) uses no symbol from `Lending.Host.Persistence`; it reaches state only through `Lending.Application` (FT:67-70 coordination; AR-29) |
| ARC-BND-02 | DET | 2 | `Lending.Host.Cli` and `Lending.Host.Persistence` call no function of `Lending.Transition` (decisions are made in Tier 2 and coordinated by Tier 3, never re-entered from Tier 4; FT:111-124; AR-07/09) |
| ARC-BND-03 | DET | 2 | `Lending.Host.Cli` reads no field of a Tier 1 entity record other than identifiers; it renders Tier 3 view models (`Lending.Application.Views`) (FT:67-70; AR-23) |
| ARC-HEU-01 | HEU | 1 | Catch-all exception handlers (`with _`/`with ex` that do not re-raise) in Tiers 1–3, or an `Unknown` outcome collapsed into a failure (AR-10) |
| ARC-HEU-02 | HEU | 1 | A domain numeric/date literal or predicate duplicated in two tiers (AR-19) |
| ARC-HEU-03 | HEU | 1 | Comparison/arithmetic on domain values in `Lending.Host` (business logic in presentation/infrastructure; AR-23/AR-08) |
| ARC-HEU-04 | HEU | 1 | A file exceeds the SDE-STRUCT-001 500-line band (AR-22) |
| ARC-TRC-01 | DET | 1 | Arms C/D only (decision fidelity): every `decision` node id in the task's ecir/1 contract appears in a production source comment and in a test (name or comment) |
| ARC-REV-01..03 | REV | — | Reviewer rubric: semantic authority (AR-07), effect flow (AR-09), single authority for duplicated facts (AR-19); 0/1/2 each |

Architectural acceptance of a trial = **zero DET violations of severity ≥ 2** in production code under the
full policy (ARC-TRC-01 is scored under decision fidelity, not architectural acceptance).

## 5. Verifier CLI (`archcheck`)

```
archcheck verify --repo DIR --policy POLICY.json [--contract CONTRACT.json] [--json] [--out REPORT.json]
archcheck selftest
```

- It builds the repository (`dotnet build`, Release, no restore from the network beyond NuGet) and
  type-checks every production project with **FSharp.Compiler.Service 43.12.402** using the real
  compiler arguments, then walks the **typed** symbol uses (`GetAllUsesOfAllSymbolsInFile`) and the
  ProjectReference and PackageReference graph.
- Exit codes: 0 = no DET violation of severity ≥ 2; 1 = at least one; 2 = could not evaluate
  (build or type-check failure, bad policy). HEU findings never change the exit code.
- Report `arch001.verifier-report/1`:
  `{schema, verifier:{version, sha256}, policy:{id, sha256}, repo:{gitHead, treeClean, treeHash},
  evaluatedAt, buildOk, projects:[{path, tier}], findings:[{ruleId, class, severity, project, file,
  line, column, symbol, message}], summary:{det:{bySeverity}, heu, pass}}`.
  Findings are sorted deterministically, and two runs on the same tree give byte-identical findings.
- The policy file maps project → tier and lists per-rule namespace/symbol sets. Both the policy
  and the verifier binary are hashed into every report.

## 6. Task package layout (Workstream B)

```
fixtures/repo/                         starting repository (git-initialised by setup)
fixtures/pack/                         architecture pack (§3)
fixtures/policy/lending.policy.json    the full verifier policy
fixtures/tasks/T<n>/requirement.md     initial requirement (all arms)
fixtures/tasks/T<n>/acceptance/*.fs    visible acceptance tests (all arms)
fixtures/tasks/T<n>/contract.json      ecir/1 decision contract (C, D) — must pass or be refused by `ordo ecir check` as designed
fixtures/tasks/T<n>/followup.md        follow-up requirement (all arms; never shown before phase 2)
fixtures/tasks/T<n>/followup-acceptance/*.fs
fixtures/tasks/T<n>/followup-contract.json
fixtures/tasks/T<n>/task.json          harness metadata: categories, traps, expected tiers, scoring
SEALED (encrypted at rest during trials):
fixtures/oracle/T<n>/{Initial,Followup}OracleTests.fs   hidden functional tests
fixtures/oracle/T<n>/probes.json                        hidden per-task architectural probes (instances of §4 rules)
fixtures/reference/T<n>/{good,trap}/                    reference solution + functionally-correct-but-architecturally-invalid trap
```
