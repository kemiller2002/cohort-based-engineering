/// Policy (`arch001.policy/1`), probe and contract decoding. Pure: text in, values out.
module Archcheck.Policy

open Archcheck.Domain
open Archcheck.Json

/// Parameters of one rule instance. Each rule reads the fields it needs; a field a rule
/// does not use is rejected at decode time so a typo cannot silently disable a check.
type RuleParams =
    {
        /// Tiers whose projects the rule applies to; empty means every tier.
        Tiers: int list
        /// Namespaces/modules (dotted prefixes) of use sites the rule applies to; empty means all.
        Modules: string list
        /// Use-site namespaces/modules exempt from the rule (e.g. the composition root).
        ExceptModules: string list
        /// Forbidden symbol prefixes. `Namespaces` and `Symbols` match identically (dotted
        /// prefix of the resolved name); they are separate only for readability.
        Namespaces: string list
        Symbols: string list
        /// Symbol kinds the rule applies to; empty means all kinds.
        Kinds: SymbolKind list
        EntityNamespaces: string list
        IdentifierFields: string list
        AllowedPackages: string list
        ForbiddenReferences: (string * string) list
        MaxLines: int option
        IgnoredLiterals: string list
        DomainNamespaces: string list
        UnknownCases: string list
        FailureCases: string list
        UnknownTiers: int list
    }

module RuleParams =
    let empty =
        { Tiers = []
          Modules = []
          ExceptModules = []
          Namespaces = []
          Symbols = []
          Kinds = []
          EntityNamespaces = []
          IdentifierFields = []
          AllowedPackages = []
          ForbiddenReferences = []
          MaxLines = None
          IgnoredLiterals = []
          DomainNamespaces = []
          UnknownCases = []
          FailureCases = []
          UnknownTiers = [] }

type RuleInstance =
    { Rule: RuleInfo
      Params: RuleParams
      /// `policy` or `probe:<index>`.
      Origin: string }

type TierEntry = { Path: string; Tier: int }

type Policy =
    { Id: string
      Projects: TierEntry list
      TestProjects: string list
      Rules: RuleInstance list }

let schema = "arch001.policy/1"

/// The parameter keys each rule accepts.
let private accepted =
    Map.ofList
        [ "ARC-DEP-01", [ "forbiddenReferences" ]
          "ARC-DEP-02", [ "tiers"; "allowedPackages" ]
          "ARC-SYM-01", [ "tiers"; "modules"; "exceptModules"; "namespaces"; "symbols"; "kinds" ]
          "ARC-SYM-02", [ "tiers"; "modules"; "exceptModules"; "namespaces"; "symbols"; "kinds" ]
          "ARC-SYM-03", [ "tiers"; "modules"; "exceptModules"; "namespaces"; "symbols"; "kinds" ]
          "ARC-BND-01", [ "tiers"; "modules"; "exceptModules"; "namespaces"; "symbols"; "kinds" ]
          "ARC-BND-02", [ "tiers"; "modules"; "exceptModules"; "namespaces"; "symbols"; "kinds" ]
          "ARC-BND-03", [ "tiers"; "modules"; "exceptModules"; "entityNamespaces"; "identifierFields"; "symbols" ]
          "ARC-HEU-01", [ "tiers"; "unknownCases"; "failureCases"; "unknownTiers" ]
          "ARC-HEU-02", [ "tiers"; "ignoredLiterals" ]
          "ARC-HEU-03", [ "modules"; "domainNamespaces" ]
          "ARC-HEU-04", [ "maxLines" ]
          "ARC-TRC-01", [] ]

let private (>>=) r f = Result.bind f r

type private ResultBuilder() =
    member _.Bind(r, f) = Result.bind f r
    member _.Return x = Ok x
    member _.ReturnFrom(r: Result<_, _>) = r

let private result = ResultBuilder()

let private traverse (f: 'a -> Result<'b, string>) (xs: 'a list) : Result<'b list, string> =
    List.foldBack
        (fun x acc ->
            match f x, acc with
            | Ok y, Ok ys -> Ok(y :: ys)
            | Error e, _ -> Error e
            | _, Error e -> Error e)
        xs
        (Ok [])

let private kindsOf (rule: RuleInfo) (names: string list) =
    names
    |> traverse (fun k ->
        match SymbolKind.tryParse k with
        | Some kind -> Ok kind
        | None -> Error $"{rule.Id}: unknown kind '{k}'")

let private referencesOf (rule: RuleInfo) (v: JsonValue) =
    match member' "forbiddenReferences" v with
    | None
    | Some JNull -> Ok []
    | Some(JArray xs) ->
        xs
        |> traverse (fun x ->
            match member' "from" x |> Option.bind asString, member' "to" x |> Option.bind asString with
            | Some f, Some t -> Ok(Paths.normalize f, Paths.normalize t)
            | _ -> Error $"{rule.Id}: forbiddenReferences entries need 'from' and 'to'")
    | Some _ -> Error $"{rule.Id}: forbiddenReferences must be an array"

let private maxLinesOf (rule: RuleInfo) (v: JsonValue) =
    match member' "maxLines" v with
    | None
    | Some JNull -> Ok None
    | Some(JInt n) when n > 0L -> Ok(Some(int n))
    | Some _ -> Error $"{rule.Id}: maxLines must be a positive integer"

let private checkKeys (rule: RuleInfo) (extraKeys: string list) (v: JsonValue) =
    match v with
    | JObject ms ->
        let allowed = (accepted |> Map.tryFind rule.Id |> Option.defaultValue []) @ extraKeys

        match ms |> List.map fst |> List.filter (fun k -> not (List.contains k allowed)) with
        | [] -> Ok()
        | bad -> Error $"""{rule.Id}: unknown parameter(s) {String.concat ", " bad}"""
    | _ -> Error $"{rule.Id}: parameters must be an object"

let private checkTiers (rule: RuleInfo) (tiers: int list) =
    match tiers |> List.filter (fun t -> t < 1 || t > 4) with
    | t :: _ -> Error $"{rule.Id}: tier {t} is not 1-4"
    | [] -> Ok()

let private decodeParams (rule: RuleInfo) (extraKeys: string list) (v: JsonValue) : Result<RuleParams, string> =
    result {
        do! checkKeys rule extraKeys v
        let! tiers = intList "tiers" v
        do! checkTiers rule tiers
        let! unknownTiers = intList "unknownTiers" v
        do! checkTiers rule unknownTiers
        let! modules = stringList "modules" v
        // A probe may name a single module with "module".
        let single = member' "module" v |> Option.bind asString |> Option.toList
        let! exceptModules = stringList "exceptModules" v
        let! namespaces = stringList "namespaces" v
        let! symbols = stringList "symbols" v
        let! forbidden = stringList "forbiddenSymbols" v
        let! kindNames = stringList "kinds" v
        let! kinds = kindsOf rule kindNames
        let! entityNamespaces = stringList "entityNamespaces" v
        let! identifierFields = stringList "identifierFields" v
        let! allowedPackages = stringList "allowedPackages" v
        let! ignoredLiterals = stringList "ignoredLiterals" v
        let! domainNamespaces = stringList "domainNamespaces" v
        let! unknownCases = stringList "unknownCases" v
        let! failureCases = stringList "failureCases" v
        let! refs = referencesOf rule v
        let! maxLines = maxLinesOf rule v

        return
            { Tiers = tiers
              Modules = modules @ single
              ExceptModules = exceptModules
              Namespaces = namespaces
              Symbols = symbols @ forbidden
              Kinds = kinds
              EntityNamespaces = entityNamespaces
              IdentifierFields = identifierFields
              AllowedPackages = allowedPackages
              ForbiddenReferences = refs
              MaxLines = maxLines
              IgnoredLiterals = ignoredLiterals
              DomainNamespaces = domainNamespaces
              UnknownCases = unknownCases
              FailureCases = failureCases
              UnknownTiers = unknownTiers }
    }

let decode (text: string) : Result<Policy, string> =
    parse text
    >>= fun root ->
        match member' "schema" root |> Option.bind asString with
        | Some s when s = schema -> Ok root
        | other -> Error $"policy schema must be '{schema}', got %A{other}"
    >>= fun root ->
        let id = member' "id" root |> Option.bind asString

        match id with
        | None
        | Some "" -> Error "policy needs a non-empty 'id'"
        | Some id ->
            let projects =
                match member' "projects" root with
                | Some(JArray xs) ->
                    xs
                    |> traverse (fun x ->
                        match member' "path" x |> Option.bind asString, member' "tier" x |> Option.bind asInt with
                        | Some p, Some t when t >= 1 && t <= 4 -> Ok { Path = Paths.normalize p; Tier = t }
                        | _ -> Error "each policy project needs 'path' and 'tier' 1-4")
                | _ -> Error "policy needs a 'projects' array"

            projects
            >>= fun projects ->
                let dupes =
                    projects |> List.countBy _.Path |> List.filter (snd >> (<) 1) |> List.map fst

                if not dupes.IsEmpty then
                    Error $"""duplicate project paths: {String.concat ", " dupes}"""
                else
                    stringList "testProjects" root
                    >>= fun tests ->
                        match member' "rules" root with
                        | Some(JObject rules) ->
                            let unknown =
                                rules |> List.map fst |> List.filter (Catalogue.tryFind >> Option.isNone)

                            let missing =
                                Catalogue.required |> List.filter (fun r -> not (rules |> List.exists (fst >> (=) r)))

                            if not unknown.IsEmpty then
                                Error $"""unknown rule id(s): {String.concat ", " unknown}"""
                            elif not missing.IsEmpty then
                                Error $"""policy must configure every rule; missing {String.concat ", " missing}"""
                            else
                                rules
                                |> traverse (fun (rid, v) ->
                                    let info = (Catalogue.tryFind rid).Value

                                    decodeParams info [] v
                                    |> Result.map (fun p -> { Rule = info; Params = p; Origin = "policy" }))
                                |> Result.map (fun instances ->
                                    { Id = id
                                      Projects = projects
                                      TestProjects = tests |> List.map Paths.normalize
                                      Rules = instances |> List.sortBy _.Rule.Id })
                        | _ -> Error "policy needs a 'rules' object"

/// `--probes`: a JSON array of rule instances, each `{"rule": "ARC-…", …params}`.
/// A probe is a complete instance: fields it omits are empty, not inherited.
let decodeProbes (text: string) : Result<RuleInstance list, string> =
    parse text
    >>= fun root ->
        match root with
        | JArray xs ->
            xs
            |> List.indexed
            |> traverse (fun (i, x) ->
                match member' "rule" x |> Option.bind asString |> Option.bind Catalogue.tryFind with
                | None -> Error $"probe {i}: 'rule' must name a rule in the catalogue"
                | Some info when info.Id = "ARC-TRC-01" -> Error $"probe {i}: ARC-TRC-01 takes its input from --contract"
                | Some info ->
                    let body =
                        match x with
                        | JObject ms -> JObject(ms |> List.filter (fun (k, _) -> k <> "rule" && k <> "id" && k <> "note"))
                        | other -> other

                    decodeParams info [ "module"; "forbiddenSymbols" ] body
                    |> Result.map (fun p -> { Rule = info; Params = p; Origin = $"probe:{i}" })
                    |> Result.mapError (fun e -> $"probe {i}: {e}"))
        | _ -> Error "probes file must be a JSON array"

/// `--contract`: ids of `decision` nodes in an ecir/1 contract, sorted.
let decodeContract (text: string) : Result<string list, string> =
    parse text
    >>= fun root ->
        match member' "schemaVersion" root |> Option.bind asString with
        | Some "ecir/1" ->
            match member' "nodes" root with
            | Some(JArray nodes) ->
                nodes
                |> List.filter (fun n -> member' "kind" n |> Option.bind asString = Some "decision")
                |> List.choose (member' "id" >> Option.bind asString)
                |> List.distinct
                |> List.sort
                |> Ok
            | _ -> Error "contract has no 'nodes' array"
        | other -> Error $"contract schemaVersion must be 'ecir/1', got %A{other}"
