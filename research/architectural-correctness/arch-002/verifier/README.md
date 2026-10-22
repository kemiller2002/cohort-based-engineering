# archcheck: ARCH-001 architecture verifier, ARCH-002 edition (0.2.0)

This is a copy of `research/architectural-correctness/verifier/` (ARCH-001, frozen) with one addition for
ARCH-002's brownfield fixtures: `--baseline REPORT.json` (section "ARCH-002: brownfield baseline" below).
Everything else is ARCH-001's verifier unchanged; provenance and hashes are in `../PROVENANCE.md`.


`archcheck` checks an F#/.NET repository against the ARCH-001 rule catalogue
(`design/INTERFACES.md` §4). It works from structure the compiler resolves:

- the MSBuild-evaluated `ProjectReference`, `PackageReference` and `ReferencePath` items;
- the typed symbol uses that `FSharpChecker` reports when it type-checks each production
  project with the project's real `fsc` arguments.

It does not search source text. Only ARC-TRC-01 reads comments, because that rule is
defined over comments.

Workstream C owns this directory. The verifier writes nothing into the repository it
evaluates except the normal `bin/` and `obj/` output of `dotnet build`.

## Build, test, publish

```sh
export DOTNET_ROOT=/home/user/.tools/dotnet PATH=$DOTNET_ROOT:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd research/architectural-correctness/verifier

dotnet build Archcheck.slnx -c Release
dotnet test  Archcheck.slnx -c Release                                   # 36 tests (~1 min, includes integration)
dotnet test  Archcheck.slnx -c Release --filter "Category!=Integration"  # 34 unit tests (~1 s)
dotnet publish src/Archcheck/Archcheck.fsproj -c Release -o dist         # framework-dependent, net10.0
dotnet dist/archcheck.dll selftest                                       # 25 sample repos (~10 min at --parallel 3)
```

The `verifier/global.json` file pins SDK 10.0.402 (`rollForward: disable`).
`dist/` is git-ignored. Each report records the sha256 of the `archcheck.dll` that
produced it.

### Why FSharp.Compiler.Service 43.12.402

FCS 43.12.402 is the compiler build inside .NET SDK 10.0.402:
`sdk/10.0.402/FSharp/FSharp.Compiler.Service.dll` has file version 43.1204.226 and ships
with FSharp.Core 10.1.402. The type-check therefore uses the same language version and
inference as the `dotnet build` it runs next to.

`ordo/tools/Ordo.Complexity` pins 43.8.400 (F# 8, FSharp.Core 8.0.400). That tool only
parses and tokenises, so it never needed to match the SDK's compiler. This tool
type-checks against assemblies the SDK has just built, so the versions must agree.

FCS requires exactly FSharp.Core `[10.1.402]`, so the implicit FSharp.Core reference is
disabled and the version is pinned explicitly.

## CLI

```
archcheck verify --repo DIR --policy POLICY.json [--contract CONTRACT.json] [--probes PROBES.json]
                 [--baseline REPORT.json] [--require-clean] [--json] [--out REPORT.json] [--facts USES.json]
archcheck selftest [--samples DIR] [--filter NAME] [--parallel N]
```

- **stdout.** By default, one line per finding (`RULE SEV file:line message`, plus
  `[probe:N]` when a probe produced it), then a summary line. With `--json`, the full
  report.
- **`--out`.** Writes the JSON report to a file, regardless of `--json`.
- **`--facts`.** Writes every resolved symbol use (file, line, column, enclosing
  scope, qualified name, owner, assembly, kind). This is diagnostic evidence for audits,
  not part of the report.
- **Exit codes.**
  - **0.** No DET finding of severity 2 or higher.
  - **1.** At least one such finding.
  - **2.** The repository could not be evaluated: a bad policy, probe or contract file;
    an input file inside `--repo`; an unmapped production project; a build or design-time
    failure; a type-check error; or a dirty tree under `--require-clean`.
  - HEU findings never change the exit code.
- **`selftest`.** Copies each `tests/samples/<name>/repo` to a temporary directory and
  commits it to a new git repository there. It runs `verify` on the copy and checks:
  - the exit code and the exact set of rule ids against `expected.json` (and the
    finding count, where the file gives one);
  - `treeClean`;
  - that `treeHash` equals git's own `HEAD^{tree}`.

## How the repository is loaded (and how compiler arguments are obtained)

1. **Content and provenance.** The verifier first lists the evaluated content:
   - tracked files from `git ls-files --cached`;
   - untracked, non-ignored files from `git ls-files --others --exclude-standard`;
   - untracked files under `bin/` or `obj/` are excluded.

   It then records four values:
   - `gitHead`;
   - `treeClean`, from `git status --porcelain` with build output ignored;
   - `treeHash`, the SHA-1 that `git write-tree` would print if exactly that content were
     staged. It is computed in-process from file bytes and modes (100644, 100755, or
     120000 for symlinks), and nothing is written to `.git`;
   - the `dotnet --version` resolved from the repository's directory, so the repo's
     `global.json` is honoured.

   With `--require-clean`, a dirty tree means exit 2. This step runs before the build.
2. **Projects.** `*.fsproj` and `*.csproj` files in that content are classified by the
   policy: `projects` maps a project path to a tier, and `testProjects` lists path
   prefixes. A production project the policy does not map means exit 2 (resolution A1:
   unmapped projects are not guessed). Declared `ProjectReference` and
   `PackageReference` elements are read with `System.Xml.Linq`, which gives file and
   line numbers. This covers the project files and any `.props` or `.targets` file in
   the repository.
3. **Build.** `dotnet build <root> -c Release -nodeReuse:false` runs for every
   production project that no other production project references. Test projects are
   never built. Restore uses the configured NuGet feeds.
4. **Real compiler arguments.** For every project, the verifier runs a design-time
   compile pass:

   ```
   dotnet msbuild P.fsproj -p:Configuration=Release -p:DesignTimeBuild=true -p:SkipCompilerExecution=true
     -p:ProvideCommandLineArgs=true -p:NonExistentFile=__archcheck_nonexistent__/__none__ -t:Compile
     -getItem:FscCommandLineArgs -getItem:ReferencePath -getItem:ProjectReference -getItem:PackageReference ...
   ```

   - `FscCommandLineArgs` is the exact command line the F# `CoreCompile` target passes
     to `fsc`: defines, `--langversion`, warnings, every `-r:` reference and the ordered
     source list.
   - `SkipCompilerExecution` stops `fsc` from running.
   - Setting `NonExistentFile` adds a missing output to `CoreCompile`, so MSBuild never
     skips the target as up to date. Without it, MSBuild returns no arguments.
   - The evaluated items carry `DefiningProjectFullPath`. That metadata tells references
     declared in repository files (including imports such as `Directory.Build.props`)
     apart from transitive and SDK-implicit ones.
   - `ReferencePath` metadata (`FrameworkReferenceName`, `ReferenceSourceTarget`,
     `NuGetPackageId`) classifies each compiled-against assembly as BCL, project output,
     package or raw assembly.
   - Test projects get a plain evaluation (`-getItem:Compile`), and their sources are
     parsed only.
5. **Type-check.** `FSharpChecker.ParseAndCheckProject` runs on options built from those
   arguments, referencing the just-built assemblies.
   - Any error diagnostic means exit 2.
   - `GetAllUsesOfAllSymbols()` supplies every non-definition, non-`open` use. Each use
     is resolved to its qualified name, declaring entity, assembly and kind (type, union
     case, field, property, method, constructor, function, module value, active pattern,
     event).
   - Type abbreviations are followed, so `type Clock = System.DateTime` resolves to
     `System.DateTime`.
   - F# entities are named by their source path (`module Loan` next to `type Loan` is
     `…Loan`, not `…LoanModule`), and generic arity suffixes are dropped.
   - The enclosing namespace or module of each use, record-construction labels,
     `try … with` clauses, match arms, numeric literals and infix operators come from the
     untyped parse tree (`ParsedInput.fold`).
   - Comments come from the parse trivia, plus `///` lines that the trivia omits and that
     do not start inside a string or block comment.
6. **Rules.** Pure functions over these immutable facts (`Rules.fs`, `Heuristics.fs`).

## Rules and their classification

Class and severity are fixed in the verifier (`Domain.Catalogue`). A policy cannot
change them.

| Rule | Class | Sev | Decided from | Policy parameters |
|---|---|---|---|---|
| ARC-DEP-01 | deterministic | 3 | Evaluated `ProjectReference`s declared by repository files: an edge to a higher tier, or from a production project to a test project. Also explicit `forbiddenReferences` `{from,to}` pairs, which subsume DOK-R008 (project path or name). | `forbiddenReferences` |
| ARC-DEP-02 | deterministic | 3 | Tier 1/2 direct `PackageReference`s plus the compiler-resolved `ReferencePath`, which also catches transitive packages and raw `<Reference>` assemblies. Allowed: `allowedPackages` and framework references. | `tiers`, `allowedPackages` |
| ARC-SYM-01 | deterministic | 3 | Typed symbol uses in Tier 1/2 under forbidden namespace or symbol prefixes. | `tiers`, `namespaces`, `symbols`, `modules`, `exceptModules`, `kinds` |
| ARC-SYM-02 | deterministic | 2 | Typed uses of clock, random, GUID and Stopwatch symbols anywhere outside `exceptModules` (the composition root). | same |
| ARC-SYM-03 | deterministic | 2 | Typed uses in Tier 3 of I/O, network, JSON and console symbols. | same |
| ARC-BND-01 | deterministic | 2 | Typed uses at sites in `Lending.Host.Cli` of any `Lending.Host.Persistence` symbol. | same |
| ARC-BND-02 | deterministic | 2 | Typed uses at sites in Cli or Persistence of a `Lending.Transition` function, method or active pattern. Types and union cases are allowed. | same, `kinds` |
| ARC-BND-03 | deterministic | 2 | Field reads at sites in Cli of a record declared in `Lending.Semantic`, except fields named like `identifierFields` (`Id`, `*Id`). Dot access and record patterns count as reads; record-construction labels do not. | `modules`, `entityNamespaces`, `identifierFields`, `symbols` |
| ARC-TRC-01 | deterministic (over comments) | 1 | Each `decision` node id in the ecir/1 `--contract` must appear in a production comment and in a test project (binding name or comment). Severity 1, so it is scored for decision fidelity and is not a gate. | none |
| ARC-HEU-01 | heuristic | 1 | Parse tree: a `with` clause matching anything (`_`, `ex`, `:? exn`) with no `when` guard and no `reraise`/`raise`/`failwith` in its body (Tiers 1–3), or a match arm `Unknown … -> Error/Failed/Failure …`. | `tiers`, `unknownTiers`, `unknownCases`, `failureCases` |
| ARC-HEU-02 | heuristic | 1 | A numeric literal, or a `field op literal` predicate, that occurs in two or more tiers. Each occurrence above the lowest tier holding it is reported. | `tiers`, `ignoredLiterals` |
| ARC-HEU-03 | heuristic | 1 | An infix comparison or arithmetic operator in `Lending.Host` whose operand contains a typed use of a field, property or function from a domain namespace. | `modules`, `domainNamespaces` |
| ARC-HEU-04 | heuristic | 1 | A production file longer than `maxLines` (500). | `maxLines` |
| ARC-REV-01..03 | review | — | Not mechanised. Scored by the blinded reviewer. | — |

**Matching.** `namespaces` and `symbols` match the same way: by dotted prefix of the
resolved name, respecting segment boundaries. `System.IO` matches `System.IO.File.Exists`
but not `System.IOX`. `modules` and `exceptModules` match the enclosing namespace or
module of the use site, also by dotted prefix.

**Policy file.** `policy/lending.policy.json` (schema `arch001.policy/1`) is the policy
for the Lending fixture layout in INTERFACES §2.
- Every rule except ARC-TRC-01 must be configured.
- An unknown rule id, an unknown parameter or an invalid kind or tier means exit 2, so a
  typo cannot silently disable a check.

**Probes (`--probes`).** The file is a JSON array of rule instances, for example
`{"rule":"ARC-BND-03","module":"Lending.Host.Cli","forbiddenSymbols":["Lending.Semantic.Loan.DueDate"]}`.
- Each probe is evaluated with its rule's class and severity.
- A probe is a complete instance: fields it omits are empty, not inherited from the
  policy.
- A finding a probe shares with the policy is reported once, with
  `origins: ["policy","probe:N"]`.

**Report.** The report schema is `arch001.verifier-report/1`:

```
{schema, verifier:{version, sha256, fcs, dotnetSdk}, policy:{id, sha256}, probes, contract,
 repo:{gitHead, treeClean, treeHash}, buildOk, errors, projects:[{path, tier, role, files, symbolUses}],
 findings:[{ruleId, class, severity, project, file, line, column, symbol, message, origins}],
 summary:{det:{bySeverity, total}, heu, pass}, run:{evaluatedAt, timingsMs}}
```

- Findings are sorted by file, line, column, rule, symbol and message.
- The JSON writer is deterministic: fixed member order, LF line endings and invariant
  number formatting.
- Two runs on the same tree are byte-identical except for `run`. An integration test
  checks this.

## Integrity

- The policy, probes and contract must be outside `--repo`. Otherwise the run is
  refused with exit 2.
- The only processes started are `git` (read-only queries) and `dotnet`
  (`build`, `msbuild` evaluation and design-time compile, `--version`). No code from
  the repository is executed by the verifier itself.
- MSBuild does run whatever targets the repository's project files and imports define,
  including during NuGet restore. That is inherent to `dotnet build`, so a hostile
  repository can still run code at build time. Run the verifier in the same sandbox as
  the build.
- The report binds the result to `gitHead`, `treeClean`, `treeHash` (computed before the
  build), the policy's sha256, the verifier assembly's sha256, the FCS version and the
  SDK version.

## Known limits (what AST and symbol analysis cannot decide)

- **Indirect effects.** An effect reached through a function value, an interface, a
  port, reflection (`Type.GetType "System.IO.File"`), `dynamic`/`?` operators, P/Invoke,
  or a lower-tier helper is attributed to the code that names the symbol, not to the
  caller. A Tier 2 function that calls a Tier 1 function that does I/O is reported in
  Tier 1 only.
- **Inlined and SRTP code.** FSharp.Core functions with effects (`printfn`, `stdout`)
  are only caught because the policy lists them. Any other library wrapper around a
  forbidden API is invisible unless listed.
- **No decision logic.** "Tier 3 decides legality" (AR-07), effect flow (AR-09) and
  "single authority for a duplicated fact" (AR-19) need semantic judgement. These are
  ARC-REV-01..03. ARC-HEU-02 and HEU-03 only point at candidates and have false
  positives and false negatives: a constant computed rather than written, a predicate
  phrased differently, logic hidden in a non-operator function.
- **Scopes are syntactic.** Module scopes come from `namespace`/`module` declarations.
  An anonymous top-level module (a file without a `module` or `namespace` line) is
  scoped by its implicit file-name module and will not match `Lending.Host.Cli`. Code
  moved into a differently named namespace inside the Host project is checked under that
  namespace.
- **F# only.** `.csproj` projects take part in the project and package rules, but their
  code is not type-checked. Test projects are parsed only, for ARC-TRC-01.
- **ARC-TRC-01 is textual.** It checks that the id appears in a comment or test name, not
  that the commented code implements the decision.
- **Build-dependent.** The verifier needs a successful restore and build. A repository
  that does not build cannot be evaluated (exit 2), and no partial findings are
  reported.
- **Tree hash.** The tree hash uses raw file bytes. It equals `git write-tree` unless
  clean or smudge filters (autocrlf, LFS) are configured. Submodules are not hashed.

## Layout

```
src/Archcheck/        Domain (facts, catalogue) · Json · Paths · Policy · Exec · Provenance · MsBuild
                      Syntax · Symbols · Rules (DET) · Heuristics (HEU) · Report · Verify · Selftest · Program
tests/Archcheck.Tests unit tests on synthetic facts, policy decoding, parse facts, tree hash; integration tests
tests/samples/<name>/ repo/ + expected.json (+ contract.json / probes.json)
policy/               lending.policy.json
```

| Sample | Expectation |
|---|---|
| `clean` | clean four-tier layout; comments mention `System.IO`, `DateTime.Now` and Console |
| `dep01-upward`, `dep02-package` | upward edge; Tier 2 package reference (unused) |
| `sym01-qualified` | `System.IO.File.ReadAllText` fully qualified, with no `open` |
| `sym01-alias` | `type Disk = System.IO.File` and `open type Term` (`System.Console`) |
| `sym02-clock` | `DateTime.Now` through a private type abbreviation in Tier 3; `Guid.NewGuid` in the CLI |
| `sym03-console` | `printfn` and `System.Console` in Tier 3 |
| `bnd01-persistence`, `bnd02-transition`, `bnd03-entity-field` | the three Tier 4 boundary rules (BND-03: pattern and dot reads flagged; `LoanId` and construction labels not) |
| `probe-bnd03` | passes the policy, fails a hidden per-task probe |
| `trc01-decisions` | one decision traced, one only in a test, one nowhere |
| `heu01-swallow` … `heu04-long-file` | one sample per heuristic |
| `neg-regex-trap` | user-defined `DateTime.Now` and `Console.WriteLine`, plus forbidden names in comments and strings: no findings |
| `err-unmapped`, `err-build`, `err-policy-in-repo`, `err-dirty` | the exit-2 paths |
| `baseline-moved-lines` | ARCH-002: the base tree's ARC-SYM-02 finding only moves down; preexisting, exit 0 |
| `baseline-new-and-preexisting` | ARCH-002: a second same-key clock read; one new (the added line 6), one preexisting, exit 1 |
| `baseline-relocated` | ARCH-002: the read moved to another module and file; new (exit 1), the old key is fixed |

## ARCH-002: brownfield baseline (`--baseline REPORT.json`)

ARCH-002 fixtures start with violations, so a trial is judged by what it *adds* (ARCH-002 INTERFACES §3).

- **Input.** A report this verifier wrote for the start commit (`arch001`/`arch002.verifier-report/1`, no
  `errors`). Like the policy, probes and contract, it must be outside `--repo`, or the run exits 2. A malformed
  baseline also exits 2.
- **Key.** A finding's key is `(ruleId, file, symbol, scope)`, where `scope` is the innermost enclosing namespace or
  module of the finding's site (new report member; `""` for project-level findings such as ARC-DEP-01/02 and
  ARC-HEU-04). Line and column are not part of the key, so a violation that only moved is not new. A violation moved
  to another file or module *is* new, and its old key is reported as fixed.
- **Multiset.** Keys are compared as multisets: with a key twice in the baseline and three times now, exactly one
  finding is new. Which one is decided by the trimmed source line (`context`, new report member): a finding whose
  line text equals a baseline finding's is matched first, so the new finding reported is the added line, not the
  old line that moved. This choice never changes how many findings are new. A baseline written before `scope`
  existed matches on rule, file and symbol alone.
- **Marking.** Every DET and HEU finding gets `preexisting: true|false`. Without `--baseline` every finding is
  `false`, and every ARCH-001 behaviour is unchanged.
- **Exit code.** 0 = no *new* (non-preexisting) DET finding of severity >= 2; 1 = at least one; 2 = could not
  evaluate. Pre-existing findings never fail the gate.
- **Report.** `findings[].scope`, `findings[].context`, `findings[].preexisting`; `summary.new` and
  `summary.preexisting` (each `{det: {bySeverity, total}, heu}`; `summary.det`/`heu` still count every finding,
  `summary.pass` is decided on `new`); `baseline: {id, sha256, findings, matched, fixed: [keys]}` (null without a
  baseline). The schema id is `arch002.verifier-report/1` (additions only).
- **Text output.** Pre-existing findings carry ` [preexisting]`; the summary line adds
  `baseline <id>: new DET sev>=2=N, preexisting=M, fixed=K`.
- **Code.** `src/Archcheck/Baseline.fs` (pure: `decode`, `withContext`, `mark`); `Verify.run` reads the file and
  applies it after the rules; tests in `tests/Archcheck.Tests/BaselineTests.fs` and the three `baseline-*` samples
  (`expected.json` keys `baselineRepo`, `new`, `preexisting`, `fixed`, `newLines`: selftest evaluates the sample's
  `base/` tree first and uses that report as the baseline of `repo/`).
