# ARCH-001 Workstream A: Architecture Specification Inventory

Worker: A (architecture inventory). Read-only research. Date: 2026-10-21.

Commits read (they match `coordination.json` pins):

| Repo | Commit |
|---|---|
| ordo | `bb43c26c106f4cbe972234636c5c67edc235c188` |
| praxis | `986211c19161bab339eebc565fb4d8edb2007d38` |
| dokimos | `04b5f856367b47a087285109c1fc5923ec351389` |
| summa | `8b0e93ea7c57934acaa20a7eabd4d67f26efcae4` |
| signal | `e19101f536e033acba8f67b479d4c767f85028f9` |
| visual-engineering | `1bda5ff24493d75af02e02df4ca11fe1a417fc5c` (context only) |
| echelon-foundry (cloned anonymously; not pinned) | `8c6b45358fb1bcae4f612534637077d35dd72762` |

Citation abbreviations:

- **FT** = `.sde/architecture/FOUR-TIER-ARCHITECTURE.md` as installed in summa and
  signal. The two copies have the same SHA-256
  (`9f6c2757…d61b`, per each repo's `.sde/MANIFEST.json`) and are byte-identical to the
  visual-engineering and echelon-foundry copies. The source is
  `ordo/doctrine/FOUR-TIER-ARCHITECTURE.md`. It differs only in the `related_documents`
  front matter, so its line numbers are **+3** from line 12 onward.
- **BP** = `.sde/architecture/BOUNDARY-PRESERVATION.md`
- **SL** = `.sde/architecture/STRUCTURAL-LOCALITY.md`
- **DES** = `.sde/architecture/DECISION-AND-EVIDENCE-SEMANTICS.md`
- **CM / VM / CC / AER** = `.sde/method/CONSTRUCTION-METHOD.md`, `VERIFICATION-METHOD.md`,
  `CHANGE-CLASSIFICATION.md`, `AGENT-EXECUTION-RULES.md`

All the `.sde/` paths above are relative to `/home/user/kemiller2002/summa/` and are identical in signal.

---

## 1. Authoritative specification

### 1.1 Primary authority: SDE Four-Tier Architecture

A formal four-tier specification **does exist**:

- Document: `FOUR-TIER-ARCHITECTURE.md`, **id `SDE-DOCTRINE-003`**, `status: accepted`,
  `version: 0.2.1`, created 2026-09-02, updated 2026-09-20 (FT:1-14).
- Normative force: "Status: `supported` theory (see `TH-SDE-2026-0001`), REQUIRED as SDE's
  canonical architectural layering." (FT:19-20)
- Distribution: it is authored in Ordo (`ordo/doctrine/`). It is shipped by the npm package
  `@echelon-foundry/sde`, whose source is `ordo/distribution/package.json` (current version
  1.17.0). `ordo/distribution/DISTRIBUTION-MAP.json:31-32` maps
  `doctrine/FOUR-TIER-ARCHITECTURE.md` to `architecture/FOUR-TIER-ARCHITECTURE.md`.
- The package installs it in each Echelon application under `.sde/`:
  - summa has SDE 1.8.2 installed (`summa/.sde/VERSION`);
  - signal has SDE 1.7.0 installed (`signal/.sde/VERSION`).
- `.sde/README.md:20` tells agents: "Apply the architecture documents in `architecture/` relevant to the change."
- `.sde/README.md:25-27` says files under `.sde/` "are versioned methodology inputs. Do not modify them directly."

Supporting records:

- Theory `ordo/research/theories/TH-SDE-2026-0001--four-tier-architecture.md`: `status: supported`,
  `confidence_estimate: 0.75` (lines 1-14). Its statement is at lines 18-25.
- Evidence `ordo/research/evidence/EV-HN-2026-0001--four-tier-and-boundary-architectural-layering.md`
  (`status: accepted`). The source is HelixNote at commit `211462a9…`.

Companion doctrine. These documents are installed with FT and reference it:

| Doc | ID | Status / version | Role relative to tiers |
|---|---|---|---|
| BP | SDE-DOCTRINE-004 | accepted 0.2.0 | "Boundary Preservation is not a fifth tier": what happens to values crossing tiers (BP:20-25) |
| SL | SDE-DOCTRINE-008 | accepted 0.2.0 | Feature locality and composition within tiers |
| DES | SDE-DOCTRINE-009 | accepted 0.1.0 | "Four-tier preservation is non-negotiable" (DES:20-27) |
| CC / CM / VM | method v0.2 | installed | Change classes per tier; architecture checks in the construction order |

### 1.2 Verbatim tier names and responsibilities (FT:36-86)

| Tier | Verbatim name | Question / responsibility (verbatim or near-verbatim) | Cite |
|---|---|---|---|
| 1 | **Semantic Model** | "What can be true?" Includes "domain identifiers, values, closed alternatives, state-specific data, evidence, capabilities, obligations, uncertainty." "Must not know about: Postgres, HTTP, JSON, frameworks, browser APIs, serialization, filesystems, infrastructure." | FT:38-46 |
| 2 | **State Transition / Domain Execution** | "What legal change may happen?" Includes "commands/intents, transitions, guards, invariants, evidence requirements, capability requirements, outcomes, obligations, requested effects." "Does not perform uncontrolled infrastructure effects — effects are requested as data and executed by Tier 4." | FT:54-63 |
| 3 | **Application / Projection / Orchestration** | "Coordinates use cases, projections, commands, requested effects, and boundary translation. Must not become a second semantic authority — if Tier 3 starts making its own decisions about what states are legal, the Tier 1/2 boundary has failed." | FT:65-70 |
| 4 | **Host / External Effects** | "Owns database, network, HTTP, browser, filesystem, clock, queue, framework, external services, and WASM/browser interop. Reports what actually happened — including 'we do not know what happened' as an explicit, first-class outcome, not a swallowed exception." | FT:76-81 |

The same split is restated in DES:24-27:

- "Tier 1 owns semantic state, evidence, coverage, capabilities, obligations, and uncertainty."
- "Tier 2 owns pure decisions, guards, policy, transitions, and interpretation of effect results."
- "Tier 3 coordinates requests/results and boundary translation."
- "Tier 4 performs external effects and observations."

Naming note (FT:22-34): the vocabulary is an "SDE-migration-era synthesis" and "**is not the same
concept as HelixNote's own 'Four-Tier State-System Model'**". That other model classifies kinds
of state (Domain/Entity, Workflow/Process, Effect/External, Presentation/Interaction) and is
attributed to an external "Echelon Foundry" brief. The text says "Do not merge the two."

### 1.3 Other "four-tier" vocabularies found (not the SDE authority)

| Vocabulary | Where | Scope / status |
|---|---|---|
| Domain / Application / Infrastructure / CLI, with Contracts as a fifth project. Called "four-tier architecture". | `praxis/requirements/CODE-QUALITY-HARDENING.md:15-30` (PRX-QUAL-001, "Status: approved work plan"); `praxis/docs/planning.md:404-410` (tier table: Domain, Contracts, Application, Infrastructure, CLI) | **Praxis's own codebase only** |
| `--tier` values `domain`, `contracts`, `application`, `infrastructure`, `cli` | `praxis/docs/work-protocol.md:153-154`; copied to `summa/docs/work-protocol.md:153` and `signal/docs/work-protocol.md:153` | Work-item risk metadata, not an architecture rule |
| Limen app layout: "Four tiers: F# semantic/transition/application projects (the Limen *engine*), a C# `Microsoft.NET.Sdk.WebAssembly` shim …, and a `web/` kernel" | `summa/research/decisions/DF-SUMMA-FND-2026-0002--build-summa-on-the-full-echelon-foundation-stack.md:61` (accepted; describes vigila) | The "same way as the other Echelon applications" physical layout |
| Domain / Engine / Application / Host / Pages (five rows) | `summa/context/ARCHITECTURE.md:10-16` | Summa's current-architecture summary |
| Limen engine (pure) / engine (admin domain) / engine (application) / kernel (WASM shim) / kernel (browser) | `signal/context/ARCHITECTURE.md:9-15` | Signal's current-architecture summary |
| HelixNote "Four-Tier State-System Model" | Known only through EV-HN-2026-0001 | A state-kind taxonomy. The brief "was not located in either repository" (EV-HN-2026-0001:109-111). The echelon-foundry repo (`8c6b453`) has only the same `.sde/` copy and no separate brief. |

`praxis/aegis-boundaries.json` (and the `aegis-boundaries.json` files in summa and signal) is **not**
a layering spec. Aegis (`EchelonFoundry.Aegis.Core`) classifies *unexpected operational failures* at
declared process, HTTP or kernel-message boundaries, with redaction. Expected outcomes stay typed
(praxis/aegis-boundaries.json `$comment`; `summa/docs/requirements/ECHELON-SHARED-APPLICATION-FOUNDATIONS.md:56-88`).
It enforces nothing about dependency direction.

---

## 2. Dependency-direction rules

| # | Rule (verbatim / near-verbatim) | Cite |
|---|---|---|
| D1 | Diagram: Host / Infrastructure → Application / Orchestration → Transition / Domain Execution → Semantic Model | FT:88-101 |
| D2 | "Dependencies point downward only. Tier 1 never imports from Tier 2, 3, or 4." | FT:103 |
| D3 | "Ordo refines Tier 1/2 semantics; it does not alter the dependency direction." | FT:107 |
| D4 | "No Ordo feature may require Tier 1/2 to perform external I/O or import browser, network, database, filesystem, provider SDK, persistence-adapter, or ROS implementation dependencies." | FT:109 |
| D5 | "ROS is not Tier 5 … Application correctness and legal transitions must not depend on ROS being available." | FT:128 |
| D6 | "[DES semantics] do not create a fifth tier and they do not move I/O downward." | DES:22 |
| D7 | "Dependencies should be explicit and directional; circular semantic dependencies trigger architectural review." | SL:87-91 |
| D8 | Failure-detection order item 2: "architecture checks for illegal dependency direction" | CM:96; VM:33 |
| D9 | (Ordo construction, draft) Avoid "a dependency on a higher tier, or a stray infrastructure import". Compile-negative probe "FS0039: tiers are compiled in upward order". | `ordo/research/decisions/DF-SDE-2026-0019--…md:33-38, 101` (status: **draft**) |

The spec does not state:

- whether a tier may depend on any lower tier or only on the adjacent one (see §7 A2);
- which physical projects belong to which tier (see §7 A1).

---

## 3. Responsibility-placement rules

| # | Rule | Cite |
|---|---|---|
| P1 | Tier 1 holds identifiers, values, closed alternatives, state data, evidence, capabilities, obligations, uncertainty; it knows nothing of Postgres/HTTP/JSON/frameworks/browser/serialization/filesystems/infrastructure. | FT:42-46 |
| P2 | Tier 2 holds commands, transitions, guards, invariants, evidence/capability requirements, outcomes, obligations, requested effects. Effects are data. | FT:58-63; DES:25 |
| P3 | Tier 3 coordinates and translates; it **must not** decide what states are legal. | FT:67-70 |
| P4 | Tier 4 owns DB, network, HTTP, browser, filesystem, **clock**, queue, framework, external services, WASM/browser interop. Unknown is an explicit outcome. | FT:78-81 |
| P5 | Effect flow: "Tier 2: decide / request effect → Tier 3: coordinate boundary → Tier 4: perform or observe effect → Tier 2: interpret Succeeded / Failed / Unknown" | FT:111-124 |
| P6 | "An Unknown external outcome may create a Tier 1/2 reconciliation obligation, but Tier 1/2 does not perform the probe." / "Tier 1/2 expresses the state and obligation. Tier 3/4 performs the probe." | FT:126; DES:92-105 |
| P7 | Tiers "do not prescribe physical source-file size or require an entire tier … to live in one file." "Root application components primarily compose features; cross-feature access uses explicit contracts." | FT:132-151 |
| P8 | "Top-level application components should primarily compose, route, and coordinate bounded features. They should not accumulate every feature's state, transitions, rendering, and interaction behavior." | SL:83-85 |
| P9 | "Splitting an authority across files MUST NOT create independent copies of the rule it owns." | SL:57-59 |
| P10 | Presentation state is state (Elmish/MVU/Redux are not exempt). | SL:96-101; FT:153-155 (source +3) |
| P11 | Semantic change "Lives in Tier 1/2". Boundary change = "representation or communication across a Tier boundary". | CC:23-24, 33 |
| P12 | (App level, Signal) Engine side owns "domain state, legal transitions, scoring, validation, privacy rules, capabilities, obligations, effects-as-data, and view projection … Browser APIs and DOM authority do not belong here." The WASM shim: "One `[JSExport]`; no decisions." | `signal/src/Echelon.Signal.Engine/README.md:3-9`; `signal/context/ARCHITECTURE.md:14` |
| P13 | (App level, Summa) "The kernel decides nothing about money"; "Forma … holds none of Summa's rules". | `summa/tests/Summa.Web.Tests/ArchitectureTests.fs:26-45` (INV-ARCH-006/007) |
| P14 | (App level, Summa) "Domain code is functional: immutable values, total functions returning `Result` for expected failures, no hidden state." | `summa/context/ARCHITECTURE.md:34-35` |
| P15 | (Foundations) Expected domain outcomes stay typed. Unexpected operational failures at declared boundaries go through Aegis, configured once at composition/startup. | `summa/docs/requirements/ECHELON-SHARED-APPLICATION-FOUNDATIONS.md:56-72` (Status: Required); the signal copy is at line 57 onward |

---

## 4. Required abstractions and boundaries

What is documented:

- **Three Contract Model (REQUIRED)** (BP:79-113):
  - Semantic Contract: Tier 1/2's own types.
  - Host Contract, e.g. WASM engine ↔ browser kernel:
    - "effects described by a closed algebra, one constructor per legal operation";
    - "every boundary-crossing value gets an explicit, hand-written tagged-JSON rendering function, never a host language's or framework's default serializer";
    - "route/operation agreement checked by an automated test";
    - field/projection mappings "matched over the actual closed domain type, exhaustiveness-checked, never over an open string pair with a wildcard" (BP:84-96).
  - Public Integration Contract: "Rich on the inside, boring on the outside."
- **Wire Contract Rule (REQUIRED)**: "Wire representations must be deliberately specified and must not depend on incidental host-language or framework serialization behavior." The mechanism is RECOMMENDED, not prescribed (BP:115-122).
- **Principles (REQUIRED)**: Preserve closure, Delay weakening, Establish authority, Validate re-entry (BP:27-42).
- **Ports**:
  - Appear only in Ordo construction (DF-SDE-2026-0019, **draft**). "Tier 3 is generated only when ports are declared. It reads ports, delegates to Tier 2, has the host perform effects…; Tier 4 is never generated." `ordo/src/Ordo.Core/ConstructionLayout.fs:23` names the interface `I<Workflow>Ports`.
  - Praxis-internal: "Application code depends on typed ports, not concrete providers" (`praxis/requirements/CODE-QUALITY-HARDENING.md:27`).
- **Limen engine/kernel boundary**: `limen.config.json` lists `boundary.engine` and `boundary.kernel` paths (`summa/limen.config.json`, `signal/limen.config.json`). This is a Limen (foundation) boundary, not one defined by FT.

What is **not** documented in SDE doctrine: repositories (in the DDD sense), adapters as a
named pattern, dependency injection, or interface-per-port requirements for handwritten code.
Abstractions beyond the Three Contract Model are **missing** for Echelon applications.

---

## 5. How Summa and Signal implement it

Neither app declares a mapping from its projects to SDE Tiers 1-4. Their `context/ARCHITECTURE.md`
files use their own row labels (§1.3). Below are the **observed** graph and a **proposed** tier
mapping (mine, from each project's own header comment).

### 5.1 Summa (`/home/user/kemiller2002/summa`)

| Project | Own description (fsproj comment) | Proposed SDE tier | ProjectReference → | Packages |
|---|---|---|---|---|
| `Summa.Contracts` | "pure F# types, a canonical JSON codec … no I/O" (fsproj:3-13) | 1 (shared contract) | none | none (tested) |
| `Summa.Access` | capabilities, rosters, approval gates; "Pure, with no dependencies" (fsproj:3-9) | 1/2 | none | none |
| `Summa.Ledger` | "financial domain … Pure F#: no clock, storage, network or browser access" (fsproj:3-11) | 1/2 | Contracts, Access | none |
| `Summa.Storage` | storage format, manifests, codecs, command-to-commit rules; "Pure: an Arca provider … performs every read and commit" (fsproj:3-9) | 2/3 (ambiguous) | Ledger, Access | Arca.Core |
| `Summa.Web.Engine` | "Pure F#: state, transitions, request descriptions and view projection" (fsproj:3-7) | 2 (+3 projection) | Ledger, Storage | Limen.Routing |
| `Summa.Web.Application` | "application tier: Limen's protocol …, and the Aegis boundary"; "no browser, network or file access" (fsproj:3-6) | 3 (+ composition root) | Web.Engine | Aegis.Core, Fides.Client, Fides.Arca, Arca.GitHub |
| `Summa.Wasm` (C#) | `[JSExport]` shim | 4 | Web.Application | WASM SDK |
| `app/`, `web/`, `web-hub/`, `web-kernel/` | Limen kernel, Forma/Folio markup | 4 (browser) | n/a | npm |
| `Summa.Operations` | backups/restore "never in the WASM application"; uses AES-GCM (fsproj:3-8) | 4 (ops host) | Storage | Arca.Core |

Observed edges (all downward under the proposed mapping; no cycles):

```
Wasm → Web.Application → Web.Engine → {Ledger, Storage}
Storage → {Ledger, Access}
Ledger → {Contracts, Access}
Operations → Storage
```

Possible deviations (heuristic; none of them is asserted by a test):

1. `Summa.Ledger/Documents.fs:27` has `open System.Text.Json` and writes JSON with `Utf8JsonWriter`
   (line 300 onward). If Ledger is Tier 1, this conflicts with "Must not know about … JSON …
   serialization" (FT:45-46). The doc places that restriction on Tier 1 only (§7 A4).
2. Clock, RNG and Guid are read in `Summa.Web.Application/Runtime.fs:36-42`. The file calls itself
   "The composition root … The accounting application's clock is read here, the one place with
   effects." FT:78 puts the clock in Tier 4 (§7 A5).
3. `Summa.Web.Application` references provider SDKs (`Arca.GitHub`, `Fides.Client`; see `Store.fs:19`,
   `Identity.fs:17`). These are Tier 4 concerns hosted in what the app calls the "application tier".
4. `Summa.Web.Engine → Summa.Storage`: whether this edge is legal depends on Storage's tier (§7 A6).
5. `context/ARCHITECTURE.md:13` says Web.Engine is "Pure page decisions for the hub and backlog
   pages". `Summa.Web.Engine/Accounting.fs` (≥2,600 lines) also holds the accounting page. This is a
   documentation-drift observation only.

### 5.2 Signal (`/home/user/kemiller2002/signal`)

| Project | Role (`context/ARCHITECTURE.md:11-15`) | Proposed SDE tier | ProjectReference → | Packages |
|---|---|---|---|---|
| `Echelon.Signal.Engine` | "Assessment, scoring, session transitions, view projection" (pure) | 1/2 (+3 projection) | none | none |
| `Echelon.Signal.Admin` | deployment config, storage profiles, Arca namespace (pure, over Arca.Core) | 2 | Engine | Arca.Core, Limen.Routing |
| `Echelon.Signal.Application` | "Limen protocol, handshake, Aegis boundary" | 3 (+ composition root) | Engine, Admin | Aegis.Core, Aegis.Integration.GitHub, Arca.GitHub, Fides, Fides.Client, Fides.Arca |
| `Echelon.Signal.Browser` (C#) | "One `[JSExport]`; no decisions." | 4 | Application | WASM SDK |
| `web-kernel/`, `web/` | BrowserKernel start-up, Forma/Folio | 4 | n/a | npm |

Observed edges: `Browser → Application → {Engine, Admin}` and `Admin → Engine`. All are downward and acyclic.

Possible deviations (heuristic):

1. The Engine uses `System.Text.Json` in 9 files (`Canonical.fs`, `TemplateDecode.fs`, `ReportExport.fs`
   and others) and `System.Security.Cryptography` (hashing) in 5. Against FT:45-46 this is the same
   ambiguity as Summa item 1.
2. Clock, RNG and Guid are read in `Echelon.Signal.Application/Runtime.fs:36-41` and `Wire.fs:91-93`
   (Tier 3 project), as in Summa item 2.

### 5.3 Architecture tests in the apps

- **No test in either app asserts the project reference graph or tier membership.**
- The only graph-like assertion is `summa/tests/Summa.Contracts.Tests/PackageTests.fs:12-14`:
  Contracts has no `ProjectReference` and no `PackageReference`.
- `summa/tests/Summa.Web.Tests/ArchitectureTests.fs` (INV-ARCH-005..008; decision
  `research/decisions/DF-SUMMA-2026-0034--architectural-ownership-asserted-by-tests.md`) asserts
  foundation ownership. These are presentation and placement rules, not tier dependency rules:
  - Praxis validates in CI;
  - the browser is "Limen's kernel and nothing else" (one script; no `parseFloat`/`toFixed`/`Math.round`/`Intl.NumberFormat` in `web-kernel/limen-wasm.js`);
  - Forma presents;
  - Folio prints.
- INV-ARCH-001..004/009/010 live in `Summa.Storage.Tests`/`Summa.Tests` (record ownership, Ordo-style lifecycle).
- Route/operation agreement tests (BP:93) exist:
  - `summa/tests/Summa.Web.Tests/RoutesTests.fs`
  - `signal/tests/Echelon.Signal.Tests/RouteSchemaTests.fs:114-123`
- Foundations conformance (Aegis referenced, pinned, boundary codes declared): `summa/tests/Summa.Web.Tests/FoundationsConformanceTests.fs:135-140`; signal `FoundationsConformanceTests.fs:125`.

---

## 6. Existing mechanical enforcement

| Mechanism | What it checks | Status |
|---|---|---|
| `dotnet test` in `summa/.github/workflows/build.yml:42`, `signal/.github/workflows/build.yml:42` | The app tests in §5.3 (no tier-graph test) | **Implemented and run in CI**. It does not cover FT dependency rules. |
| `limen verify --strict` (`npm run check:limen`, build.yml:48/45; `limen-verify.yml:30`; signal `echelon-verification.yml` gate "Limen strict verification") | Limen engine/kernel boundary declared in `limen.config.json` | **Implemented and run**. The exact checks are not documented in the pinned repos (Limen source not inspected), so whether it inspects F# references is **unknown**. |
| `./praxis validate`, `./praxis registry check` (`praxis-validation.yml:19-20`, both apps) | Praxis work and records state. `praxis architecture check` checks the implementation-language policy only ("no prohibited repository-owned Node/JavaScript/TypeScript or Python automation", `praxis/src/Praxis.Cli/ArchitectureCommands.fs:1-49`) | Implemented and run. **Not a tier check.** |
| `npx @echelon-foundry/sde verify [--strict]` | Manifest hashes and the `SDE-STRUCT-001` source-size bands (500/1,000/2,000/4,000 lines) (`ordo/distribution/README.md:217-235`) | Implemented. Not seen in the summa/signal workflows I grepped. **No tier check.** |
| Praxis `tests/Praxis.Tests/ArchitectureTests.fs:9-31,110-122` | Exact ProjectReference graph for Praxis.Domain/Contracts/Application/Infrastructure/Cli; "Praxis.Domain must not reference an outward project"; Application must not reference Infrastructure/CLI; forbidden adapter tokens (`System.IO`, `HttpClient`, `ProcessStartInfo`, `File.`, `Thread.Sleep`…) in `Praxis.Application/Pacing/*.fs` and `PacingCommands.fs`; a self-test showing the guard rejects an outward Domain edge | **Implemented and run** (registered `tests/Praxis.Tests/Program.fs:15`; `praxis/.github/workflows/praxis-validation.yml:23`). **Praxis-only** (hard-coded names); not applied to Echelon apps. |
| Praxis "Compiler-derived F# tier analysis" | n/a | **Proposed / remaining slice** of GH-234 (`praxis/docs/worker-checklists.md:121-122`) |
| Ordo Construction (`src/Ordo.Construction`, DF-SDE-2026-0019 draft) | Generated `*.Model.g.fs` (Tier 1), `*.Transition.g.fs` (Tier 2), `*.Orchestration.g.fs` (Tier 3, only with ports) (`ConstructionLayout.fs:18-44`); compile-negative probe FS0039 "tiers are compiled in upward order" | **Implemented and tested inside Ordo** (34 tests, per DF-0019:88-101). Applies only to code Ordo generates. Not used by summa/signal. |
| Dokimos `ConstructionVerification.fs` | Verifies construction manifests/artifacts by tier tag and oracle behavior (`:117-118, 287`) | Implemented for construction fixtures. **No generic tier-dependency check.** |
| HelixNote `scripts/check-semantic-architecture.sh` | Semantic project isolation | Cited as evidence (FT:48-52; VM:45-47). **Not present** in any pinned repo. |
| Aegis | Operational-failure boundary classification/redaction | Implemented and tested (`AegisBoundaryTests`, `FoundationsConformanceTests`). **Not a layering enforcer.** |
| Compiler | Project-reference cycles are impossible in MSBuild/F#. File order inside a project forbids forward references. | Implicit, always on. Gives acyclicity only, not tier direction. |

Bottom line: for Summa and Signal, FT dependency direction is **formally specified but not mechanically
enforced**. The apps' graphs comply only by construction and convention. The only working tier-graph
test pattern in the ecosystem is Praxis's own `ArchitectureTests.fs`.

---

## 7. Ambiguities and inconsistencies (each resolution is a PROPOSAL)

**A1. No project→tier mapping exists.**
FT names responsibilities, not projects, and neither app declares tiers for its projects. Summa uses
Domain/Engine/Application/Host/Pages; Signal uses Limen engine/kernel labels.
*Proposed resolution:* the verifier takes an explicit per-app mapping file as preregistered input, seeded
from the tables in §5 (`Contracts/Access/Ledger`, `Engine` = 1/2; `Storage`, `Admin` = 2; `*.Application` =
3; WASM shim + `web*` + `Operations` = 4). Unmapped projects are a finding, not a guess.
*Reasoning:* FT never prescribes physical layout (FT:132-137), so only a declared mapping makes D2
deterministically checkable.

**A2. Adjacent-only or any-lower dependencies.**
The diagram is a chain (FT:88-101); the text says only "downward only".
*Proposed:* any downward edge (skipping tiers) is legal and only upward edges are violations.
*Reasoning:* that is the literal text. Praxis's enforced graph allows Cli→Domain. The Summa edge
Web.Engine→Ledger would otherwise be a violation, which no document claims it is.

**A3. Tier 1 and Tier 2 share projects.**
Ledger, Access and Signal.Engine each hold both semantic values and transitions. FT gives no rule for
separating 1 from 2 physically.
*Proposed:* treat "Tier 1/2" as one compile-time unit for reference rules. Check 1-vs-2 only where
separate projects or Ordo-generated files exist.
*Reasoning:* DES and CC speak of "Tier 1/2" jointly (CC:23; DES:22, 105), and DF-0019 separates them
only for generated files.

**A4. JSON and serialization in pure projects.**
FT:45-46 bars JSON and serialization from Tier 1 only. BP:90-92 *requires* hand-written tagged-JSON
rendering at the Host Contract. Summa.Contracts' purpose is "a canonical JSON codec".
*Proposed:* classify `System.Text.Json` use in a Tier 1/2 project as **heuristic, requires review**.
It is not a deterministic violation. A violation is a reference to a serialization *framework
package* or the default reflective serializer applied to domain types. Hand-written canonical codecs
in a contract or Tier 2 module are allowed.
*Reasoning:* the BCL namespace cannot be excluded by project references, and BP explicitly mandates
explicit encoders.

**A5. Where is the clock read, and is the composition root Tier 3 or Tier 4?**
FT:78 puts the clock in Tier 4. Both apps read it in `*.Application/Runtime.fs`, which self-describes
as the composition root. The C# shim is a pass-through.
*Proposed:* treat the composition-root module inside the Tier 3 project as Tier 4 code co-located for
WASM packaging reasons. Make this an explicit allow-listed exception per app, not a silent pass.
*Reasoning:* the shim "cannot thread state between calls" (`summa/src/Summa.Web.Application/Runtime.fs:3-6`).
DF-SUMMA-FND-2026-0002 deliberately makes the shim two methods.

**A6. Summa.Storage tier.**
It is "pure", but it owns persistence format and command-to-commit rules over Arca.Core. FT:109 forbids
Tier 1/2 from importing "persistence-adapter" dependencies.
*Proposed:* classify Storage as Tier 2 (persistence *decisions as data*). Arca.Core counts as a pure
library, not a persistence adapter. Arca.GitHub, which performs I/O, is Tier 4 and must not be
referenced by Tier 1/2.
*Reasoning:* the fsproj states that "an Arca provider … performs every read and commit"
(`Summa.Storage.fsproj:7-8`).

**A7. Several "four-tier" names collide.**
SDE (Semantic/Transition/Orchestration/Host), Praxis (Domain/Application/Infrastructure/CLI),
HelixNote state-kinds, and DF-SUMMA-FND-2026-0002:61's Limen layout.
*Proposed:* SDE-DOCTRINE-003 is the authority for Echelon applications. Praxis's version is a
codebase-specific instance for Praxis. HelixNote's is excluded, per FT:31-34 and
`ordo/doctrine/CONTRADICTIONS-AND-DEPRECATED.md:98-107`.
*Reasoning:* FT is the only one marked REQUIRED and installed into every app's `.sde/`.

**A8. Normative strength.**
FT is "REQUIRED" doctrine, but its theory is only `supported` (confidence 0.75, single-app validation;
TH-SDE-2026-0001:46-61). FT:162-166 (source) says it "does not claim … that it has been validated
outside HelixNote/F#".
*Proposed:* treat FT rules as normative for this experiment and record the limited empirical basis
as a threat to validity.

**A9. Stale cross-references in installed copies.**
- Installed FT:19-20 cites `TH-SDE-2026-0001`, which is not installed.
- The installed `reference/GLOSSARY.md:36` points to `doctrine/FOUR-TIER-ARCHITECTURE.md`, a path absent from `.sde/`.
- Signal pins SDE 1.7.0 and Summa pins 1.8.2, while Ordo ships 1.17.0.

*Proposed:* cite by document ID and version (`SDE-DOCTRINE-003 v0.2.1`, which is identical across all
copies by hash) rather than by path.

**A10. "Architecture checks" are required by method but none exist in the apps.**
CM:50, 96 and 166 and VM:33 require that architecture checks run and pass. The check they cite is
HelixNote's script.
*Proposed:* record this as a gap ("missing"). The experiment's verifier (Workstream C) would be the
first such check for summa and signal, and must not be described as a pre-existing gate.

**A11. ROS/Praxis dependence.**
FT:128 says correctness must not depend on ROS. Praxis is the renamed ROS (`.ros/` paths remain; see
`summa/tests/Summa.Web.Tests/ArchitectureTests.fs:20`).
*Proposed:* the check "no production project references a Praxis/ROS package" is deterministic. It
currently holds for both apps (no such PackageReference observed).

---

## 8. Candidate rule catalog

Classes:

- **DET**: deterministically enforceable from the compiler or project structure (fsproj graph, package refs, file order).
- **HEU**: heuristically detectable (source tokens, namespaces, sizes; false positives possible).
- **REV**: requires independent review (semantic judgement).

Status values:

- **FS**: formally specified, no enforcement for summa/signal.
- **ME**: mechanically enforced (a CI-run check fails on violation).
- **TNE**: a test or check exists but does not gate this rule generally.
- **GO**: guidance-only (RECOMMENDED or "should").
- **MA**: missing or ambiguous.

| ID | Statement | Source | Class | Status (summa/signal) |
|---|---|---|---|---|
| AR-01 | A Tier 1 (Semantic Model) project/module must not reference any Tier 2, 3 or 4 project/module. | FT:103 | DET (given mapping A1) | FS |
| AR-02 | Every project/module dependency points to the same or a lower tier (Host→Application→Transition→Semantic); no upward edge. | FT:88-103; A2 | DET (given mapping) | FS (Praxis-own analog: ME) |
| AR-03 | Tier 1/2 projects reference no browser, network, database, filesystem, provider-SDK, persistence-adapter or ROS implementation package (e.g. Arca.GitHub, Fides.Client, Npgsql, ASP.NET, Giraffe). | FT:109; FT:45-46 | DET (package/assembly refs) | FS |
| AR-04 | Tier 1 code does not use Postgres/HTTP/JSON/framework/browser/serialization/filesystem APIs (including BCL namespaces such as `System.IO`, `System.Net`, `System.Text.Json`). | FT:45-46; A4 | HEU | FS (possible deviations §5.1-1, §5.2-1) |
| AR-05 | Tier 2 performs no uncontrolled infrastructure effects; effects are returned as data for Tier 4 to execute. | FT:62-63; DES:25 | HEU (effectful-API tokens) + REV | FS |
| AR-06 | Tier 1/2 does not read the clock, randomness or environment (all are Tier 4). These arrive as arguments. | FT:78; `Summa.Ledger.fsproj:5-6` | HEU | FS (holds in Ledger/Engine by inspection; no test) |
| AR-07 | Tier 3 must not decide which states/transitions are legal; it delegates to Tier 1/2 and does not become "a second semantic authority". | FT:67-70 | REV | FS |
| AR-08 | Database, network, HTTP, browser, filesystem, clock, queue, framework, external-service and WASM/browser interop code lives in Tier 4. | FT:78-79 | HEU | MA (Application-project composition roots read the clock: A5) |
| AR-09 | Effects follow decide (T2) → coordinate (T3) → perform/observe (T4) → interpret Succeeded/Failed/Unknown (T2). | FT:111-124 | REV | FS |
| AR-10 | Unknown external outcomes are explicit, first-class values, never swallowed exceptions or aliased to Failed. | FT:79-81; DES:92-105 | HEU (catch-all handlers) + REV | FS |
| AR-11 | Tier 1/2 may record a reconciliation obligation but never performs the probe (Tier 3/4 does). | FT:126; DES:105 | HEU + REV | FS |
| AR-12 | No production project depends on ROS/Praxis; application correctness must not require ROS. | FT:128; A11 | DET | FS (holds; unchecked) |
| AR-13 | DES/Ordo semantics add no fifth tier and move no I/O downward. | DES:22; FT:107 | DET (subsumed by AR-02/03) | FS |
| AR-14 | Every Host-Contract boundary value has an explicit hand-written tagged-JSON encoder; no default/reflective serializer on domain types. | BP:90-92; BP:115-118 | HEU | FS |
| AR-15 | Host-Contract effects are a closed algebra (one constructor per legal operation), not a flat record of optional fields. | BP:88-89 | HEU + REV | FS |
| AR-16 | Route/operation agreement between engine and kernel/server is asserted by an automated test. | BP:93-94 | HEU (presence of test) | TNE (RoutesTests / RouteSchemaTests run in CI for route tables only) |
| AR-17 | Field/projection mappings match over the closed domain type, exhaustively, never via an open string pair with a wildcard. | BP:95-96 | HEU (wildcard match on strings) + REV | FS |
| AR-18 | External/untyped data is validated before becoming trusted semantic state. | BP:41-42 | REV (HEU for decode-to-Result) | FS |
| AR-19 | A duplicated semantic fact has one authority, a derivation, or a mechanical agreement check. | BP:37-39; SL:57-59 | REV | FS |
| AR-20 | Closed alternatives stay closed across boundaries; weakening to strings/primitives happens as late as possible. | BP:29-50 | REV | GO ("wherever practical") |
| AR-21 | Cross-feature behavior uses explicit contracts; no arbitrary access to another feature's internal state; circular semantic dependencies trigger review. | SL:87-91; FT:149-150 | DET for project cycles (compiler); HEU for module-level | FS (project acyclicity: ME by compiler) |
| AR-22 | Root/top-level components compose features and do not accumulate every feature's state, transitions and rendering. | SL:83-85; FT:149 | HEU (size/union growth, SDE-STRUCT-001 bands) + REV | GO (sde verify size bands exist; not run in app CI) |
| AR-23 | The browser kernel/UI holds no domain rules ("kernel decides nothing"; shim has "no decisions"). | FT:67-70 (derived); `summa/tests/Summa.Web.Tests/ArchitectureTests.fs:26-42`; `signal/context/ARCHITECTURE.md:14` | HEU | Summa: TNE (INV-ARCH-006 token list for money only, run in CI); Signal: FS |
| AR-24 | Unexpected operational failures at declared boundaries go through Aegis (configured once at composition); expected domain outcomes stay typed. | `summa/docs/requirements/ECHELON-SHARED-APPLICATION-FOUNDATIONS.md:56-72` | HEU + REV | TNE (FoundationsConformanceTests check reference/pin/codes, not placement) |
| AR-25 | Architecture checks for illegal dependency direction run and pass before a work item completes. | CM:50, 96, 166; VM:33 | DET (process) | MA (no such check in summa/signal: A10) |
| AR-26 | A shared contract package (e.g. Summa.Contracts) references no project and no package beyond FSharp.Core. | `summa/src/Summa.Contracts/Summa.Contracts.fsproj:3-9`; `PackageTests.fs:12-14` | DET | ME (Summa only) |
| AR-27 | (Ordo-generated code only) Tier 1 has closed unions; Tier 2 has an exhaustive legality table with no catch-all; Tier 3 exists only if ports are declared; Tier 4 is never generated; tiers compile in upward order. | DF-SDE-2026-0019:53-62, 82-84, 101 (draft) | DET | ME inside Ordo tests; not applicable to summa/signal today |
| AR-28 | Each app declares which tier each project/path belongs to. | not stated anywhere; A1 | DET (once declared) | MA |
| AR-29 | Tier 3 depends on typed ports, not concrete providers. | Praxis PRX-QUAL-001:27 (Praxis scope); DF-0019:60-62 (draft) | DET (no Tier 4 provider package in Tier 3) + HEU | MA for Echelon apps (both Application projects reference provider SDKs directly) |

Counts by primary class (mixed entries are counted by their first-listed class; 10 entries carry a secondary REV or HEU component):

- DET = AR-01, 02, 03, 12, 13, 21, 25, 26, 27, 28, 29 → **11**
- HEU = AR-04, 05, 06, 08, 10, 11, 14, 15, 16, 17, 22, 23, 24 → **13**
- REV = AR-07, 09, 18, 19, 20 → **5**
- Total 29.

Counts by status:

- FS 18 (AR-01-07, 09-15, 17-19, 21)
- ME 2 (AR-26; AR-27 inside Ordo only)
- TNE 3 (AR-16, 23, 24)
- GO 2 (AR-20, 22)
- MA 4 (AR-08, 25, 28, 29)
- AR-21 is counted under FS. Its project-cycle part is enforced by the compiler.

---

## Summary of findings

- A formal four-tier specification exists: **SDE-DOCTRINE-003 "Four-Tier Architecture" v0.2.1 (accepted, REQUIRED)**. It is authored in `ordo/doctrine/` and installed byte-identically in both apps at `.sde/architecture/FOUR-TIER-ARCHITECTURE.md`.
- The tiers are Semantic Model, State Transition / Domain Execution, Application / Projection / Orchestration, and Host / External Effects. Dependencies point downward only.
- Summa and Signal are acyclic and appear downward under a proposed mapping. Neither declares tiers, and **neither has a dependency-direction check**. The only enforced tier-graph test in the ecosystem is Praxis's own, hard-coded to Praxis's projects.
