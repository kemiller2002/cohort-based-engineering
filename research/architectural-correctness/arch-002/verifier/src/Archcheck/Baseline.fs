/// ARCH-002 brownfield baseline (`--baseline REPORT.json`). Pure.
///
/// A finding is *pre-existing* when its key (rule id, file, symbol, enclosing namespace or
/// module) matches a finding of the baseline report. Line and column are not part of the
/// key, so a violation that only moved does not count as new. Keys are compared as
/// multisets: if the baseline holds a key twice and the evaluated tree holds it three
/// times, exactly one of the three is new.
///
/// Which of several same-key findings is the new one is decided by the source line text
/// (`context`): a finding whose trimmed line equals a baseline finding's line is matched
/// first, so the new one reported is the line that was added, not the old line that moved.
/// This never changes how many findings are new.
module Archcheck.Baseline

open Archcheck.Domain
open Archcheck.Json

/// A baseline finding's key, plus its line text. `Scope = None` only for a report written
/// before ARCH-002 added `scope`; such a key matches on rule, file and symbol alone.
type Key =
    { RuleId: string
      File: string
      Symbol: string
      Scope: string option
      Context: string option }

type Baseline =
    { Id: string
      Sha256: string
      Keys: Key list }

/// What `mark` did, for the report: the baseline keys no current finding consumed are the
/// violations the change *fixed* (or moved to another key).
type Outcome =
    { Findings: Finding list
      Matched: int
      Fixed: Key list }

let keyOf (f: Finding) : Key =
    { RuleId = f.RuleId
      File = f.File
      Symbol = f.Symbol
      Scope = Some f.Scope
      Context = Some f.Context }

/// Attach the trimmed source line to each finding that names a file and line. `lines`
/// holds the evaluated tree's files (repository-relative path -> lines).
let withContext (lines: Map<string, string[]>) (findings: Finding list) : Finding list =
    findings
    |> List.map (fun f ->
        match lines.TryFind f.File with
        | Some ls when f.Line >= 1 && f.Line <= ls.Length -> { f with Context = ls[f.Line - 1].Trim() }
        | _ -> f)

let private reportSchemas = set [ "arch001.verifier-report/1"; "arch002.verifier-report/1" ]

/// Decode a verifier report as a baseline. The report must be one this verifier family
/// wrote and must have evaluated its tree (no `errors`), or the baseline is meaningless.
let decode (text: string) : Result<Key list, string> =
    match parse text with
    | Error e -> Error $"not JSON: {e}"
    | Ok root ->
        match member' "schema" root |> Option.bind asString with
        | Some s when reportSchemas.Contains s ->
            let errors =
                member' "errors" root |> Option.bind asList |> Option.defaultValue []

            if not errors.IsEmpty then
                Error "the baseline report has errors (its tree was not evaluated)"
            else
                match member' "findings" root |> Option.bind asList with
                | None -> Error "the baseline report has no 'findings' array"
                | Some items ->
                    let key (v: JsonValue) =
                        let text name = member' name v |> Option.bind asString

                        match text "ruleId" with
                        | None -> Error "a baseline finding has no 'ruleId'"
                        | Some rule ->
                            Ok
                                { RuleId = rule
                                  File = text "file" |> Option.defaultValue ""
                                  Symbol = text "symbol" |> Option.defaultValue ""
                                  Scope = text "scope"
                                  Context = text "context" }

                    items
                    |> List.map key
                    |> List.fold
                        (fun acc r ->
                            match acc, r with
                            | Ok ks, Ok k -> Ok(k :: ks)
                            | Error e, _
                            | _, Error e -> Error e)
                        (Ok [])
                    |> Result.map List.rev
        | Some s -> Error $"unsupported baseline schema '{s}'"
        | None -> Error "the baseline file is not a verifier report (no 'schema')"

let private sameKey (k: Key) (f: Finding) =
    k.RuleId = f.RuleId && k.File = f.File && k.Symbol = f.Symbol && k.Scope = Some f.Scope

let private sameKeyAndLine (k: Key) (f: Finding) =
    sameKey k f && f.Context <> "" && k.Context = Some f.Context

let private legacy (k: Key) (f: Finding) =
    k.Scope.IsNone && k.RuleId = f.RuleId && k.File = f.File && k.Symbol = f.Symbol

/// One matching pass: each not-yet-matched finding (in report order) consumes the first
/// unconsumed baseline entry the predicate accepts.
let private pass (accepts: Key -> Finding -> bool) (baseline: (int * Key) list) (consumed: Set<int>, findings: Finding list) =
    let step (consumed: Set<int>, acc) (f: Finding) =
        if f.Preexisting then
            consumed, f :: acc
        else
            match baseline |> List.tryFind (fun (i, k) -> not (consumed.Contains i) && accepts k f) with
            | Some(i, _) -> consumed.Add i, { f with Preexisting = true } :: acc
            | None -> consumed, f :: acc

    let consumed', reversed = findings |> List.fold step (consumed, [])
    consumed', List.rev reversed

/// Mark the findings whose key the baseline holds. Passes, in order: same key and same
/// line text; same key; then scope-less legacy keys on rule, file and symbol. Every pass
/// stays within one key, so the number of new findings per key is max(0, current - baseline).
let mark (baseline: Key list) (findings: Finding list) : Outcome =
    let indexed = baseline |> List.indexed

    let consumed, marked =
        (Set.empty, findings)
        |> pass sameKeyAndLine indexed
        |> pass sameKey indexed
        |> pass legacy indexed

    { Findings = marked
      Matched = marked |> List.filter _.Preexisting |> List.length
      Fixed = indexed |> List.filter (fun (i, _) -> not (consumed.Contains i)) |> List.map snd }
