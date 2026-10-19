// REL-001 deterministic summary (RES-REL-006).
// Usage: dotnet fsi analysis/analyze.fsx [OBSERVATIONS-DIR] [OUT.json]
// Reads every observations/**/*.json (cbe.rel-001.observation/1), reports every
// run, compares only eligible runs (completed, nominal, instrumentation
// complete), never imputes a missing value, and states conclusiveness
// explicitly. Identical observations give byte-identical output.
open System
open System.Globalization
open System.IO
open System.Text.Json.Nodes

let args = fsi.CommandLineArgs |> Array.skip 1
let here = __SOURCE_DIRECTORY__
let observationsDir = args |> Array.tryItem 0 |> Option.defaultValue (Path.Combine(here, "..", "observations"))
let outPath = args |> Array.tryItem 1 |> Option.defaultValue (Path.Combine(here, "results.json"))
let preregistrationPath = Path.Combine(here, "preregistration.json")

let ordinal (xs: string seq) = xs |> Seq.sortWith (fun a b -> String.CompareOrdinal(a, b)) |> Seq.toList

let files =
    if Directory.Exists observationsDir then Directory.EnumerateFiles(observationsDir, "*.json", SearchOption.AllDirectories) |> ordinal else []

let runs = files |> List.map (fun f -> JsonNode.Parse(File.ReadAllText f) :?> JsonObject)
let str (n: JsonNode) (k: string) = match n[k] with null -> "" | v -> v.GetValue<string>()

/// A metric's value only when available; partial/unavailable are not used.
let metric (run: JsonObject) (name: string) : decimal option =
    match run["metrics"] with
    | null -> None
    | m ->
        match m[name] with
        | null -> None
        | x when str x "availability" = "available" && not (isNull x["value"]) -> Some(x["value"].GetValue<decimal>())
        | _ -> None

let eligible (run: JsonObject) =
    str run "status" = "completed" && str run "scenario" = "nominal" && str run["instrumentation"] "status" = "complete"

let num (d: decimal) = JsonValue.Create(Math.Round(d, 6, MidpointRounding.ToEven)) :> JsonNode
let opt (d: decimal option) = d |> Option.map num |> Option.toObj
let obj (fields: (string * JsonNode) list) =
    let o = JsonObject()
    fields |> List.sortWith (fun (a, _) (b, _) -> String.CompareOrdinal(a, b)) |> List.iter (fun (k, v) -> o[k] <- v)
    o :> JsonNode
let arr (xs: JsonNode list) = let a = JsonArray() in xs |> List.iter a.Add; a :> JsonNode
let int (n: int) = JsonValue.Create n :> JsonNode

/// Pooled ratio sum(numerator)/sum(denominator) over runs; null unless every
/// run reports both and the denominator is positive.
let pooled (rs: JsonObject list) (numerator: string) (denominator: string) =
    let pairs = rs |> List.map (fun r -> metric r numerator, metric r denominator)
    if rs.IsEmpty || pairs |> List.exists (fun (n, d) -> n.IsNone || d.IsNone) then None
    else
        let d = pairs |> List.sumBy (snd >> Option.get)
        if d <= 0m then None else Some((pairs |> List.sumBy (fst >> Option.get)) / d)

let median (xs: decimal list) =
    match List.sort xs with
    | [] -> None
    | s when s.Length % 2 = 1 -> Some s[s.Length / 2]
    | s -> Some((s[s.Length / 2 - 1] + s[s.Length / 2]) / 2m)

let armSummary (arm: string) =
    let all = runs |> List.filter (fun r -> str r "arm" = arm)
    let ok = all |> List.filter eligible
    let perRun name = ok |> List.choose (fun r -> metric r name)
    let byCache state = ok |> List.filter (fun r -> str r["cache"] "state" = state)

    let gate (name: string) =
        let values = all |> List.map (fun r -> match r["gates"][name] with null -> None | v -> Some(v.GetValue<int>()))
        if all.IsEmpty || values |> List.exists Option.isNone then null else int (values |> List.sumBy Option.get)

    obj
        [ "runs", int all.Length
          "byStatus", obj (all |> List.countBy (fun r -> str r "status") |> List.map (fun (k, n) -> k, int n))
          "byScenario", obj (all |> List.countBy (fun r -> str r "scenario") |> List.map (fun (k, n) -> k, int n))
          "instrumentationIncomplete", int (all |> List.filter (fun r -> str r["instrumentation"] "status" <> "complete") |> List.length)
          "eligibleRuns", int ok.Length
          "costEstimatedPerVerifiedRequirementPooled", opt (pooled ok "costEstimated" "verifiedRequirements")
          "costBilledPerVerifiedRequirementPooled", opt (pooled ok "costBilled" "verifiedRequirements")
          "tokensPerVerifiedRequirementPooled", opt (pooled ok "tokensTotal" "verifiedRequirements")
          "tokensPerVerifiedRequirementMedian", opt (median (perRun "tokensPerVerifiedRequirement"))
          "tokensPerVerifiedRequirementByRun", arr (perRun "tokensPerVerifiedRequirement" |> List.sort |> List.map num)
          "cacheReadTokensPerVerifiedRequirement",
          obj [ for state in [ "cold"; "warm" ] -> state, opt (pooled (byCache state) "tokensCacheRead" "verifiedRequirements") ]
          "reworkFrequencyMean", opt (perRun "reworkFrequency" |> function [] -> None | xs -> Some(List.average xs))
          "firstPassVerificationRateMean", opt (perRun "firstPassVerificationRate" |> function [] -> None | xs -> Some(List.average xs))
          "escapedDefects", opt (if ok.IsEmpty || perRun "escapedDefects" |> List.length < ok.Length then None else Some(perRun "escapedDefects" |> List.sum))
          "gates", obj [ for g in [ "duplicateActiveClaims"; "invalidAcceptedDecisions"; "unverifiedCompletions" ] -> g, gate g ] ]

let minimum =
    if File.Exists preregistrationPath then
        match (JsonNode.Parse(File.ReadAllText preregistrationPath))["minimumEligibleRunsPerArm"] with
        | null -> None
        | v -> Some(v.GetValue<int>())
    else None

let eligibleIn arm = runs |> List.filter (fun r -> str r "arm" = arm && eligible r) |> List.length

let relative (name: string) (num': string) (den: string) =
    let b = pooled (runs |> List.filter (fun r -> str r "arm" = "baseline" && eligible r)) num' den
    let t = pooled (runs |> List.filter (fun r -> str r "arm" = "treatment" && eligible r)) num' den
    name, opt (match b, t with Some b, Some t when b > 0m -> Some((t - b) / b) | _ -> None)

let conclusive, reason =
    match minimum with
    | None -> false, "no preregistration.json (minimumEligibleRunsPerArm); results are descriptive only"
    | Some m when eligibleIn "baseline" < m || eligibleIn "treatment" < m -> false, $"fewer than {m} eligible runs in an arm"
    | Some _ -> true, "preregistered minimum met; apply the preregistered threshold and uncertainty analysis"

let result =
    obj
        [ "schema", JsonValue.Create "cbe.rel-001.analysis/1" :> JsonNode
          "observationFiles", int files.Length
          "arms", obj [ "baseline", armSummary "baseline"; "treatment", armSummary "treatment" ]
          "relativeChangeTreatmentVsBaseline",
          obj [ relative "tokensPerVerifiedRequirement" "tokensTotal" "verifiedRequirements"
                relative "costEstimatedPerVerifiedRequirement" "costEstimated" "verifiedRequirements" ]
          "hypothesisTargets", obj [ "H1TokensPerVerifiedRequirement", num (-0.20m); "H2ReworkFrequency", num (-0.30m) ]
          "conclusive", JsonValue.Create conclusive :> JsonNode
          "conclusiveReason", JsonValue.Create reason :> JsonNode ]

let json = result.ToJsonString(Text.Json.JsonSerializerOptions(WriteIndented = true)).Replace("\r\n", "\n") + "\n"
Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath outPath)) |> ignore
File.WriteAllText(outPath, json)
printfn "wrote %s (%d observation files; conclusive=%b)" outPath files.Length conclusive
