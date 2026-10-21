# ARCH-001 architecture rule catalog

This catalog sets out the authoritative rules ARCH-001 uses, where each comes from, and how far each can be decided
mechanically.

| Item | Location |
|---|---|
| Source authority | **SDE-DOCTRINE-003 v0.2.1**, `ordo/doctrine/FOUR-TIER-ARCHITECTURE.md` at ordo `bb43c26` (sha256 `725cb3d9…775b`) |
| Companion doctrine | BOUNDARY-PRESERVATION (004) and STRUCTURAL-LOCALITY (008), from the same SDE distribution |
| Rule derivation, with line citations | [`inventory/architecture-spec-inventory.md`](inventory/architecture-spec-inventory.md) §2–§8 |
| Lending instance given to arms B–D | [`fixtures/pack/LENDING-ARCHITECTURE.md`](fixtures/pack/LENDING-ARCHITECTURE.md) |
| Policy implementing the instance | [`verifier/policy/lending.policy.json`](verifier/policy/lending.policy.json) |

The catalog has two levels:

- **AR-xx**: doctrine rules as they apply to any Echelon application.
- **ARC-xx**: their mechanised instances in `archcheck` for the Lending fixture.

There are no ARC rules without an AR source. Every ARC rule appears in the pack text that arms B–D receive.

## 1. Classification

- **Deterministic**: decided from compiler-resolved facts. These are evaluated MSBuild project and package
  references, and FSharp.Compiler.Service typed symbol uses with their declaring entity and assembly. Comments,
  strings and lookalike names never create findings (verifier samples `neg-regex-trap`, `sym01-alias`,
  `sym01-qualified`). Given a declared tier map, two runs on the same tree give the same verdict.
- **Heuristic**: a syntactic or typed signal that correlates with a violation but can be wrong in both directions. It
  is reported and never gates.
- **Requires independent review**: semantic properties no static analysis decides. A blinded reviewer scores them on
  a rubric.

## 2. Catalog

### Dependency direction and imports

| AR | Doctrine statement (source) | Class | ARC instance | Sev | Mechanically detectable? |
|---|---|---|---|---|---|
| AR-01, AR-02 | Dependencies point downward only; Tier 1 never imports Tiers 2–4 (FT:88-103) | Deterministic, given the tier map (A1) | ARC-DEP-01 | 3 | Yes: evaluated ProjectReference graph. Subsumes Dokimos DOK-R008. |
| AR-03 | Tier 1/2 imports no I/O, provider-SDK, persistence-adapter or ROS package (FT:109) | Deterministic | ARC-DEP-02 | 3 | Yes: PackageReference and the compiler's resolved ReferencePath, transitive included. |
| AR-04, AR-05 | Tier 1 knows no JSON, filesystem, network or serialization; Tier 2 performs no uncontrolled effects (FT:45, FT:62, FT:109) | Deterministic for named APIs; review for "uncontrolled" | ARC-SYM-01 | 3 | Typed uses of listed namespaces and symbols: yes. An effect reached through a function value or port: no (§3). |
| AR-06, AR-08 | Clock, randomness and environment belong to Tier 4 (FT:78) | Deterministic for named APIs | ARC-SYM-02 (outside the composition root) | 2 | Yes, for the listed clock, random, GUID and Stopwatch symbols. |
| AR-08, AR-29 | Tier 3 reaches the outside world through ports; I/O lives in Tier 4 (FT:78) | Deterministic for named APIs | ARC-SYM-03 | 2 | Yes, as for SYM-01. |
| AR-12, AR-13 | No production dependency on ROS/Praxis; no fifth tier (FT:107, FT:128) | Deterministic | Covered by ARC-DEP-02 (no packages in Tier 1/2) | 3 | Yes. |
| AR-21 | No circular dependencies between features or projects | Deterministic at project level | Compiler | — | Yes: MSBuild and F# forbid cycles. Module-level cycles are prevented by F# file order. |

### Responsibility placement and boundaries

| AR | Doctrine statement (source) | Class | ARC instance | Sev | Mechanically detectable? |
|---|---|---|---|---|---|
| AR-07, AR-09 | Tier 3 coordinates use cases and is not a second semantic authority. Effects flow decide (T2) → coordinate (T3) → perform (T4) → interpret (T2) (FT:67-70, FT:111-124) | Review in general. Deterministic *boundary proxies* in the fixture. | ARC-BND-01 (presentation does not touch persistence adapters); ARC-BND-02 (Tier 4 never calls Tier 2 decision functions) | 2 | The proxies: yes (typed uses at sites in Tier 4 presentation, meaning every Host module except Persistence and Composition). Whether Tier 3 re-decides legality: no (ARC-REV-01). |
| AR-23 | The UI holds no domain rules; it renders projections (FT:67-70, derived) | Deterministic proxy plus heuristic | ARC-BND-03 (presentation reads no Tier 1 entity field except identifiers); ARC-HEU-03 (domain comparison or arithmetic in Tier 4) | 2 / 1 | Field reads: yes. "Is this logic a business rule?": no. HEU-03 has false positives, for example formatting. |
| AR-10, AR-11 | Unknown is an explicit outcome, not a swallowed exception. Tier 1/2 records reconciliation obligations but does not probe (FT:79-81, FT:126) | Heuristic plus review | ARC-HEU-01 (catch-alls; Unknown mapped to failure) | 1 | Partial. Functional oracle tests (T4) check the observable behaviour. |
| AR-19 | One authority for each duplicated semantic fact (BP:37-39, SL:57-59) | Review; heuristic signal | ARC-HEU-02 (literal or predicate in two tiers); ARC-REV-03 | 1 | No. A recomputed or rephrased rule is invisible to the heuristic. |
| AR-22 | Root components compose features and do not accumulate them (SL:83-85) | Heuristic | ARC-HEU-04 (SDE-STRUCT-001 500-line band) | 1 | Size only. |
| AR-14, AR-15, AR-17, AR-18, AR-20 | Explicit encoders; closed effect algebra; exhaustive mappings; validate before trust; keep alternatives closed (Boundary Preservation) | Review or heuristic | Not mechanised in ARCH-001; mentioned in the review rubric where relevant | — | Mostly no. |
| AR-16, AR-24 | Route agreement tests; Aegis boundaries | Application-specific | Not applicable to the fixture | — | — |

### Process, traceability and Ordo-generated code

| AR | Doctrine statement (source) | Class | ARC instance | Sev | Mechanically detectable? |
|---|---|---|---|---|---|
| AR-25 | Architecture checks run and pass before completion (CM:50) | Process | Arm D's `submit` gate | — | This is the treatment H3 tests. |
| AR-26 | A shared contract package has no references (Summa-specific) | Deterministic | Not applicable to the fixture | — | — |
| AR-27 | Tier order of Ordo-generated code | Deterministic inside Ordo | Not applicable | — | — |
| AR-28 | Each app declares its tier map | Deterministic once declared | The `tiers` block in the policy; an unmapped project gives exit 2 | — | Yes. |
| (decision traceability) | Decision ids traceable to code and tests (ARCH-001 decision-fidelity criterion; Ordo has no such check) | Deterministic over comments | ARC-TRC-01, arms C and D only | 1 | Presence only, not that the commented code implements the decision. |

Each ARC rule's exact symbol sets are in the policy file. For example, F#'s `printf`, `printfn`, `eprintf`,
`eprintfn`, `stdin`, `stdout` and `stderr` count as `System.Console` use. The pack text states every such set.

## 3. What compiler and AST analysis cannot establish

The full list is in `verifier/README.md`, "Known limits". In summary:

1. **Indirect effects.** An effect reached through a port, function value, interface, reflection or a lower-tier
   helper is attributed to the code that names the symbol. The verifier proves which names are referenced, not which
   effects are performed.
2. **Semantic authority.** Whether Tier 3 makes its own legality decisions (AR-07), whether effect flow is correct
   (AR-09), and whether two pieces of code encode the same fact (AR-19) are judgements. The deterministic BND rules
   are *proxies* that make the most common misplacements decidable in this fixture's layout. They do not decide the
   general property.
3. **Unlisted wrappers.** A third-party wrapper around a forbidden API is invisible unless the policy lists it.
4. **Scopes are declared, not inferred.** The tier map and the presentation scope are policy inputs (A1). A wrong
   map gives wrong verdicts.
5. **Build dependence.** A repository that does not build cannot be evaluated.

## 4. Mandatory and optional controls

Final recommendations depend on the trial results and are in IMPLEMENTATION-RECOMMENDATIONS.md. Independent of
those results, this inventory shows two things:

- AR-01, AR-02, AR-03 and AR-28 are cheap, deterministic and currently **unenforced** in Summa and Signal.
- AR-07, AR-09 and AR-19 cannot be mechanised and need review whatever the outcome.
