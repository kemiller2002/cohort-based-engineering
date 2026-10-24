/// Heuristic rules (class HEU). Reported as findings; they never affect the exit code.
module Archcheck.Heuristics

open Archcheck.Domain
open Archcheck.Policy
open Archcheck.Rules

let private tierOf (p: Project) = p.Tier |> Option.defaultValue 0

// ---- ARC-HEU-01 -----------------------------------------------------------------------

let swallowedFailures (instance: RuleInstance) (facts: Facts) : Finding list =
    let p = instance.Params

    let handlers =
        [ for project in projectsIn p.Tiers facts do
              for file in project.Files do
                  for h in file.Handlers do
                      if h.CatchAll && not h.Reraises then
                          yield
                              finding
                                  instance
                                  project.Path
                                  file.Path
                                  h.Span.StartLine
                                  (h.Span.StartCol + 1)
                                  "try/with"
                                  $"catch-all exception handler in {h.Scope} does not re-raise"
                              |> at h.Scope ]

    let collapses =
        [ for project in projectsIn p.UnknownTiers facts do
              for file in project.Files do
                  for a in file.Arms do
                      if List.contains a.Case p.UnknownCases && List.contains a.Into p.FailureCases then
                          yield
                              finding
                                  instance
                                  project.Path
                                  file.Path
                                  a.Span.StartLine
                                  (a.Span.StartCol + 1)
                                  a.Case
                                  $"'{a.Case}' outcome collapsed into '{a.Into}' in {a.Scope}"
                              |> at a.Scope ]

    handlers @ collapses

// ---- ARC-HEU-02 -----------------------------------------------------------------------

/// A literal value or a `field op literal` predicate occurring in more than one tier.
/// Each occurrence above the lowest tier that holds it is reported (the lowest tier is
/// taken to be the authority).
let duplicatedFacts (instance: RuleInstance) (facts: Facts) : Finding list =
    let p = instance.Params
    let ignored = p.IgnoredLiterals |> Set.ofList
    let projects = projectsIn p.Tiers facts

    let report (kind: string) (occurrences: (Project * SourceFile * Span * string * string) list) =
        occurrences
        |> List.groupBy (fun (_, _, _, key, _) -> key)
        |> List.collect (fun (key, occ) ->
            let tiers = occ |> List.map (fun (pr, _, _, _, _) -> tierOf pr) |> List.distinct |> List.sort

            match tiers with
            | lowest :: _ :: _ ->
                let where =
                    tiers |> List.map (fun t -> $"Tier {t}") |> String.concat ", "

                occ
                |> List.filter (fun (pr, _, _, _, _) -> tierOf pr <> lowest)
                |> List.map (fun (pr, f, s, _, scope) ->
                    finding instance pr.Path f.Path s.StartLine (s.StartCol + 1) key $"{kind} '{key}' is duplicated across {where}"
                    |> at scope)
            | _ -> [])

    let literals =
        [ for pr in projects do
              for f in pr.Files do
                  for l in f.Literals do
                      if not (ignored.Contains l.Value) then
                          yield pr, f, l.Span, l.Value, l.Scope ]

    let predicates =
        [ for pr in projects do
              for f in pr.Files do
                  for o in f.BinaryOps do
                      match o.Predicate with
                      | Some pred -> yield pr, f, o.Span, pred, o.Scope
                      | None -> () ]

    report "literal" literals @ report "predicate" predicates

// ---- ARC-HEU-03 -----------------------------------------------------------------------

/// Comparison or arithmetic in the host whose operand reads a domain value (a field,
/// property or function of a domain namespace).
let hostDecisions (instance: RuleInstance) (facts: Facts) : Finding list =
    let p = instance.Params

    let isDomain (u: SymbolUse) =
        (u.Kind = Field || u.Kind = Property || u.Kind = Function || u.Kind = Method || u.Kind = ModuleValue)
        && p.DomainNamespaces |> List.exists (fun ns -> Paths.isWithin ns u.Owner)

    [ for project in production facts do
          for file in project.Files do
              for o in file.BinaryOps do
                  if siteInScope p o.Scope then
                      let domainUses =
                          file.Uses
                          |> List.filter (fun u -> isDomain u && o.Operands |> List.exists (fun s -> Span.within s u.Span))

                      match domainUses with
                      | u :: _ ->
                          yield
                              finding
                                  instance
                                  project.Path
                                  file.Path
                                  o.Span.StartLine
                                  (o.Span.StartCol + 1)
                                  u.Name
                                  $"'{o.Op}' on domain value {u.Name} in {o.Scope}"
                              |> at o.Scope
                      | [] -> () ]

// ---- ARC-HEU-04 -----------------------------------------------------------------------

let oversizedFiles (instance: RuleInstance) (facts: Facts) : Finding list =
    let limit = instance.Params.MaxLines |> Option.defaultValue 500

    [ for project in production facts do
          for file in project.Files do
              if file.Lines > limit then
                  yield finding instance project.Path file.Path 1 1 "" $"{file.Lines} lines exceeds the {limit}-line band" ]

let evaluate (facts: Facts) (instance: RuleInstance) : Finding list =
    match instance.Rule.Id with
    | "ARC-HEU-01" -> swallowedFailures instance facts
    | "ARC-HEU-02" -> duplicatedFacts instance facts
    | "ARC-HEU-03" -> hostDecisions instance facts
    | "ARC-HEU-04" -> oversizedFiles instance facts
    | _ -> []
