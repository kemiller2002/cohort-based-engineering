// REL-001 run-01: deterministic summary of one deterministic experiment (A, B or C).
// Usage: dotnet fsi harness/summarize.fsx a|b|c [TAG]
// TAG (amendment A5): summarize results/<exp>/treatment-TAG.jsonl into summary-TAG.json instead.
// Reads results/<exp>/{baseline,treatment}.jsonl (cbe.rel-001.case-result/1) and writes
// results/<exp>/summary.json. Counts only; no inference. Blocked and not-applicable cases
// are listed, never counted as passing.
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes

let exp = (fsi.CommandLineArgs |> Array.tryItem 1 |> Option.defaultValue "a").ToLowerInvariant()
let dir = Path.Combine(__SOURCE_DIRECTORY__, "..", "results", exp)
let tag = fsi.CommandLineArgs |> Array.tryItem 2
let treatmentFile = match tag with Some t -> $"treatment-{t}" | None -> "treatment"
let gateMetrics =
    match exp with
    | "a" -> [ "duplicateActiveOwners"; "staleCompletionsAccepted"; "lostWork" ]
    | "b" -> [ "invalidAccepted"; "completionAccepted"; "ordoAdmittedDeemedInvalid" ]
    | _ -> [ "unverifiedCompletion"; "completionAccepted" ]

let lines arm =
    let f = Path.Combine(dir, arm + ".jsonl")
    if File.Exists f then File.ReadAllLines f |> Array.filter (String.IsNullOrWhiteSpace >> not) |> Array.map (fun l -> JsonNode.Parse l :?> JsonObject) |> Array.toList
    else []

let str (n: JsonNode) = match n with null -> "" | v -> v.ToJsonString().Trim('"')
let metricValue (r: JsonObject) (name: string) =
    match r["metrics"] with
    | :? JsonObject as m ->
        match m[name] with
        | null -> None
        | v when v.GetValueKind() = JsonValueKind.True -> Some 1m
        | v when v.GetValueKind() = JsonValueKind.False -> Some 0m
        | v when v.GetValueKind() = JsonValueKind.Number -> Some(v.GetValue<decimal>())
        | _ -> None
    | _ -> None

let o (fields: (string * JsonNode) list) =
    let x = JsonObject()
    for k, v in fields do x[k] <- v
    x :> JsonNode
let n (d: decimal) = JsonValue.Create d :> JsonNode
let i (d: int) = JsonValue.Create d :> JsonNode
let s (t: string) = JsonValue.Create t :> JsonNode
let a (xs: JsonNode list) = let r = JsonArray() in xs |> List.iter r.Add; r :> JsonNode

let armSummary arm =
    let rs = lines arm
    let executed = rs |> List.filter (fun r -> str r["status"] = "executed")
    let byStatus = rs |> List.countBy (fun r -> str r["status"]) |> List.sortBy fst
    let sumOf m =
        let vs = executed |> List.choose (fun r -> metricValue r m)
        if vs.IsEmpty then null else n (List.sum vs)
    let matches = executed |> List.countBy (fun r -> str r["matchesPrediction"]) |> List.sortBy fst
    let binaries = rs |> List.tryHead |> Option.map (fun r -> r["binaries"].DeepClone()) |> Option.toObj
    o [ "cases", i rs.Length
        "byStatus", o (byStatus |> List.map (fun (k, c) -> k, i c))
        "binaries", binaries
        "totals", o (gateMetrics |> List.map (fun m -> m, sumOf m))
        "matchesPrediction", o (matches |> List.map (fun (k, c) -> (if k = "" then "none" else k), i c))
        "wallMsTotal", n (rs |> List.sumBy (fun r -> match r["wallMs"] with null -> 0m | v -> v.GetValue<decimal>()))
        "caseTable",
        a (rs |> List.map (fun r ->
            o ([ "case", s (str r["case"]); "status", s (str r["status"]); "matchesPrediction", (match r["matchesPrediction"] with null -> null | v -> v.DeepClone())
                 "wallMs", (match r["wallMs"] with null -> null | v -> v.DeepClone()) ]
               @ (gateMetrics |> List.map (fun m -> m, (match metricValue r m with Some v -> n v | None -> null)))
               @ (match r["reason"] with null -> [] | v -> [ "reason", v.DeepClone() ])))) ]

let summary =
    o [ "schema", s "cbe.rel-001.experiment-summary/1"
        "experiment", s (exp.ToUpperInvariant())
        "protocol", s "protocol/run-01.md"
        "sources", a [ s $"results/{exp}/baseline.jsonl"; s $"results/{exp}/{treatmentFile}.jsonl" ]
        "arms", o [ "baseline", armSummary "baseline"; "treatment", armSummary treatmentFile ]
        "note", s "Deterministic conformance cases; counts only, no inference. matchesPrediction compares each case with the preregistered HA/HB/HC prediction for that arm." ]

let out = Path.Combine(dir, (match tag with Some t -> $"summary-{t}.json" | None -> "summary.json"))
File.WriteAllText(out, summary.ToJsonString(JsonSerializerOptions(WriteIndented = true)).Replace("\r\n", "\n") + "\n")
printfn "wrote %s" out
