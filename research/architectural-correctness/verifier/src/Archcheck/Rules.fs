/// Deterministic rules (class DET). Pure functions from facts and rule instances to findings.
module Archcheck.Rules

open System
open Archcheck.Domain
open Archcheck.Policy

let finding (instance: RuleInstance) (project: string) (file: string) (line: int) (column: int) (symbol: string) (message: string) =
    { RuleId = instance.Rule.Id
      Class = instance.Rule.Class
      Severity = instance.Rule.Severity
      Project = project
      File = file
      Line = line
      Column = column
      Symbol = symbol
      Message = message
      Origins = [ instance.Origin ] }

let production (facts: Facts) =
    facts.Projects |> List.filter (fun p -> p.Role = Production)

/// Production projects whose tier is in `tiers` (every production project if `tiers` is empty).
let projectsIn (tiers: int list) (facts: Facts) =
    production facts
    |> List.filter (fun p ->
        tiers.IsEmpty
        || (match p.Tier with
            | Some t -> List.contains t tiers
            | None -> false))

/// The use site is inside one of `modules` (all sites if empty) and none of `exceptModules`.
let siteInScope (p: RuleParams) (scope: string) =
    (p.Modules.IsEmpty || p.Modules |> List.exists (fun m -> Paths.isWithin m scope))
    && not (p.ExceptModules |> List.exists (fun m -> Paths.isWithin m scope))

let forbidden (p: RuleParams) (u: SymbolUse) =
    (p.Namespaces @ p.Symbols) |> List.exists (fun prefix -> Paths.isWithin prefix u.Name)

let kindAllowed (p: RuleParams) (u: SymbolUse) = p.Kinds.IsEmpty || List.contains u.Kind p.Kinds

let private tierText =
    function
    | Some t -> $"Tier {t}"
    | None -> "unmapped"

// ---- ARC-DEP-01 -----------------------------------------------------------------------

let private nameOf (path: string) =
    IO.Path.GetFileNameWithoutExtension path

let private refMatches (spec: string) (path: string) =
    spec = path || spec = nameOf path || spec = IO.Path.GetFileName path

/// Upward ProjectReference edges, edges into test projects, and (DOK-R008 parity) any
/// explicitly forbidden `from → to` edge. Only references declared by repository files
/// are edges; transitive references are implied by them.
let dependencyDirection (instance: RuleInstance) (facts: Facts) : Finding list =
    let byPath = facts.Projects |> List.map (fun p -> p.Path, p) |> Map.ofList

    [ for p in production facts do
          for r in p.ProjectRefs do
              match byPath |> Map.tryFind r.Target with
              | Some target when target.Role = Test ->
                  yield finding instance p.Path r.DefinedIn r.Line 1 r.Target $"production project {p.Path} references test project {r.Target}"
              | Some target ->
                  match p.Tier, target.Tier with
                  | Some from, Some into when into > from ->
                      yield
                          finding
                              instance
                              p.Path
                              r.DefinedIn
                              r.Line
                              1
                              r.Target
                              $"upward reference: Tier {from} project {p.Path} references Tier {into} project {r.Target}"
                  | _ -> ()
              | None -> ()

              for (from, into) in instance.Params.ForbiddenReferences do
                  if refMatches from p.Path && refMatches into r.Target then
                      yield finding instance p.Path r.DefinedIn r.Line 1 r.Target $"forbidden reference {p.Path} -> {r.Target}" ]

// ---- ARC-DEP-02 -----------------------------------------------------------------------

/// Package and assembly references of pure-tier projects beyond the allowed packages
/// (FSharp.Core) and the framework (BCL). Uses the compiler-resolved `ReferencePath`, so
/// a package that arrives transitively or from an import is seen too.
let pureReferences (instance: RuleInstance) (facts: Facts) : Finding list =
    let allowed = instance.Params.AllowedPackages |> Set.ofList

    [ for p in projectsIn instance.Params.Tiers facts do
          let direct =
              p.Packages
              |> List.filter (fun pk -> pk.Direct && not (allowed.Contains pk.Id))

          for pk in direct do
              yield
                  finding instance p.Path pk.DefinedIn pk.Line 1 pk.Id ($"{tierText p.Tier} project references package {pk.Id} {pk.Version}".TrimEnd())

          let reported = direct |> List.map _.Id |> Set.ofList

          let resolved =
              p.AssemblyRefs
              |> List.choose (fun a ->
                  match a.Kind with
                  | Package id when not (allowed.Contains id) && not (reported.Contains id) -> Some(id, "package")
                  | Raw -> Some(IO.Path.GetFileName a.Path, "assembly")
                  | _ -> None)
              |> List.distinct

          for (name, what) in resolved do
              yield finding instance p.Path p.Path 1 1 name $"{tierText p.Tier} project compiles against {what} {name} (resolved reference)" ]

// ---- symbol rules (ARC-SYM-01/02/03, ARC-BND-01/02) ------------------------------------

let private describeUse (u: SymbolUse) =
    $"{SymbolKind.name u.Kind} {u.Name}"

/// Every use, in a project of the rule's tiers and a site in the rule's modules, of a
/// symbol under one of the forbidden prefixes.
let forbiddenSymbols (instance: RuleInstance) (facts: Facts) : Finding list =
    let p = instance.Params

    [ for project in projectsIn p.Tiers facts do
          for file in project.Files do
              for u in file.Uses do
                  if siteInScope p u.Scope && kindAllowed p u && forbidden p u then
                      yield
                          finding
                              instance
                              project.Path
                              file.Path
                              u.Span.StartLine
                              (u.Span.StartCol + 1)
                              u.Name
                              $"{u.Scope} uses {describeUse u} ({instance.Rule.Statement})" ]

// ---- ARC-BND-03 -----------------------------------------------------------------------

let private lastSegment (name: string) =
    match name.LastIndexOf '.' with
    | -1 -> name
    | i -> name.Substring(i + 1)

/// Reads (not record-construction labels) of a non-identifier field of a record declared
/// in an entity namespace, plus any use of an explicitly listed symbol.
let entityFieldReads (instance: RuleInstance) (facts: Facts) : Finding list =
    let p = instance.Params

    let isIdentifier (u: SymbolUse) =
        p.IdentifierFields |> List.exists (fun pattern -> Paths.wildcard pattern (lastSegment u.Name))

    [ for project in projectsIn p.Tiers facts do
          for file in project.Files do
              for u in file.Uses do
                  if siteInScope p u.Scope && not u.IsRecordConstructionLabel then
                      let entityField =
                          u.Kind = Field
                          && p.EntityNamespaces |> List.exists (fun ns -> Paths.isWithin ns u.Owner)
                          && not (isIdentifier u)

                      let listed = p.Symbols |> List.exists (fun s -> Paths.isWithin s u.Name)

                      if entityField || listed then
                          yield
                              finding
                                  instance
                                  project.Path
                                  file.Path
                                  u.Span.StartLine
                                  (u.Span.StartCol + 1)
                                  u.Name
                                  $"{u.Scope} reads {describeUse u} of a Tier 1 entity; render a view model instead" ]

// ---- ARC-TRC-01 -----------------------------------------------------------------------

let private mentions (id: string) (text: string) =
    text.Contains(id, StringComparison.Ordinal)

/// Each contract decision id must appear in a production comment and in a test (a test
/// binding name or a comment in a test project), per INTERFACES.md §4.
let decisionTrace (instance: RuleInstance) (decisions: string list) (facts: Facts) : Finding list =
    let prodComments =
        production facts
        |> List.collect (fun p -> p.Files |> List.collect (fun f -> f.Comments |> List.map _.Text))

    let testTexts =
        facts.Projects
        |> List.filter (fun p -> p.Role = Test)
        |> List.collect (fun p ->
            p.Files
            |> List.collect (fun f -> (f.Comments |> List.map _.Text) @ f.BindingNames))

    [ for id in decisions do
          if not (prodComments |> List.exists (mentions id)) then
              yield finding instance "" "" 0 0 id $"decision {id} is not cited in any production source comment"

          if not (testTexts |> List.exists (mentions id)) then
              yield finding instance "" "" 0 0 id $"decision {id} is not cited by any test name or test comment" ]

/// Dispatch a DET rule instance.
let evaluate (decisions: string list option) (facts: Facts) (instance: RuleInstance) : Finding list =
    match instance.Rule.Id with
    | "ARC-DEP-01" -> dependencyDirection instance facts
    | "ARC-DEP-02" -> pureReferences instance facts
    | "ARC-SYM-01"
    | "ARC-SYM-02"
    | "ARC-SYM-03"
    | "ARC-BND-01"
    | "ARC-BND-02" -> forbiddenSymbols instance facts
    | "ARC-BND-03" -> entityFieldReads instance facts
    | "ARC-TRC-01" ->
        match decisions with
        | Some ids -> decisionTrace instance ids facts
        | None -> []
    | _ -> []
