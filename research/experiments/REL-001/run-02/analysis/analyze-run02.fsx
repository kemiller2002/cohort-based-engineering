// REL-001 run-02 preregistered analysis (design 02-run02-design.md: primary outcome, H1-H5, exclusions,
// R8, R9 and the replicate decision).
// Usage: dotnet fsi run-02/analysis/analyze-run02.fsx [OBSERVATIONS-DIR] [OUT.json]
//   defaults: run-02/observations and run-02/analysis/results.json
// Reads every OBSERVATIONS-DIR/**/*.json that carries a run02 block. Pilot and smoke observations are
// ignored; X4 runs are excluded; X2 runs leave the paired comparisons; a missing metric excludes a run only
// from the comparisons that need that metric (X3). U6 is reported separately and never enters H1-H5.
// Paired percentile bootstrap over (task, replicate) blocks: 10,000 resamples, seed 20261020, one
// independent splitmix64 stream per comparison. Output keys are sorted and numbers are rounded to 6
// decimals, so identical inputs give byte-identical output. No package beyond the .NET SDK.
open System
open System.IO
open System.Security.Cryptography
open System.Text
open System.Text.Json
open System.Text.Json.Nodes

let args = fsi.CommandLineArgs |> Array.skip 1
let here = __SOURCE_DIRECTORY__
let observationsDir = args |> Array.tryItem 0 |> Option.defaultValue (Path.Combine(here, "..", "observations"))
let outPath = args |> Array.tryItem 1 |> Option.defaultValue (Path.Combine(here, "results.json"))
let seed = 20261020UL
let resamples = 10000
let arms = [ "A"; "B"; "C"; "D" ]
let armNames = Map [ "A", "bare"; "B", "directives"; "C", "echelon-original"; "D", "echelon-optimized" ]
let categories = [ "simple"; "moderate"; "complex"; "adversarial" ]

// ------------------------------------------------------------------------------------------ input
let ordinal (xs: string seq) = xs |> Seq.sortWith (fun a b -> String.CompareOrdinal(a, b)) |> Seq.toList

let files =
    if Directory.Exists observationsDir then
        Directory.EnumerateFiles(observationsDir, "*.json", SearchOption.AllDirectories) |> ordinal
    else []

type Obs =
    { RunId: string; Supersedes: string option; Letter: string; Task: string; Category: string; Block: string
      Label: string; Excluded: bool; Paired: bool; Units: decimal; Correct: decimal
      Cost: decimal option; Tokens: decimal option; TokensExcl: decimal option
      InvalidAccepted: decimal; Escaped: decimal; DuplicateOwners: decimal; LostWork: decimal; Conflicting: decimal
      U6Completions: decimal option; FirstPass: bool option; TestRuns: decimal; TestFull: decimal; TestFocused: decimal
      TestComputeMs: decimal; ToolCalls: decimal option; WallMs: decimal option; Rework: decimal
      OutcomeConsistent: bool option }

let node (n: JsonNode) (path: string list) =
    path |> List.fold (fun (acc: JsonNode) k -> if isNull acc then null else (match acc with :? JsonObject as o -> o[k] | _ -> null)) n
let dec (n: JsonNode) path =
    match node n path with
    | null -> None
    | v -> (match v.GetValueKind() with JsonValueKind.Number -> Some(v.GetValue<decimal>()) | _ -> None)
let boolean (n: JsonNode) path =
    match node n path with
    | null -> None
    | v -> (match v.GetValueKind() with JsonValueKind.True -> Some true | JsonValueKind.False -> Some false | _ -> None)
let text (n: JsonNode) path = match node n path with null -> "" | v -> (try v.GetValue<string>() with _ -> "")
let zero = Option.defaultValue 0m

/// A metric value usable for comparisons: available or partial (transcript output is a lower bound in every
/// arm alike), never unavailable.
let metricValue (n: JsonNode) path =
    match text n (path @ [ "availability" ]) with
    | "available" | "partial" -> dec n (path @ [ "value" ])
    | _ -> None

let parse (n: JsonNode) =
    { RunId = text n [ "runId" ]
      Supersedes = (match text n [ "supersedes" ] with "" -> None | s -> Some s)
      Letter = text n [ "run02"; "armLetter" ]
      Task = text n [ "task"; "taskId" ]
      Category = text n [ "run02"; "category" ]
      Block = text n [ "run02"; "block" ]
      Label = text n [ "run02"; "label" ]
      Excluded = text n [ "status" ] = "excluded" || boolean n [ "run02"; "exclusions"; "x4"; "contaminated" ] = Some true
      Paired = boolean n [ "run02"; "eligibility"; "pairedComparisons" ] |> Option.defaultValue false
      Units = dec n [ "run02"; "units"; "total" ] |> zero
      Correct = dec n [ "run02"; "units"; "correct" ] |> zero
      Cost = metricValue n [ "metrics"; "costEstimated" ]
      Tokens = metricValue n [ "metrics"; "tokensTotal" ]
      TokensExcl = metricValue n [ "run02"; "tokens"; "excludingCacheReads" ]
      InvalidAccepted = dec n [ "run02"; "reliability"; "invalidCompletionsAccepted" ] |> zero
      Escaped = dec n [ "run02"; "reliability"; "escapedDefects" ] |> zero
      DuplicateOwners = dec n [ "run02"; "reliability"; "duplicateOwners" ] |> zero
      LostWork = dec n [ "run02"; "reliability"; "lostWork" ] |> zero
      Conflicting = dec n [ "run02"; "reliability"; "conflictingCompletions" ] |> zero
      U6Completions = dec n [ "run02"; "u6"; "completions" ]
      FirstPass = boolean n [ "run02"; "firstPassCorrect" ]
      TestRuns = dec n [ "run02"; "tests"; "total" ] |> zero
      TestFull = dec n [ "run02"; "tests"; "full" ] |> zero
      TestFocused = dec n [ "run02"; "tests"; "focused" ] |> zero
      TestComputeMs = dec n [ "run02"; "tests"; "computeMs" ] |> zero
      ToolCalls = dec n [ "run02"; "toolCalls" ]
      WallMs = dec n [ "run02"; "wallMs" ]
      Rework = dec n [ "run02"; "rework"; "total" ] |> zero
      OutcomeConsistent = boolean n [ "run02"; "completionEvidence"; "outcomeConsistency"; "consistent" ] }

let documents = files |> List.map (fun f -> f, JsonNode.Parse(File.ReadAllText f))
let parsed = documents |> List.filter (fun (_, n) -> not (isNull (node n [ "run02" ]))) |> List.map (snd >> parse)
let superseded = parsed |> List.choose (fun o -> o.Supersedes) |> Set.ofList
let current = parsed |> List.filter (fun o -> not (superseded.Contains o.RunId))
let ignored = current |> List.filter (fun o -> o.Label <> "trial")
let trials = current |> List.filter (fun o -> o.Label = "trial")
let excluded = trials |> List.filter (fun o -> o.Excluded)
let included = trials |> List.filter (fun o -> not o.Excluded)
let efficiency = included |> List.filter (fun o -> o.Task <> "U6") // U6 never enters the efficiency headline (R8)

// ------------------------------------------------------------------------------------------ output helpers
let round6 (d: decimal) = Math.Round(d, 6, MidpointRounding.ToEven)
let num (d: decimal) = JsonValue.Create(round6 d) :> JsonNode
let optNum (d: decimal option) = d |> Option.map num |> Option.toObj
let flt (f: float) = if Double.IsNaN f || Double.IsInfinity f then null else num (decimal f)
let str (s: string) = JsonValue.Create s :> JsonNode
let bln (b: bool) = JsonValue.Create b :> JsonNode
let jint (n: int) = JsonValue.Create n :> JsonNode
let obj (fields: (string * JsonNode) list) =
    let o = JsonObject()
    fields |> List.sortWith (fun (a, _) (b, _) -> String.CompareOrdinal(a, b)) |> List.iter (fun (k, v) -> o[k] <- v)
    o :> JsonNode
let arr (xs: JsonNode list) = let a = JsonArray() in xs |> List.iter a.Add; a :> JsonNode
let strs xs = xs |> List.map str |> arr

// ------------------------------------------------------------------------------------------ descriptive
let ratio (num: decimal) (den: decimal) = if den > 0m then Some(num / den) else None
let sumOpt (f: Obs -> decimal option) (rs: Obs list) =
    let vs = rs |> List.map f
    if rs.IsEmpty || vs |> List.exists Option.isNone then None else Some(vs |> List.sumBy Option.get)

/// Pooled per-correct-requirement value over the runs that report the metric (X3); runs with 0 correct
/// still add their cost.
let pooledPerCorrect (f: Obs -> decimal option) (rs: Obs list) =
    let usable = rs |> List.filter (f >> Option.isSome)
    let total = usable |> List.sumBy (f >> Option.get)
    let correct = usable |> List.sumBy (fun o -> o.Correct)
    obj [ "runs", jint usable.Length; "runsMissingMetric", jint (rs.Length - usable.Length)
          "numerator", num total; "correctRequirements", num correct; "value", optNum (ratio total correct) ]

let totals (rs: Obs list) =
    let units = rs |> List.sumBy (fun o -> o.Units)
    let correct = rs |> List.sumBy (fun o -> o.Correct)
    let fp = rs |> List.choose (fun o -> o.FirstPass)
    obj [ "runs", jint rs.Length
          "requirementUnits", num units
          "correctRequirements", num correct
          "correctRate", optNum (ratio correct units)
          "costEstimatedUSD", optNum (sumOpt (fun o -> o.Cost) rs)
          "tokensTotal", optNum (sumOpt (fun o -> o.Tokens) rs)
          "tokensExcludingCacheReads", optNum (sumOpt (fun o -> o.TokensExcl) rs)
          "costPerCorrectRequirement", pooledPerCorrect (fun o -> o.Cost) rs
          "tokensPerCorrectRequirement", pooledPerCorrect (fun o -> o.Tokens) rs
          "invalidCompletionsAccepted", num (rs |> List.sumBy (fun o -> o.InvalidAccepted))
          "escapedDefects", num (rs |> List.sumBy (fun o -> o.Escaped))
          "duplicateOwners", num (rs |> List.sumBy (fun o -> o.DuplicateOwners))
          "lostWork", num (rs |> List.sumBy (fun o -> o.LostWork))
          "conflictingCompletions", num (rs |> List.sumBy (fun o -> o.Conflicting))
          "firstPassCorrectRate", optNum (ratio (fp |> List.filter id |> List.length |> decimal) (decimal fp.Length))
          "outcomeLineInconsistencies", jint (rs |> List.filter (fun o -> o.OutcomeConsistent = Some false) |> List.length)
          "testRuns", obj [ "total", num (rs |> List.sumBy (fun o -> o.TestRuns)); "full", num (rs |> List.sumBy (fun o -> o.TestFull))
                            "focused", num (rs |> List.sumBy (fun o -> o.TestFocused)); "computeMs", num (rs |> List.sumBy (fun o -> o.TestComputeMs)) ]
          "toolCalls", optNum (sumOpt (fun o -> o.ToolCalls) rs)
          "wallMs", optNum (sumOpt (fun o -> o.WallMs) rs)
          "rework", num (rs |> List.sumBy (fun o -> o.Rework)) ]

let groupedBy (key: Obs -> string) (keys: string list) (rs: Obs list) =
    keys |> List.map (fun k -> k, totals (rs |> List.filter (fun o -> key o = k))) |> obj

let byArm (f: Obs list -> JsonNode) (rs: Obs list) =
    arms |> List.map (fun a -> a, f (rs |> List.filter (fun o -> o.Letter = a))) |> obj

let tasksOf (rs: Obs list) = rs |> List.map (fun o -> o.Task) |> List.distinct |> ordinal

// ------------------------------------------------------------------------------------------ bootstrap
/// splitmix64: the next value and state.
let splitmix (state: uint64) =
    let s = state + 0x9E3779B97F4A7C15UL
    let z1 = (s ^^^ (s >>> 30)) * 0xBF58476D1CE4E5B9UL
    let z2 = (z1 ^^^ (z1 >>> 27)) * 0x94D049BB133111EBUL
    z2 ^^^ (z2 >>> 31), s

/// Uniform index in [0, n) from 53 random bits.
let index (n: int) (v: uint64) = min (n - 1) (int (float (v >>> 11) * (1.0 / 9007199254740992.0) * float n))

/// One resample: n block indices drawn with replacement, and the next state.
let draw (n: int) (state: uint64) =
    (state, [ 1..n ]) ||> List.mapFold (fun s _ -> let v, s' = splitmix s in index n v, s') |> fun (idx, s) -> List.toArray idx, s

/// Percentile (type 7, linear interpolation) of sorted values.
let percentile (sorted: float[]) (p: float) =
    let h = float (sorted.Length - 1) * p
    let lo = int (floor h)
    let hi = min (sorted.Length - 1) (lo + 1)
    sorted[lo] + (h - float lo) * (sorted[hi] - sorted[lo])

/// Paired percentile bootstrap of a statistic over block rows (each row: the per-block sums the statistic needs).
let bootstrap (rows: float[][]) (stat: float[] -> float option) =
    let width = if rows.Length = 0 then 0 else rows[0].Length
    let sumOf (idx: int[]) = Array.init width (fun j -> idx |> Array.sumBy (fun i -> rows[i][j]))
    let point = if rows.Length = 0 then None else stat (sumOf (Array.init rows.Length id))
    let stats =
        if rows.Length = 0 then [||]
        else
            (seed, [ 1..resamples ]) ||> List.mapFold (fun s _ -> let idx, s' = draw rows.Length s in stat (sumOf idx), s')
            |> fst |> List.toArray
    let defined = stats |> Array.choose id |> Array.sort
    let ci = if defined.Length = 0 then None else Some(percentile defined 0.025, percentile defined 0.975)
    point, ci, stats.Length - defined.Length

let decision (ci: (float * float) option) lowerMeans higherMeans =
    match ci with
    | Some(lo, hi) when hi < 0.0 -> lowerMeans
    | Some(lo, hi) when lo > 0.0 -> higherMeans
    | Some _ -> "not distinguishable"
    | None -> "not estimable"

type Measure =
    { Name: string; Value: Obs -> decimal option; Unit: string }
let costMeasure = { Name = "costPerCorrectRequirement"; Value = (fun o -> o.Cost); Unit = "USD (F5 price table, estimated)" }
let tokenMeasure = { Name = "tokensPerCorrectRequirement"; Value = (fun o -> o.Tokens); Unit = "tokens (output is a lower bound)" }
let tokenExclMeasure = { Name = "tokensExcludingCacheReadsPerCorrectRequirement"; Value = (fun o -> o.TokensExcl); Unit = "tokens" }

let cell (rs: Obs list) (block: string) (letter: string) = rs |> List.tryFind (fun o -> o.Block = block && o.Letter = letter)

/// Blocks of the subset where both arms have a run, both runs are paired-eligible (X2, X4) and both report
/// the measure (X3); and the reasons the other blocks were left out.
let pairedBlocks (rs: Obs list) (x: string) (y: string) (value: Obs -> decimal option) =
    let blocks = rs |> List.map (fun o -> o.Block) |> List.distinct |> ordinal
    let classify b =
        match cell rs b x, cell rs b y with
        | Some ox, Some oy when not (ox.Paired && oy.Paired) -> Error "x2"
        | Some ox, Some oy when (value ox).IsNone || (value oy).IsNone -> Error "metricMissing"
        | Some ox, Some oy -> Ok(b, ox, oy)
        | _ -> Error "runMissing"
    let results = blocks |> List.map classify
    let ok = results |> List.choose (function Ok v -> Some v | _ -> None)
    let reasons = results |> List.choose (function Error e -> Some e | _ -> None) |> List.countBy id |> List.sortBy fst
    ok, reasons

let interval (point, ci, undefinedResamples) =
    [ "pointEstimate", (point |> Option.map flt |> Option.toObj)
      "ci95", (match ci with Some(lo, hi) -> arr [ flt lo; flt hi ] | None -> null)
      "undefinedResamples", jint undefinedResamples ]

/// Relative difference in pooled per-correct-requirement value, X vs Y: (sum vX / sum cX) / (sum vY / sum cY) - 1.
let relativeComparison (rs: Obs list) (x: string) (y: string) (m: Measure) =
    let ok, reasons = pairedBlocks rs x y m.Value
    let rows =
        ok |> List.map (fun (_, ox, oy) -> [| float (m.Value ox).Value; float ox.Correct; float (m.Value oy).Value; float oy.Correct |]) |> List.toArray
    let stat (s: float[]) = if s[1] > 0.0 && s[3] > 0.0 && s[2] > 0.0 then Some((s[0] / s[1]) / (s[2] / s[3]) - 1.0) else None
    let result = bootstrap rows stat
    let _, ci, _ = result
    obj ([ "measure", str m.Name; "unit", str m.Unit
           "statistic", str $"relative difference in pooled {m.Name}, {x} vs {y}: ({x}/{y}) - 1"
           "blocks", jint ok.Length; "blockIds", strs (ok |> List.map (fun (b, _, _) -> b))
           "blocksLeftOut", obj (reasons |> List.map (fun (r, n) -> r, jint n))
           "decision", str (decision ci $"{x} lower" $"{x} higher") ]
         @ interval result)

/// Difference in correct-completion rate, X minus Y (H4).
let rateComparison (rs: Obs list) (x: string) (y: string) =
    let ok, reasons = pairedBlocks rs x y (fun _ -> Some 0m)
    let rows = ok |> List.map (fun (_, ox, oy) -> [| float ox.Correct; float ox.Units; float oy.Correct; float oy.Units |]) |> List.toArray
    let stat (s: float[]) = if s[1] > 0.0 && s[3] > 0.0 then Some(s[0] / s[1] - s[2] / s[3]) else None
    let result = bootstrap rows stat
    let _, ci, _ = result
    obj ([ "measure", str "correctCompletionRate"; "unit", str "proportion of requirement units correct"
           "statistic", str $"difference in correct-completion rate, {x} - {y}"
           "blocks", jint ok.Length; "blockIds", strs (ok |> List.map (fun (b, _, _) -> b))
           "blocksLeftOut", obj (reasons |> List.map (fun (r, n) -> r, jint n))
           "decision", str (decision ci $"{x} lower" $"{x} higher") ]
         @ interval result)

let withAndWithoutU2 (f: Obs list -> JsonNode) (rs: Obs list) =
    obj [ "withU2", f rs; "withoutU2", f (rs |> List.filter (fun o -> o.Task <> "U2")) ]

let costAndTokens (x: string) (y: string) (rs: Obs list) =
    obj [ "cost", relativeComparison rs x y costMeasure
          "tokens", relativeComparison rs x y tokenMeasure
          "tokensExcludingCacheReads", relativeComparison rs x y tokenExclMeasure ]

let inCategory c (rs: Obs list) = rs |> List.filter (fun o -> o.Category = c)

let hypothesis id rq (question: string) (comparison: string) (blocks: string) (result: JsonNode) =
    obj [ "id", str id; "researchQuestion", str rq; "label", str "preregistered (confirmatory)"; "question", str question
          "comparison", str comparison; "blocks", str blocks; "result", result ]

/// H5: per category, each arm's pooled cost per correct requirement on the blocks where all four arms are
/// eligible, with a percentile bootstrap interval, and the ordering of the point estimates.
let ordering (rs: Obs list) (m: Measure) =
    let blocks =
        rs |> List.map (fun o -> o.Block) |> List.distinct |> ordinal
        |> List.filter (fun b -> arms |> List.forall (fun a -> match cell rs b a with Some o -> o.Paired && (m.Value o).IsSome | None -> false))
    let perArm a =
        let rows = blocks |> List.map (fun b -> let o = (cell rs b a).Value in [| float (m.Value o).Value; float o.Correct |]) |> List.toArray
        bootstrap rows (fun s -> if s[1] > 0.0 then Some(s[0] / s[1]) else None)
    let results = arms |> List.map (fun a -> a, perArm a)
    let order =
        results |> List.choose (fun (a, (p, _, _)) -> p |> Option.map (fun v -> a, v)) |> List.sortBy (fun (a, v) -> v, a) |> List.map fst
    obj [ "measure", str m.Name; "blocks", jint blocks.Length; "blockIds", strs blocks
          "descriptiveOnly", bln true
          "fewerThan4Blocks", bln (blocks.Length < 4)
          "perArm", obj (results |> List.map (fun (a, r) -> a, obj (interval r)))
          "orderLowestFirst", strs order
          "armsWithoutEstimate", strs (arms |> List.filter (fun a -> not (List.contains a order))) ]

// ------------------------------------------------------------------------------------------ results
let hypotheses =
    [ hypothesis "H1" "RQ4" "Does protocol optimization lower cost per correct requirement?" "D vs C" "all (U6 excluded)"
          (withAndWithoutU2 (costAndTokens "D" "C") efficiency)
      hypothesis "H2" "RQ5" "Is optimized Echelon cheaper per correct requirement than bare Claude?" "D vs A" "all, and per category (U6 excluded)"
          (obj [ "all", withAndWithoutU2 (costAndTokens "D" "A") efficiency
                 "perCategory", obj (categories |> List.map (fun c -> c, withAndWithoutU2 (costAndTokens "D" "A") (inCategory c efficiency))) ])
      hypothesis "H3" "RQ1" "On simple tasks, is bare Claude cheaper per correct requirement than original Echelon?" "A vs C" "simple"
          (withAndWithoutU2 (costAndTokens "A" "C") (inCategory "simple" efficiency))
      hypothesis "H4" "RQ2" "Do the directives alone change correct-completion rate and cost per correct requirement?" "B vs A" "all (U6 excluded)"
          (withAndWithoutU2 (fun rs -> obj [ "correctCompletionRate", rateComparison rs "B" "A"; "costAndTokens", costAndTokens "B" "A" rs ]) efficiency)
      hypothesis "H5" "RQ3" "Per category, how do A, B, C and D order on cost per correct requirement?" "A, B, C, D" "per category (U6 excluded)"
          (obj (categories |> List.map (fun c ->
              c, obj [ "cost", ordering (inCategory c efficiency) costMeasure; "tokens", ordering (inCategory c efficiency) tokenMeasure ]))) ]

let reliability =
    let count f a = included |> List.filter (fun o -> o.Letter = a) |> List.sumBy f
    let kinds =
        [ "invalidCompletionsAccepted", (fun o -> o.InvalidAccepted); "escapedDefects", (fun o -> o.Escaped)
          "duplicateOwners", (fun o -> o.DuplicateOwners); "lostWork", (fun o -> o.LostWork) ]
    obj [ "label", str "preregistered (non-inferiority criterion: D no more than C on each count)"
          "perArm", obj (arms |> List.map (fun a -> a, obj (kinds |> List.map (fun (k, f) -> k, num (count f a)))))
          "dNoMoreThanC", obj (kinds |> List.map (fun (k, f) -> k, bln (count f "D" <= count f "C")))
          "met", bln (kinds |> List.forall (fun (_, f) -> count f "D" <= count f "C")) ]

let pooledPrimary (rs: Obs list) =
    byArm (fun xs -> obj [ "cost", pooledPerCorrect (fun o -> o.Cost) xs
                           "tokens", pooledPerCorrect (fun o -> o.Tokens) xs
                           "tokensExcludingCacheReads", pooledPerCorrect (fun o -> o.TokensExcl) xs ]) rs

let rq6 =
    let contrast (x: string) (y: string) (rs: Obs list) =
        let p (a: string) f = let xs = rs |> List.filter (fun o -> o.Letter = a) in let us = xs |> List.filter (f >> Option.isSome) in ratio (us |> List.sumBy (f >> Option.get)) (us |> List.sumBy (fun o -> o.Correct))
        let rate (a: string) = let xs = rs |> List.filter (fun o -> o.Letter = a) in ratio (xs |> List.sumBy (fun o -> o.Correct)) (xs |> List.sumBy (fun o -> o.Units))
        let diff a b = match a, b with Some u, Some v -> Some(u - v) | _ -> None
        obj [ "costPerCorrectRequirement", optNum (diff (p x (fun o -> o.Cost)) (p y (fun o -> o.Cost)))
              "tokensPerCorrectRequirement", optNum (diff (p x (fun o -> o.Tokens)) (p y (fun o -> o.Tokens)))
              "correctRate", optNum (diff (rate x) (rate y)) ]
    let all rs = obj [ "directives (B - A)", contrast "B" "A" rs
                       "orchestration + constructibility + verification, bundled (C - B)", contrast "C" "B" rs
                       "protocol optimization (D - C)", contrast "D" "C" rs ]
    obj [ "label", str "exploratory (descriptive arm contrasts; individual effects inside the C - B bundle are unresolved by this design)"
          "all", all efficiency
          "perCategory", obj (categories |> List.map (fun c -> c, all (inCategory c efficiency))) ]

let u6Report =
    let u6 = included |> List.filter (fun o -> o.Task = "U6")
    obj [ "label", str "reported separately (R8); never in H1-H5; exploratory"
          "perArm", byArm (fun xs -> obj [ "runs", jint xs.Length
                                           "exactlyOneCompletion", jint (xs |> List.filter (fun o -> o.U6Completions = Some 1m) |> List.length)
                                           "duplicateOwners", num (xs |> List.sumBy (fun o -> o.DuplicateOwners))
                                           "lostWork", num (xs |> List.sumBy (fun o -> o.LostWork))
                                           "conflictingCompletions", num (xs |> List.sumBy (fun o -> o.Conflicting))
                                           "correctRequirements", num (xs |> List.sumBy (fun o -> o.Correct))
                                           "costEstimatedUSD", optNum (sumOpt (fun o -> o.Cost) xs) ]) u6 ]

let difficulty =
    obj [ "label", str "exploratory (observed failure rate per task as a difficulty measure; categories are builder-assigned and unvalidated)"
          "perTask", obj (tasksOf included |> List.map (fun t ->
              let xs = included |> List.filter (fun o -> o.Task = t)
              let units = xs |> List.sumBy (fun o -> o.Units)
              t, obj [ "runs", jint xs.Length; "category", str (xs.Head.Category)
                       "failureRate", optNum (ratio (units - (xs |> List.sumBy (fun o -> o.Correct))) units) ])) ]

let inputDigest =
    use sha = SHA256.Create()
    let lines = files |> List.map (fun f -> $"{Path.GetFileName f} {Convert.ToHexString(SHA256.HashData(File.ReadAllBytes f)).ToLowerInvariant()}\n")
    Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes(String.Concat lines))).ToLowerInvariant()

let result =
    obj [ "schema", str "cbe.rel-001.run-02-analysis/1"
          "design", str "02-run02-design.md (preregistered); paired percentile bootstrap over (task, replicate) blocks"
          "seed", JsonValue.Create seed :> JsonNode
          "resamples", jint resamples
          "arms", obj (armNames |> Map.toList |> List.map (fun (k, v) -> k, str v))
          "inputs", obj [ "files", jint files.Length; "sha256", str inputDigest; "observations", jint parsed.Length
                          "superseded", jint superseded.Count
                          "ignoredNonTrial", obj (ignored |> List.countBy (fun o -> o.Label) |> List.sortBy fst |> List.map (fun (l, n) -> l, jint n))
                          "trials", jint trials.Length
                          "excludedX4", strs (excluded |> List.map (fun o -> o.RunId) |> ordinal)
                          "pairedIneligibleX2", strs (included |> List.filter (fun o -> not o.Paired) |> List.map (fun o -> o.RunId) |> ordinal) ]
          "primary", obj [ "label", str "preregistered primary outcome"
                           "definition", str "total estimated model cost (USD, F5 price table) per correctly completed requirement, pooled per arm; runs with 0 correct still add their cost; U6 excluded (R8); token-based equivalents alongside"
                           "perArm", withAndWithoutU2 pooledPrimary efficiency ]
          "hypotheses", arr hypotheses
          "reliability", reliability
          "rq6MechanismAttribution", rq6
          "u6", u6Report
          "descriptive", obj [ "label", str "exploratory (descriptive totals and rates; U6 included here, efficiency rows elsewhere exclude it)"
                               "perArm", byArm totals included
                               "perArmCategory", byArm (groupedBy (fun o -> o.Category) categories) included
                               "perArmTask", byArm (fun xs -> groupedBy (fun o -> o.Task) (tasksOf included) xs) included ]
          "difficulty", difficulty ]

let json = result.ToJsonString(JsonSerializerOptions(WriteIndented = true)) + "\n"
File.WriteAllText(outPath, json)
printfn "%s: %d trial observations (%d excluded, %d non-trial ignored)" outPath trials.Length excluded.Length ignored.Length
