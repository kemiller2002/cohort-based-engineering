# Lending architecture

This document applies `FOUR-TIER-ARCHITECTURE.md` (SDE-DOCTRINE-003 v0.2.1, in this
directory) to the Lending repository. It adds no principle of its own: every rule below
is an instance of a statement in that doctrine, which is cited by section. Where the two
seem to differ, the doctrine wins.

## 0. Existing code and new work

The repository is not clean. Some of its existing code breaks the rules in §4, and
some features are layered differently from others. Existing code is not a precedent: where
it and this document disagree, this document wins.

New work must not add a new violation of the rules in §4. It need not fix existing
violations; it may fix one it touches, as long as behaviour is kept. The architecture
check compares a change with the code it started from, so a violation that was already
there does not count against the change, and a new one does.

## 1. Tier map

| Tier | Doctrine name | Project | Namespace |
|---|---|---|---|
| 1 | Semantic Model | `src/Lending.Semantic` | `Lending.Semantic` |
| 2 | State Transition / Domain Execution | `src/Lending.Transition` | `Lending.Transition` |
| 3 | Application / Projection / Orchestration | `src/Lending.Application` | `Lending.Application` |
| 4 | Host / External Effects | `src/Lending.Host` | `Lending.Host` |

Inside Tier 4:

| Part | Namespace / module | Role |
|---|---|---|
| Persistence | `Lending.Host.Persistence` | adapters that implement the `Store`, `Files` and `Archive` ports (in-memory and JSON file stores, local files, JSON backups) |
| Command line | `Lending.Host.Cli` | presentation: parse command text, call a Tier 3 use case, render a Tier 3 view as text |
| Composition root | `Lending.Host.Composition` | reads the clock, chooses the adapters, builds the `Ports` record, runs the program |

Tests (`tests/`) are not production code and may use any tier.

## 2. Allowed dependency directions

Dependencies point downward only (doctrine, "Dependency direction"):

    Lending.Host  ->  Lending.Application  ->  Lending.Transition  ->  Lending.Semantic

A project may depend on any lower tier, not only the adjacent one. An edge to the same or
a higher tier is a violation.

## 3. Responsibility placement

| Responsibility | Tier | Where in this repository |
|---|---|---|
| Identifiers, entities, closed alternatives, state, obligations, uncertainty | 1 | `Lending.Semantic` |
| Lending rules: guards, invariants, transitions, policy values from `docs/decisions`, requested effects (as data), interpretation of effect outcomes | 2 | `Lending.Transition` (policy values in `Policy`) |
| Use cases: translate input, call Tier 2, persist through the `Store` port, request effects through ports, project view models | 3 | `Lending.Application` (`Ports`, `UseCases`, `Views`) |
| Ports (records of functions the application needs from the outside world) | 3 | `Lending.Application.Ports` |
| Storage, files, clock, notification channels, console, start-up | 4 | `Lending.Host` |

External effects follow the doctrine's flow: Tier 2 decides and requests the effect as
data; Tier 3 coordinates; Tier 4 performs or observes it; Tier 2 interprets the result as
Succeeded, Failed or Unknown. An Unknown outcome is kept as an explicit value (for
example a reconciliation obligation in Tier 1/2 state); it is not turned into a failure
or swallowed, and Tier 1/2 does not perform the probe.

Tier 3 must not become a second semantic authority: it does not decide which states or
transitions are legal; Tier 2 does.

## 4. Rules

Each rule has the id used by the architecture check. "Tier 1/2" means
`Lending.Semantic` and `Lending.Transition`.

### Dependency rules

- **ARC-DEP-01.** No project references a project of a higher tier (§2). *Doctrine:
  "Dependencies point downward only."*
- **ARC-DEP-02.** Tier 1/2 projects reference no package and no assembly beyond
  FSharp.Core and the .NET base library. *Doctrine: Tier 1 "must not know about …
  frameworks, … infrastructure"; "No Ordo feature may require Tier 1/2 to … import …
  persistence-adapter … dependencies."*

### Symbol rules

- **ARC-SYM-01.** Tier 1/2 code uses no symbol from `System.IO`, `System.Net`,
  `System.Text.Json`, `System.Data`, `System.Diagnostics.Process`, `System.Console`,
  `System.Environment`, and performs no `System.Threading.Tasks` effects. Console output
  through F#'s `printf`/`printfn`/`eprintf`/`eprintfn` and the `stdin`/`stdout`/`stderr` values counts as
  `System.Console` use, and `System.Diagnostics.ProcessStartInfo` as `System.Diagnostics.Process` use. *Doctrine:
  Tier 1 must not know about JSON, serialization, filesystems; Tier 2 "does not perform
  uncontrolled infrastructure effects".*
- **ARC-SYM-02.** No code outside the composition root (`Lending.Host.Composition`)
  reads the clock, randomness or GUID generation (`DateTime.Now`, `DateTime.UtcNow`,
  `DateTime.Today`, `DateTimeOffset.Now`, `DateTimeOffset.UtcNow`, `System.Random`,
  `Guid.NewGuid`, `Stopwatch`). Today's date reaches the application through the
  `Clock` port. *Doctrine: Tier 4 "owns … clock".*
- **ARC-SYM-03.** Tier 3 uses no symbol from `System.IO`, `System.Net`,
  `System.Text.Json`, `System.Console` (including `printf`-family console output); it reaches
  the outside world only through ports.
  *Doctrine: Tier 3 coordinates; Tier 4 owns filesystem, network, database.*

### Boundary rules inside Tier 4

Presentation means every module of the `Lending.Host` project other than
`Lending.Host.Persistence` (adapters) and `Lending.Host.Composition` (the composition root):
`Lending.Host.Cli` and any new presentation module, whatever it is named.

- **ARC-BND-01.** Presentation (`Lending.Host.Cli`) uses no symbol from `Lending.Host.Persistence`; it
  reaches state only through `Lending.Application` use cases. *Doctrine: Tier 3
  "coordinates use cases"; Tier 4 presentation does not bypass it.*
- **ARC-BND-02.** Presentation and `Lending.Host.Persistence` call no function of
  `Lending.Transition`. Decisions are made in Tier 2 and coordinated by Tier 3, never
  re-entered from Tier 4. *Doctrine: the effect flow "Tier 2: decide → Tier 3:
  coordinate → Tier 4: perform or observe".*
- **ARC-BND-03.** Presentation reads no field of a Tier 1 entity record other than
  identifiers; it renders Tier 3 view models (`Lending.Application.Views`). *Doctrine:
  Tier 3 owns projection.*

### Findings that are reported but do not fail the check

- **ARC-HEU-01.** A catch-all exception handler in Tier 1–3 that does not re-raise, or
  an Unknown outcome collapsed into a failure. *Doctrine: Unknown is "an explicit,
  first-class outcome, not a swallowed exception".*
- **ARC-HEU-02.** A lending rule's number, date offset or condition written in two
  tiers. *Doctrine: Tier 3 must not become a second semantic authority.*
- **ARC-HEU-03.** Comparisons or arithmetic on lending values (dates, amounts, counts)
  in `Lending.Host`. *Doctrine: decisions belong to Tier 2.*
- **ARC-HEU-04.** A source file longer than 500 lines. *Doctrine: "Layering does not
  imply one file per tier"; see Structural Locality.*

### Decision traceability (only when the task comes with a decision contract)

- **ARC-TRC-01.** Every `decision` node id in the task's `contract.json` appears in a
  comment in the production code that implements it and in a test (its name or a
  comment).

## 5. Ports

`Lending.Application.Ports` defines `Store`, `Notifier`, `Files` (reading and writing
text files), `Archive` (whole-state snapshots at a path, for backups) and the `Ports`
record (store, clock, notifier, files, archive). Tier 4 implements them
(`Lending.Host.Persistence`, `Lending.Host.Composition`) and passes the record to the
command line, which passes it to use cases. A new external effect gets a port in Tier 3
and an adapter in Tier 4; tests build the `Ports` record themselves, so an existing port
is used where one fits.
