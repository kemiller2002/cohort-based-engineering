// REL-001 Experiment D: EXPLORATORY analysis, written after the data were seen.
// The preregistered analysis (analyze.fsx) is inconclusive: it admits only runs whose
// instrumentation is complete, and cost is unavailable for every run (no price table
// exists; none is invented). Protocol rule X3 excludes incomplete instrumentation from
// the affected comparison only, and token instrumentation is complete for all runs, so
// this script reports the token, rework, defect and effort comparisons descriptively,
// with a paired percentile bootstrap over (task, replicate) blocks. It never replaces
// analyze.fsx and nothing it prints is a confirmatory result.
// usage: dotnet fsi exploratory.fsx [OBSERVATIONS_DIR] [OUT_FILE]
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes

let here = __SOURCE_DIRECTORY__
let args = fsi.CommandLineArgs |> Array.skip 1
let observationsDir = args |> Array.tryItem 0 |> Option.defaultValue (Path.Combine(here, "..", "observations"))
let outPath = args |> Array.tryItem 1 |> Option.defaultValue (Path.Combine(here, "exploratory-results.json"))
let seed = 20261019
let resamples = 10000

type Run =
    { Id: string; Arm: string; Block: string; Tokens: float; Verified: float
      Escaped: float; Rework: float; ToolCalls: float; TestRuns: float; ElapsedMs: float
      HarnessTokens: float option }

let metric (o: JsonNode) (name: string) = o["metrics"].[name].["value"] |> Option.ofObj |> Option.map (fun v -> v.GetValue<float>())

let harnessTokens (runId: string) =
    let path = Path.Combine("/tmp/claude-0/rel001/runs", runId, "logs", "agent.json")
    if File.Exists path then
        (JsonNode.Parse(File.ReadAllText path))["harness"] |> Option.ofObj
        |> Option.map (fun h -> h["subagentTokens"].GetValue<float>())
    else None

let load (path: string) =
    let o = JsonNode.Parse(File.ReadAllText path)
    let id = Path.GetFileNameWithoutExtension path
    let parts = id.Split('-') // REL-001-D-Tn-rN-arm
    let value name = metric o name |> Option.defaultValue nan
    { Id = id; Arm = parts[5]; Block = $"{parts[3]}-{parts[4]}"
      Tokens = value "tokensTotal"; Verified = value "verifiedRequirements"
      Escaped = value "escapedDefects"; Rework = value "reworkFrequency"
      ToolCalls = value "toolCalls"; TestRuns = value "testRuns"; ElapsedMs = value "elapsedMs"
      HarnessTokens = harnessTokens id }

let runs =
    Directory.EnumerateFiles(observationsDir, "*.json", SearchOption.AllDirectories)
    |> Seq.sortWith (fun a b -> String.CompareOrdinal(a, b))
    |> Seq.map load
    |> List.ofSeq

// Pairs are (task, replicate) blocks holding one run of each arm.
let pairs =
    runs
    |> List.groupBy _.Block
    |> List.choose (fun (block, rs) ->
        match List.tryFind (fun r -> r.Arm = "baseline") rs, List.tryFind (fun r -> r.Arm = "treatment") rs with
        | Some b, Some t -> Some(block, b, t)
        | _ -> None)
    |> List.sortBy (fun (block, _, _) -> block)

let pooledRatio (num: Run -> float) (den: Run -> float) (rs: Run list) =
    let d = rs |> List.sumBy den
    if d = 0.0 then nan else (rs |> List.sumBy num) / d

let relativeChange num den (ps: (string * Run * Run) list) =
    let b = ps |> List.map (fun (_, b, _) -> b) |> pooledRatio num den
    let t = ps |> List.map (fun (_, _, t) -> t) |> pooledRatio num den
    (t - b) / b

let percentile (p: float) (xs: float array) =
    let sorted = Array.sort xs
    sorted[int (Math.Floor(p * float (sorted.Length - 1)))]

let bootstrap num den =
    let rng = Random(seed)
    let arr = Array.ofList pairs
    let stats =
        Array.init resamples (fun _ -> List.init arr.Length (fun _ -> arr[rng.Next arr.Length]) |> relativeChange num den)
    percentile 0.025 stats, percentile 0.975 stats

let summarize name (num: Run -> float) (den: Run -> float) =
    let lo, hi = bootstrap num den
    name,
    JsonObject(
        [ Collections.Generic.KeyValuePair("baselinePooled", JsonValue.Create(pairs |> List.map (fun (_, b, _) -> b) |> pooledRatio num den) :> JsonNode)
          Collections.Generic.KeyValuePair("treatmentPooled", JsonValue.Create(pairs |> List.map (fun (_, _, t) -> t) |> pooledRatio num den))
          Collections.Generic.KeyValuePair("relativeChange", JsonValue.Create(relativeChange num den pairs))
          Collections.Generic.KeyValuePair("bootstrap95", JsonArray(JsonValue.Create lo, JsonValue.Create hi))
          Collections.Generic.KeyValuePair(
              "pairsTreatmentHigher",
              JsonValue.Create(pairs |> List.filter (fun (_, b, t) -> num t / den t > num b / den b) |> List.length)) ])

let one _ = 1.0
let totals (f: Run -> float) arm = runs |> List.filter (fun r -> r.Arm = arm) |> List.sumBy f

let result =
    JsonObject(
        [ Collections.Generic.KeyValuePair("schema", JsonValue.Create "cbe.rel-001.exploratory-analysis/1" :> JsonNode)
          Collections.Generic.KeyValuePair("status", JsonValue.Create "exploratory; written after data were seen; not confirmatory")
          Collections.Generic.KeyValuePair("pairs", JsonValue.Create pairs.Length)
          Collections.Generic.KeyValuePair("bootstrap", JsonValue.Create $"paired percentile, {resamples} resamples over (task, replicate) blocks, seed {seed}")
          Collections.Generic.KeyValuePair(
              "comparisons",
              JsonObject(
                  [ summarize "tokensPerVerifiedRequirement" _.Tokens _.Verified
                    summarize "harnessTokensPerVerifiedRequirement" (fun r -> r.HarnessTokens |> Option.defaultValue nan) _.Verified
                    summarize "toolCallsPerRun" _.ToolCalls one
                    summarize "testRunsPerRun" _.TestRuns one
                    summarize "elapsedMsPerRun" _.ElapsedMs one ]
                  |> List.map (fun (k, v) -> Collections.Generic.KeyValuePair(k, v :> JsonNode))))
          Collections.Generic.KeyValuePair(
              "totals",
              JsonObject(
                  [ for arm in [ "baseline"; "treatment" ] ->
                        Collections.Generic.KeyValuePair(
                            arm,
                            JsonObject(
                                [ "verifiedRequirements", totals _.Verified arm
                                  "escapedDefects", totals _.Escaped arm
                                  "rework", totals _.Rework arm
                                  "tokens", totals _.Tokens arm ]
                                |> List.map (fun (k, v) -> Collections.Generic.KeyValuePair(k, JsonValue.Create v :> JsonNode))) :> JsonNode) ])) ])

let json = result.ToJsonString(JsonSerializerOptions(WriteIndented = true))
File.WriteAllText(outPath, json + "\n")
printfn "%s" json
