# Summa architecture

This document applies `FOUR-TIER-ARCHITECTURE.md` (SDE-DOCTRINE-003 v0.2.1, in this
directory) to the Summa repository. It adds no principle of its own: every rule below is
an instance of a statement in that doctrine, which is cited. Where the two seem to
differ, the doctrine wins.

Summa's own `context/ARCHITECTURE.md` names its layers Domain, Engine, Application, Host
and Pages. This document maps them onto the doctrine's four tiers.

## 1. Tier map

| Tier | Doctrine name | Projects | Namespaces |
|---|---|---|---|
| 1 | Semantic Model | `src/Summa.Contracts`, `src/Summa.Access`, `src/Summa.Ledger` | `Summa.Contracts`, `Summa.Access`, `Summa.Ledger` |
| 2 | State Transition / Domain Execution | `src/Summa.Storage`, `src/Summa.Web.Engine` | `Summa.Storage`, `Summa.Web.Engine` |
| 3 | Application / Projection / Orchestration | `src/Summa.Web.Application` | `Summa.Web.Application` |
| 4 | Host / External Effects | `src/Summa.Wasm` (C#), `src/Summa.Operations`; the browser pages `app/`, `web/`, `web-hub/`, `web-kernel/` | `Summa.Wasm`, `Summa.Operations` |

- `Summa.Ledger`, `Summa.Access` and `Summa.Contracts` hold both semantic values and the
  financial rules over them. The doctrine speaks of "Tier 1/2" for such code; they are
  mapped to Tier 1 because nothing they reference may be higher.
- `Summa.Storage` decides persistence as data: the storage format, the record checks and
  the command-to-commit rules. An Arca provider performs every read and commit. It is
  Tier 2.
- `Summa.Web.Engine` holds each page's state, its transitions and the requests it
  describes as data, and projects the page's view. It is Tier 2.
- **Composition root.** `Summa.Web.Application.Runtime` (`src/Summa.Web.Application/Runtime.fs`)
  is the composition root the WebAssembly shim calls. It reads the clock, the random
  source and GUIDs, and builds the providers. It is Tier 4 code, kept in the Tier 3
  project because the shim cannot hold state between calls. The rules below name it as
  an exception where it applies.

Tests (`tests/`) are not production code and may use any tier.

## 2. Allowed dependency directions

Dependencies point downward only (doctrine, "Dependency direction"):

    Summa.Wasm, Summa.Operations  ->  Summa.Web.Application  ->  Summa.Web.Engine, Summa.Storage  ->  Summa.Ledger, Summa.Access, Summa.Contracts

A project may depend on any lower tier, not only the adjacent one, and on a project of
its own tier. An edge to a higher tier is a violation.

## 3. Responsibility placement

| Responsibility | Tier | Where in this repository |
|---|---|---|
| Money, accounts, journal entries, customers, invoices, payments, credits, periods: the values and the financial rules over them (posting, settlement, aging, reports, documents' content) | 1/2 | `Summa.Ledger` |
| Capabilities and roles | 1/2 | `Summa.Access` |
| The external contract types and their canonical codec | 1/2 | `Summa.Contracts` |
| Persistence decisions as data: record format, checks, migrations, export metadata, the browser snapshot | 2 | `Summa.Storage` |
| A page's state and transitions, the requests it describes as data, its view projection | 2 | `Summa.Web.Engine` |
| The Limen protocol: kernel messages in, engine messages out; engine effects out as kernel requests; the Aegis boundary | 3 | `Summa.Web.Application` (`AccountingWire`, `BacklogWire`, `HubWire`, `Limen`, `Json`, `Replies`, `Boundary`, `Bridge`) |
| Coordinating the store and sign-in through the providers | 3 | `Summa.Web.Application` (`Store`, `Identity`) |
| Clock, randomness, providers, browser interop, backups | 4 | `Summa.Web.Application.Runtime` (composition root), `Summa.Wasm`, `Summa.Operations`, the browser pages |

External effects follow the doctrine's flow: Tier 2 decides and requests the effect as
data (an engine effect); Tier 3 coordinates it (the wire turns it into a kernel request);
Tier 4 performs or observes it (the browser kernel, a provider); Tier 2 interprets the
result. An Unknown outcome is kept as an explicit value; it is not turned into a failure
or swallowed, and Tier 1/2 does not perform the probe.

Tier 3 must not become a second semantic authority: it does not decide which states or
transitions are legal, and it does not compute financial facts; Tier 1/2 does.

## 4. Rules

Each rule has the id used by the architecture check. "Tier 1/2" means every project of
Tiers 1 and 2 in §1.

### Dependency rules

- **ARC-DEP-01.** No project references a project of a higher tier (§2). *Doctrine:
  "Dependencies point downward only."*
- **ARC-DEP-02.** Tier 1/2 projects reference no package and no assembly beyond
  FSharp.Core, the .NET base library, `EchelonFoundry.Arca.Core` (Arca's pure record and
  storage model, with no provider) and `EchelonFoundry.Limen.Routing` (Limen's pure
  router). *Doctrine: Tier 1 "must not know about … frameworks, … infrastructure"; "No
  Ordo feature may require Tier 1/2 to … import … provider SDK, persistence-adapter …
  dependencies."*

### Symbol rules

- **ARC-SYM-01.** Tier 1/2 code uses no symbol from `System.IO`, `System.Net`,
  `System.Text.Json`, `System.Data`, `System.Diagnostics.Process`, `System.Console`,
  `System.Environment`, and performs no `System.Threading.Tasks` effects (`Task.Run`,
  `Task.Delay`, `Task.Factory`, `Task.Start`, `Task.Yield`, `TaskFactory`, `Parallel`).
  Console output through F#'s `printf`/`printfn`/`eprintf`/`eprintfn` and the
  `stdin`/`stdout`/`stderr` values counts as `System.Console` use, and
  `System.Diagnostics.ProcessStartInfo` as `System.Diagnostics.Process` use. *Doctrine:
  Tier 1 must not know about JSON, serialization, filesystems; Tier 2 "does not perform
  uncontrolled infrastructure effects".*
- **ARC-SYM-02.** No code outside the composition root (`Summa.Web.Application.Runtime`)
  reads the clock, randomness or GUID generation (`DateTime.Now`, `DateTime.UtcNow`,
  `DateTime.Today`, `DateTimeOffset.Now`, `DateTimeOffset.UtcNow`, `System.Random`,
  `Guid.NewGuid`, `Stopwatch`). The time reaches the engine with each message (`Ctx.Now`)
  and the wire through its `Env`. *Doctrine: Tier 4 "owns … clock".*
- **ARC-SYM-03.** Tier 3 code outside the composition root uses no symbol from
  `System.IO`, `System.Net`, `System.Console` (including `printf`-family console output);
  it reaches the outside world only through the kernel's requests and the providers.
  Writing and reading the protocol's JSON is boundary translation and belongs to Tier 3.
  *Doctrine: Tier 3 coordinates "boundary translation"; Tier 4 owns filesystem, network.*

### Boundary rules inside Tier 3

- **ARC-BND-01.** Tier 3 code outside the composition root uses no symbol of the GitHub
  storage and sign-in adapters (`Arca.GitHub`, `Fides.Client`). *Doctrine: Tier 4 owns
  "network, HTTP, … external services"; Tier 3 coordinates them.*
- **ARC-BND-02.** Tier 3 code outside the composition root calls no function, method or
  active pattern of `Summa.Ledger`. Financial decisions reach the boundary through the
  engine (`Summa.Web.Engine`), which takes them from `Summa.Ledger`; types and union
  cases may be named. *Doctrine: Tier 3 "must not become a second semantic authority";
  the effect flow "Tier 2: decide → Tier 3: coordinate".*
- **ARC-BND-03.** Tier 3 code outside the composition root reads no field of a
  `Summa.Ledger` record other than identifiers (`Id`, `*Id`); it writes out the engine's
  view (`Accounting.view`) and effects. *Doctrine: Tier 3 coordinates projections and
  boundary translation; it does not re-derive financial facts.*

### Findings that are reported but do not fail the check

- **ARC-HEU-01.** A catch-all exception handler in Tier 1–3 that does not re-raise, or an
  Unknown outcome collapsed into a failure. *Doctrine: Unknown is "an explicit,
  first-class outcome, not a swallowed exception".*
- **ARC-HEU-02.** A number written in two tiers. *Doctrine: Tier 3 must not become a
  second semantic authority.*
- **ARC-HEU-03.** Comparisons or arithmetic on `Summa.Ledger` values in
  `Summa.Web.Application`. *Doctrine: decisions belong to Tier 1/2.*
- **ARC-HEU-04.** A source file longer than 500 lines. *Doctrine: "Layering does not
  imply one file per tier"; see Structural Locality.*

### Decision traceability (only when the task comes with a decision contract)

- **ARC-TRC-01.** Every `decision` node id in the task's `contract.json` appears in a
  comment in the production code that implements it and in a test (its name or a
  comment).

## 5. Existing code

These rules apply to the changes you make. Some code already in this repository predates
them; the check counts only findings that are new relative to the commit you start from,
and it never requires you to change code you did not otherwise need to touch.
