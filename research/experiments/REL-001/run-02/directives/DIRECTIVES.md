# Echelon engineering directives (REL-001 run-02 pack)

Assembled verbatim from Echelon documents for arms B, C and D of REL-001 run-02.
Headings of the form `## From ...` are added by the assembler; every other line is
copied unchanged from the source named in the heading. Sources, digests and every
removed passage are listed in `PROVENANCE.md`.

## From praxis: `AGENTS.md`

## Start Here

2. Identify the task's scope and operating mode.
3. Locate the applicable canonical domain records; inspect the repository and user changes before editing.
4. State or record material unknowns, constraints, assumptions, and risks.
5. Use the smallest process that preserves correctness, traceability, and continuity.
6. Execute, validate, update affected records, and leave a handoff.

## Authority

Apply, in descending order: explicit user instruction; applicable safety, legal, and platform constraints; canonical governance; accepted domain REPs and theory; accepted architecture and decision records; current implementation; local convention; agent preference. A higher authority cannot authorize a violation of an applicable safety or legal constraint. When same-level sources conflict, prefer the narrower and newer accepted record and document the resolution; escalate if the outcome materially changes the authorized goal.

## Core Rules

- Never fabricate evidence, file reads, approvals, commands, test results, or certainty.
- Preserve user work. Inspect before modifying; do not destroy or irreversibly migrate without authorization.
- Make reasonable, reversible, in-scope decisions. Escalate high-impact irreversible, security/privacy-sensitive, legally ambiguous, or materially out-of-scope decisions.
- Research by testing hypotheses against confirming and falsifying evidence. Engineering by establishing a baseline, defining acceptance criteria, making the smallest robust change, and testing in proportion to risk.
- Do not silently change canonical policy. Propose or record the change, its evidence, consequences, version, and migration path.
- Do not claim a test passed unless it ran and passed. Name skipped or unavailable checks and their implications.

## Handoff

For substantial work, record: objective; work completed; files changed; decisions and assumptions; tests run and results; evidence added; unresolved questions; risks; and next recommended action. A capable successor must be able to continue without the originating conversation.

## From praxis: `docs/agent-mistake-prevention.md`

The objective is to eliminate specific invalid actions before effects occur.

Types should carry established facts and constrain available operations. A new
wrapper with a public constructor, a boolean `validated`, or a worker-editable
policy file is not prevention.

## From dokimos: `docs/rules/DOK-FS-001.md`

# DOK-FS-001 — Ambiguous F# record inference at evidence boundaries

Dokimos has encountered the same compiler-inference failure in multiple modules where related records intentionally share field names. F# may infer the wrong record type before later field access disambiguates intent.

## Rule

At public/core transformation boundaries involving record types with overlapping labels, explicitly type parameters when inference would otherwise depend on later field access.

## Why this is a candidate quality rule

The rule is not "all parameters require annotations." It applies only when evidence demonstrates ambiguity risk. The purpose is to make the intended domain boundary explicit and prevent a known recurring failure mode.

## From dokimos: `docs/rules/DOK-COMPLEXITY-001.md`

# DOK-COMPLEXITY-001 — Lexical complexity proxy

## Known limitation

F# discriminated-union and pattern-matching code can contain many match arms while remaining explicit, exhaustive, and maintainable. Therefore a high lexical proxy value is not by itself evidence of poor code quality.

- Pattern-match exhaustiveness and declarative union handling must not be penalized merely for having multiple cases.

## From dokimos: `docs/quality/RATCHET-RULES.md`

Unavailable evidence is the verdict `unavailable`. It is never a pass.

| Rule | Name | Scope | Signal | Rationale | Remediation |
|---|---|---|---|---|---|
| DOK-R001 | compiler-warnings | repository | MSBuild `N Warning(s)` summary of `--build-log` | Warnings are deferred defects; a growing count hides new ones | Fix the warnings; do not suppress them (that is R002) |
| DOK-R002 | warning-suppressions | file | `#nowarn`, `#pragma warning disable`, `[<SuppressMessage>]`; project `<NoWarn>` (other than an inherited `$(NoWarn)`), `<WarningsNotAsErrors>`, `NoWarn="..."`, `TreatWarningsAsErrors=false` | A suppression silences evidence for every future change | Fix the underlying warning, or except it with the false-positive rationale |
| DOK-R003 | skipped-tests | file | `Skip = "..."`, `[<Ignore>]`, `[<Explicit>]`, Expecto `ptest*`, `Skip.If/IfNot`, `Assert.Skip` | A skipped test reports success while verifying nothing | Make it pass or delete it with a reason; quarantine only through a dated exception |
| DOK-R004 | debt-markers | file | Comment lines with the whole words TODO, FIXME or HACK | Growth means work declared done while incomplete | Finish it, or track it in the work queue and remove the marker |
| DOK-R005 | large-file-growth | file | Line count of handwritten `.fs` files over `largeFileLines` (default 400) | Growth of an already-large file concentrates responsibility; size is a review signal, not a verdict | Extract a cohesive responsibility first, or except it with a cohesion rationale |
| DOK-R006 | broad-exception-catches | file | try/with handlers catching everything (`_`, an identifier, `:? exn`, `:? Exception`) that are wildcards or never use the exception (same line or the next code line) | Catch-all-and-discard turns failures into silent defaults | Catch specific exceptions and return typed errors, or let faults reach the fault boundary |
| DOK-R007 | package-references | file | `<PackageReference Include=...>` per `.fsproj` / `Directory.Build.props` / `Directory.Packages.props` | Each dependency adds supply-chain, upgrade and boundary cost | Remove it, or except it with justification and owner |
| DOK-R008 | architecture-violations | repository | `<ProjectReference>` edges forbidden by the baseline's `forbiddenReferences` layer map (`Architecture.boundaryViolations`) | Dependency direction is the architecture | Move the shared concept down a layer or invert the dependency |

## From ordo: `doctrine/STATE-DIRECTED-ENGINEERING.md`

## Bounded reasoning scope

> Make illegal states unrepresentable. Make illegal transitions unavailable.
> Make legal capabilities explicit. Establish semantic decisions once and
> derive their consequences where practical. Keep the reasoning context
> required for change bounded and deterministically discoverable. Use the
> earliest trustworthy mechanism capable of detecting each failure class, and
> require evidence when declared boundaries are crossed.

## From ordo: `doctrine/STATE-PROGRAMMING.md`

## What State Programming is

State Programming is a programming and architectural paradigm concerned
with making the legal evolution of a system's meaning explicit, so that a
change to that meaning is discoverable by mechanism rather than by
inference alone. Its central concepts:

- **Explicit semantic states** — what can be true is named, not inferred
  from a combination of flags or null checks.
- **Legal transitions** — what change may happen is a closed, checkable set,
  not an implicit consequence of arbitrary code paths.
- **Invariants** — properties that must hold across every reachable state.
- **Evidence** — the basis for believing a state is true, tracked
  explicitly rather than assumed.
- **Capabilities** — what an actor or state is permitted to do next.
- **Obligations** — what must still happen for a transition to be complete.
- **Effects** — externally-observable consequences, requested as data
  rather than performed directly by the code that decides them.
- **Uncertainty** — a first-class, explicit state (not silently mapped to
  `null`, an exception, or a default) for "we do not yet know the outcome."
- **Constrained legal evolution** — the system can only move between states
  in ways the model actually permits.
- **Boundary preservation** — semantic information does not degrade for
  free when it crosses a responsibility boundary (see
  [`BOUNDARY-PRESERVATION.md`](BOUNDARY-PRESERVATION.md)).
- **Mechanically discoverable change obligations** — when a semantic
  decision requires a corresponding change elsewhere, that requirement
  should be discoverable by a mechanism (compiler, architecture check,
  contract test), not solely by a human or agent remembering it.
