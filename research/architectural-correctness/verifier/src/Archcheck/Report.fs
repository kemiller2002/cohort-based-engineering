/// The `arch001.verifier-report/1` document and its text rendering. Pure.
module Archcheck.Report

open System
open Archcheck.Domain
open Archcheck.Json

let schema = "arch001.verifier-report/1"

type VerifierInfo =
    { Version: string
      Sha256: string
      Fcs: string
      DotnetSdk: string }

type InputInfo = { Id: string; Sha256: string }

type RepoInfo =
    { GitHead: string option
      TreeClean: bool
      TreeHash: string }

type Report =
    { Verifier: VerifierInfo
      Policy: InputInfo
      Probes: InputInfo option
      Contract: (InputInfo * string list) option
      Repo: RepoInfo
      BuildOk: bool
      Errors: string list
      Projects: Project list
      Findings: Finding list
      EvaluatedAt: DateTimeOffset
      TimingsMs: (string * int64) list }

let private originRank (o: string) = if o = "policy" then "0" else "1" + o

/// Merge findings that report the same thing at the same place (a probe repeating the
/// policy) and sort them by location, then rule.
let consolidate (findings: Finding list) : Finding list =
    findings
    |> List.groupBy (fun f -> f.File, f.Line, f.Column, f.RuleId, f.Symbol, f.Message)
    |> List.map (fun (_, group) ->
        { List.head group with
            Origins = group |> List.collect _.Origins |> List.distinct |> List.sortBy originRank })
    |> List.sortBy (fun f -> f.File, f.Line, f.Column, f.RuleId, f.Symbol, f.Message)

/// Exit criterion: any DET finding of severity ≥ 2.
let gateFailures (findings: Finding list) =
    findings |> List.filter (fun f -> f.Class = Det && f.Severity >= 2)

let pass (findings: Finding list) = (gateFailures findings).IsEmpty

let private findingJson (f: Finding) =
    obj
        [ "ruleId", str f.RuleId
          "class", str (RuleClass.name f.Class)
          "severity", num f.Severity
          "project", str f.Project
          "file", str f.File
          "line", num f.Line
          "column", num f.Column
          "symbol", str f.Symbol
          "message", str f.Message
          "origins", arr (f.Origins |> List.map str) ]

let summaryJson (findings: Finding list) =
    let det = findings |> List.filter (fun f -> f.Class = Det)

    obj
        [ "det",
          obj
              [ "bySeverity", obj [ for s in [ 3; 2; 1 ] -> string s, num (det |> List.filter (fun f -> f.Severity = s) |> List.length) ]
                "total", num det.Length ]
          "heu", num (findings |> List.filter (fun f -> f.Class = Heu) |> List.length)
          "pass", JBool(pass findings) ]

let toJson (r: Report) : JsonValue =
    let input (i: InputInfo) = obj [ "id", str i.Id; "sha256", str i.Sha256 ]

    obj
        [ "schema", str schema
          "verifier",
          obj
              [ "version", str r.Verifier.Version
                "sha256", str r.Verifier.Sha256
                "fcs", str r.Verifier.Fcs
                "dotnetSdk", str r.Verifier.DotnetSdk ]
          "policy", input r.Policy
          "probes", (r.Probes |> Option.map input |> Option.defaultValue JNull)
          "contract",
          (match r.Contract with
           | Some(i, ids) -> obj [ "id", str i.Id; "sha256", str i.Sha256; "decisions", arr (ids |> List.map str) ]
           | None -> JNull)
          "repo",
          obj
              [ "gitHead", strOpt r.Repo.GitHead
                "treeClean", JBool r.Repo.TreeClean
                "treeHash", str r.Repo.TreeHash ]
          "buildOk", JBool r.BuildOk
          "errors", arr (r.Errors |> List.map str)
          "projects",
          arr (
              r.Projects
              |> List.sortBy _.Path
              |> List.map (fun p ->
                  obj
                      [ "path", str p.Path
                        "tier", (p.Tier |> Option.map num |> Option.defaultValue JNull)
                        "role", str (if p.Role = Production then "production" else "test")
                        "files", num p.Files.Length
                        "symbolUses", num (p.Files |> List.sumBy (fun f -> f.Uses.Length)) ])
          )
          "findings", arr (r.Findings |> List.map findingJson)
          "summary", summaryJson r.Findings
          "run",
          obj
              [ "evaluatedAt", str (r.EvaluatedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ"))
                "timingsMs", obj (r.TimingsMs |> List.map (fun (k, v) -> k, JInt v)) ] ]

let render (r: Report) = Json.render (toJson r)

/// Diagnostic dump of every resolved symbol use (`--facts FILE`): the evidence the symbol
/// rules were evaluated over.
let factsJson (projects: Project list) : JsonValue =
    arr
        [ for p in projects |> List.sortBy _.Path do
              for f in p.Files do
                  for u in f.Uses do
                      yield
                          obj
                              [ "file", str f.Path
                                "line", num u.Span.StartLine
                                "column", num (u.Span.StartCol + 1)
                                "scope", str u.Scope
                                "name", str u.Name
                                "owner", str u.Owner
                                "assembly", str u.Assembly
                                "kind", str (SymbolKind.name u.Kind)
                                "pattern", JBool u.IsFromPattern
                                "type", JBool u.IsFromType
                                "recordLabel", JBool u.IsRecordConstructionLabel ] ]

/// One line per finding: `RULE SEV file:line message`, then a summary line.
let text (r: Report) : string =
    let lines =
        [ for e in r.Errors do
              yield $"ERROR {e}"
          for f in r.Findings do
              let at = if f.File = "" then "-" else $"{f.File}:{f.Line}"
              let origin =
                  match f.Origins with
                  | [ "policy" ] -> ""
                  | origins -> " [" + String.concat "," origins + "]"

              yield $"{f.RuleId} {f.Severity} {at} {f.Message}{origin}"
          let det = r.Findings |> List.filter (fun f -> f.Class = Det)
          let count s = det |> List.filter (fun f -> f.Severity = s) |> List.length
          let heu = r.Findings |> List.filter (fun f -> f.Class = Heu) |> List.length

          let verdict =
              if not r.Errors.IsEmpty then "NOT EVALUATED"
              elif pass r.Findings then "PASS"
              else "FAIL"

          yield $"summary: DET sev3={count 3} sev2={count 2} sev1={count 1}; HEU={heu}; {verdict}" ]

    String.concat "\n" lines + "\n"
