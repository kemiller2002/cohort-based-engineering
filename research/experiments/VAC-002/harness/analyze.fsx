// VAC-002 analysis (F#, no dependencies beyond the SDK). Pure over committed observation files; I/O at the edges.
//
//   dotnet fsi --quiet --exec analyze.fsx units    RESULTS RUN FIXTURE            -> per-unit rows (JSON)
//   dotnet fsi --quiet --exec analyze.fsx summary  RESULTS RUN FIXTURE SEALED     -> RESULTS/RUN/analysis.json
//   dotnet fsi --quiet --exec analyze.fsx dataset  RESULTS RUN                    -> RESULTS/RUN/decision-dataset.jsonl (Layer 2)
//   dotnet fsi --quiet --exec analyze.fsx blind    RESULTS RUN WORK OUT SEED       -> OUT/items.jsonl + OUT/trees, STATE mapping
//
// Definitions: METRICS.md. Statistical plan: PREREGISTRATION.md (the pilot is descriptive: one chain per arm).
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes
open System.Text.RegularExpressions

let jstr (s: string) = JsonValue.Create(s) :> JsonNode
let jint (i: int64) = JsonValue.Create(i) :> JsonNode
let jdec (d: decimal) = JsonValue.Create(d) :> JsonNode
let jbool (b: bool) = JsonValue.Create(b) :> JsonNode
let jnull: JsonNode = null
let jopt f = function Some v -> f v | None -> jnull
let jarr (xs: JsonNode seq) = JsonArray(Seq.toArray xs) :> JsonNode
let jobj (kvs: (string * JsonNode) list) =
    let o = JsonObject()
    kvs |> List.iter (fun (k, v) -> o[k] <- v)
    o :> JsonNode
let pretty (n: JsonNode) = n.ToJsonString(JsonSerializerOptions(WriteIndented = true))
let tryParse (path: string) = if File.Exists path then (try Some(JsonNode.Parse(File.ReadAllText path)) with _ -> None) else None
let str (n: JsonNode) (k: string) =
    match n with
    | null -> None
    | _ -> match n[k] with :? JsonValue as v -> (try Some(v.GetValue<string>()) with _ -> None) | _ -> None
let items (n: JsonNode) (k: string) : JsonNode list =
    match n with
    | null -> []
    | _ -> match n[k] with :? JsonArray as a -> a |> Seq.filter (isNull >> not) |> Seq.toList | _ -> []
let num (n: JsonNode) (k: string) =
    match n with
    | null -> None
    | _ -> match n[k] with :? JsonValue as v -> (try Some(v.GetValue<decimal>()) with _ -> None) | _ -> None
let i64 n k = num n k |> Option.map int64 |> Option.defaultValue 0L
let bool (n: JsonNode) (k: string) =
    match n with
    | null -> false
    | _ -> match n[k] with :? JsonValue as v -> (try v.GetValue<bool>() with _ -> false) | _ -> false
let strings (n: JsonNode) (k: string) = items n k |> List.choose (fun x -> try Some(x.GetValue<string>()) with _ -> None)
let at (n: JsonNode) (path: string list) = path |> List.fold (fun (acc: JsonNode) k -> if isNull acc then null else acc[k]) n
let ratio (a: decimal) (b: decimal) = if b = 0m then None else Some(Math.Round(a / b, 6))

// ---------- Loading ----------
/// Amendment A1: the CLI reports total_cost_usd cumulatively over a session, so a turn's cost is its cumulative value
/// minus that of the session's previous turn. `costIndex` maps (session, cumulative cost) to the per-turn delta.
let turnCostDeltas (dir: string) =
    Directory.GetFiles(dir, "turn-*.json") |> Array.toList |> List.choose tryParse
    |> List.groupBy (fun t -> str t "sessionId" |> Option.defaultValue "")
    |> List.collect (fun (_, ts) ->
        ts |> List.sortBy (fun t -> str t "startedAt" |> Option.defaultValue "")
        |> List.fold (fun (prev, acc) t ->
            let c = num (at t [ "usage" ]) "costUsdCli"
            let delta = c |> Option.map (fun c -> c - prev)
            (defaultArg c prev), (str t "label" |> Option.defaultValue "", delta) :: acc) (0m, [])
        |> snd)
    |> Map.ofList

type Unit =
    { Arm: string; Position: int; Task: string; Fault: string; Kind: string; Categories: int list
      RequirementIds: string list; ConflictRequirementIds: string list
      Score: JsonNode option; FirstScore: JsonNode option; Gates: JsonNode list; Policy: JsonNode option
      Turns: JsonNode list; TurnCosts: decimal option list; Attempts: int }

let taskMeta (fixture: string) (task: string) = tryParse (Path.Combine(fixture, "tasks", task, "task.json")) |> Option.get

let loadArm (fixture: string) (dir: string) : Unit list =
    let arm = Path.GetFileName dir
    let costs = turnCostDeltas dir
    match tryParse (Path.Combine(dir, "setup.json")) with
    | None -> []
    | Some setup ->
        items setup "units"
        |> List.filter (fun u -> not (List.isEmpty (items u "attempts")))
        |> List.map (fun u ->
            let n = int (i64 u "unit")
            let task = str u "task" |> Option.get
            let meta = taskMeta fixture task
            let attempts = items u "attempts" |> List.length
            let score k = tryParse (Path.Combine(dir, sprintf "score-%d-%d.json" n k))
            let turns = Directory.GetFiles(dir, sprintf "turn-unit-%d*.json" n) |> Array.filter (fun f -> Regex.IsMatch(Path.GetFileName f, sprintf @"^turn-unit-%d(-repair-\d+)?\.json$" n)) |> Array.sort |> Array.toList |> List.choose tryParse
            { Arm = arm; Position = n; Task = task; Fault = str u "fault" |> Option.defaultValue "none"
              Kind = str meta "kind" |> Option.defaultValue ""
              Categories = items meta "categories" |> List.map (fun c -> c.GetValue<int>())
              RequirementIds = strings meta "requirementIds"; ConflictRequirementIds = strings meta "conflictRequirementIds"
              Score = score attempts; FirstScore = score 1
              Gates = [ 1..attempts ] |> List.choose (fun k -> tryParse (Path.Combine(dir, sprintf "gate-%d-%d.json" n k)))
              Policy = tryParse (Path.Combine(dir, sprintf "policy-%d.json" n))
              Turns = turns
              TurnCosts = turns |> List.map (fun t -> costs |> Map.tryFind (str t "label" |> Option.defaultValue "") |> Option.flatten)
              Attempts = attempts })
        |> List.sortBy (fun u -> u.Position)

let loadRun (fixture: string) (results: string) (run: string) =
    let root = Path.Combine(results, run)
    if Directory.Exists root then Directory.GetDirectories root |> Array.sort |> Array.toList |> List.map (fun d -> Path.GetFileName d, loadArm fixture d)
    else []

// ---------- Per-unit derived values ----------
let verdict (s: JsonNode option) k = s |> Option.map (fun s -> bool s["verdict"] k) |> Option.defaultValue false
let accepted u = verdict u.Score "accepted"
let functional u = verdict u.Score "functional"
let firstAccepted u = verdict u.FirstScore "accepted"
let claimed u = verdict u.FirstScore "claimedCompleted"
let falseCompletionFirst u = verdict u.FirstScore "falseCompletion"
let falseCompletionFinal u = verdict u.Score "falseCompletion"
let earlierFailing u = u.Score |> Option.map (fun s -> strings s["verdict"] "earlierTasksFailing") |> Option.defaultValue []
let buildBroken u = verdict u.Score "buildBroken"
let archPass u = u.Score |> Option.map (fun s -> bool s["architecture"] "pass") |> Option.defaultValue false
let detFindings u =
    u.Score |> Option.map (fun s -> items s["architecture"] "findings" |> List.filter (fun f -> str f "class" = Some "DET" && i64 f "severity" >= 2L)) |> Option.defaultValue []
let failingTests u = u.Score |> Option.map (fun s -> items s["oracle"] "failing" |> List.map (fun f -> str f "task" |> Option.defaultValue "", str f "test" |> Option.defaultValue "")) |> Option.defaultValue []
let unitCost u = u.TurnCosts |> fun cs -> if not (List.isEmpty cs) && cs |> List.forall Option.isSome then Some(cs |> List.sumBy Option.get) else None
let turnTokens (t: JsonNode) =
    let usage = at t [ "usage"; "usage" ]
    [ "input"; "output"; "cacheRead"; "cacheWrite" ] |> List.map (fun k -> k, i64 usage k)
let unitTokens u = u.Turns |> List.collect turnTokens |> List.groupBy fst |> List.map (fun (k, vs) -> k, vs |> List.sumBy snd)
let contextLast u = u.Turns |> List.tryHead |> Option.map (fun t -> i64 (at t [ "requests"; "context" ]) "last")
let compactions u = u.Turns |> List.sumBy (fun t -> max (i64 t["usage"] "compactBoundaries") (i64 t["requests"] "compactions"))
let contamination u = u.Turns |> List.sumBy (fun t -> int64 ((items t["usage"] "contaminationHits").Length + (items t["requests"] "contaminationHits").Length))
let toolUses u = u.Turns |> List.sumBy (fun t -> i64 t["usage"] "toolUses")
let wallMs u = u.Turns |> List.sumBy (fun t -> i64 t["usage"] "durationMs")
let gateMs u = u.Gates |> List.sumBy (fun g -> i64 g "verifyMs")
let tier u = u.Policy |> Option.bind (fun p -> str p "tier") |> Option.orElse (if List.isEmpty u.Gates then None else Some "high")
let reportText (s: JsonNode option) =
    s |> Option.map (fun s ->
        [ str s["claim"] "blockedReason" |> Option.defaultValue "" ] @ strings s["claim"] "openQuestions" @ strings s["claim"] "rejectedAssumptions"
        @ (items s["evidence"] "decisions" |> List.collect (fun d -> [ str d "statement" |> Option.defaultValue "" ])) |> String.concat "\n")
    |> Option.defaultValue ""

/// A critical failure (survival): a false completion, a regression of an earlier task, or a broken build at head.
let critical u = falseCompletionFinal u || not (List.isEmpty (earlierFailing u)) || buildBroken u

// ---------- Fault exposures (FAULT-CATALOG.md) ----------
let faultEval (units: Unit list) (workRoot: string option) =
    let byTask t = units |> List.tryFind (fun u -> u.Task = t)
    let failingIn (u: Unit) (task: string) (patterns: string list) =
        failingTests u |> List.filter (fun (t, n) -> t = task && (List.isEmpty patterns || patterns |> List.exists n.Contains))
    let rejectedText (u: Unit) (keys: string list) =
        let s = u.Score |> Option.map (fun s -> strings s["claim"] "rejectedAssumptions" |> String.concat "\n") |> Option.defaultValue ""
        keys |> List.exists (fun k -> s.ToLowerInvariant().Contains(k.ToLowerInvariant()))
    [ match byTask "L05" with
      | Some u ->
          let fails = failingIn u "L05" [ "oldest fine first"; "list is oldest first"; "old stores load" ]
          "F1-NEWEST-FIRST-FINES", u, (not (List.isEmpty fails)), rejectedText u [ "newest"; "oldest" ], "applicable", fails
      | None -> ()
      match byTask "L06" with
      | Some u ->
          let fails = failingIn u "L06" [ "no longer owed"; "skip waived"; "lifts the borrowing" ]
          "F2-OUTSTANDING-SKIPS-WAIVED", u, (not (List.isEmpty fails)), rejectedText u [ "outstanding"; "waived" ], "applicable", fails
      | None -> ()
      match byTask "L10" with
      | Some u ->
          let d1Fails = failingTests u |> List.filter (fun (t, n) -> (t = "L03" || t = "L09") || (t = "L10" && n.Contains "open deadline day is kept"))
          let visibleFail = u.Score |> Option.map (fun s -> i64 s["visibleTests"] "failed" > 0L) |> Option.defaultValue true
          "D1-OPENDAYS-2.0.0", u, (not (List.isEmpty d1Fails)), rejectedText u [ "nextOpen"; "OpenDays"; "2.0.0" ], "applicable", d1Fails
          "F3-GREEN-BUILD-REPORT", u, (visibleFail || claimed u && not (functional u)), rejectedText u [ "build report"; "build-reports"; "CI"; "all tests passed" ], "applicable", []
      | None -> () ]

// ---------- Propagation (METRICS.md §5) ----------
let propagation (units: Unit list) (map: JsonNode option) =
    match map with
    | None -> []
    | Some m ->
        (m["origins"] :?> JsonObject)
        |> Seq.map (fun kv ->
            let origin = kv.Key
            let task = str kv.Value "unit" |> Option.defaultValue ""
            let start = units |> List.tryFind (fun u -> u.Task = task) |> Option.map (fun u -> u.Position) |> Option.defaultValue Int32.MaxValue
            let deps = match kv.Value["dependentCases"] with :? JsonObject as o -> o |> Seq.map (fun d -> d.Key, d.Value.AsArray() |> Seq.map (fun x -> x.GetValue<string>()) |> Seq.toList) |> Seq.toList | _ -> []
            let patterns = strings kv.Value "citationPatterns"
            let later = units |> List.filter (fun u -> u.Position > start)
            let affected =
                later
                |> List.filter (fun u ->
                    let fails = failingTests u |> List.exists (fun (t, n) -> deps |> List.exists (fun (dt, cases) -> dt = t && cases |> List.exists n.Contains))
                    let cites = patterns |> List.exists (fun p -> (reportText u.Score).Contains p)
                    fails || cites)
            origin, start, affected |> List.map (fun u -> u.Position))
        |> Seq.toList

// ---------- Kaplan–Meier over chains ----------
let kaplanMeier (chains: (int * bool) list) =
    // (time, event) per chain; returns (time, survival) steps
    let times = chains |> List.filter snd |> List.map fst |> List.distinct |> List.sort
    times
    |> List.scan (fun (_, s) t ->
        let atRisk = chains |> List.filter (fun (tt, _) -> tt >= t) |> List.length
        let events = chains |> List.filter (fun (tt, e) -> e && tt = t) |> List.length
        t, (if atRisk = 0 then s else s * (1.0 - float events / float atRisk))) (0, 1.0)

// ---------- Per-arm summary ----------
let armSummary (fixture: string) (arm: string) (units: Unit list) (propMap: JsonNode option) =
    let n = units.Length
    let acc = units |> List.filter accepted
    let reqAccepted = acc |> List.sumBy (fun u -> (u.RequirementIds |> List.except u.ConflictRequirementIds).Length)
    let costs = units |> List.map unitCost
    let costKnown = costs |> List.forall Option.isSome
    let total = costs |> List.choose id |> List.sum
    // regressions: an earlier task, accepted at its own unit, failing at a later unit's head (counted once per (task, unit))
    let acceptedTasks = acc |> List.map (fun u -> u.Task) |> Set.ofList
    let regressionEvents = units |> List.collect (fun u -> earlierFailing u |> List.filter acceptedTasks.Contains |> List.map (fun t -> u.Position, t))
    let regressionOpps = units |> List.sumBy (fun u -> acc |> List.filter (fun a -> a.Position < u.Position) |> List.length)
    let faults = faultEval units None
    let faultAccepted = faults |> List.filter (fun (_, _, a, _, _, _) -> a) |> List.length
    let silentConflict = units |> List.filter (fun u -> not (List.isEmpty u.ConflictRequirementIds) && functional u && not (verdict u.Score "conflictSurfaced")) |> List.length
    let uf = units |> List.filter (accepted >> not) |> List.length
    let ce = uf + regressionEvents.Length + faultAccepted + silentConflict
    let firstCritical = units |> List.tryFind critical |> Option.map (fun u -> u.Position)
    let gates = units |> List.collect (fun u -> u.Gates |> List.mapi (fun i g -> u, i + 1, g))
    let gateFp = gates |> List.filter (fun (u, k, g) -> not (bool g "passed") && verdict (if k = 1 then u.FirstScore else u.Score) "accepted") |> List.length
    let gateFn = gates |> List.filter (fun (u, k, g) -> bool g "passed" && not (verdict (if k = 1 then u.FirstScore else u.Score) "accepted")) |> List.length
    let claimedN = units |> List.filter claimed |> List.length
    let fcFirst = units |> List.filter falseCompletionFirst |> List.length
    let avrUnits = units |> List.filter (detFindings >> List.isEmpty >> not) |> List.length
    let tokens = units |> List.collect unitTokens |> List.groupBy fst |> List.map (fun (k, vs) -> k, jint (vs |> List.sumBy snd))
    jobj [ "arm", jstr arm; "units", jint (int64 n)
           "accepted", jint (int64 acc.Length); "firstPassAccepted", jint (int64 (units |> List.filter firstAccepted |> List.length))
           "unitFailures", jint (int64 uf)
           "consequentialErrors", jobj [ "total", jint (int64 ce); "notAccepted", jint (int64 uf); "regressions", jint (int64 regressionEvents.Length); "premisesAccepted", jint (int64 faultAccepted); "silentConflicts", jint (int64 silentConflict) ]
           "regressionRate", (match regressionOpps with 0 -> jnull | o -> jdec (Math.Round(decimal regressionEvents.Length / decimal o, 4)))
           "regressionEvents", jarr (regressionEvents |> List.map (fun (p, t) -> jobj [ "position", jint (int64 p); "task", jstr t ]))
           "architecturalViolationRate", jdec (if n = 0 then 0m else Math.Round(decimal avrUnits / decimal n, 4))
           "unitsWithDetViolation", jarr (units |> List.filter (detFindings >> List.isEmpty >> not) |> List.map (fun u -> jstr (sprintf "%d:%s" u.Position u.Task)))
           "falseCompletion", jobj [ "claimed", jint (int64 claimedN); "firstPass", jint (int64 fcFirst); "final", jint (int64 (units |> List.filter falseCompletionFinal |> List.length)) ]
           "costUsdCli", (if costKnown then jdec (Math.Round(total, 4)) else jnull)
           "acceptedRequirements", jint (int64 reqAccepted)
           "costPerAcceptedRequirement", (if costKnown then jopt jdec (ratio total (decimal reqAccepted)) else jnull)
           "costPerUnit", (if costKnown && n > 0 then jdec (Math.Round(total / decimal n, 4)) else jnull)
           "tokens", jobj tokens
           "toolUses", jint (units |> List.sumBy toolUses); "agentWallMs", jint (units |> List.sumBy wallMs); "gateMs", jint (units |> List.sumBy gateMs)
           "compactions", jint (units |> List.sumBy (int64 << compactions)); "contaminationHits", jint (units |> List.sumBy contamination)
           "repairTurns", jint (int64 (units |> List.sumBy (fun u -> u.Attempts - 1)))
           "gate", jobj [ "runs", jint (int64 gates.Length); "rejections", jint (int64 (gates |> List.filter (fun (_, _, g) -> not (bool g "passed")) |> List.length)); "falsePositives", jint (int64 gateFp); "falseNegatives", jint (int64 gateFn) ]
           "survival", jobj [ "firstCriticalFailure", jopt (int64 >> jint) firstCritical; "censoredAt", jint (int64 n) ]
           "faults", jarr (faults |> List.map (fun (id, u, a, r, appl, fails) ->
               jobj [ "fault", jstr id; "unit", jint (int64 u.Position); "accepted", jbool a; "reportedAsFalse", jbool r; "exposure", jstr appl; "failingCases", jarr (fails |> List.map (fun (t, nm) -> jstr (t + ": " + nm))) ]))
           "propagation", jarr (propagation units propMap |> List.map (fun (o, start, ps) -> jobj [ "origin", jstr o; "originPosition", jint (int64 start); "depth", jint (int64 ps.Length); "affectedPositions", jarr (ps |> List.map (int64 >> jint)) ]))
           "perUnit", jarr (units |> List.map (fun u ->
               jobj [ "position", jint (int64 u.Position); "task", jstr u.Task; "kind", jstr u.Kind; "fault", jstr u.Fault
                      "accepted", jbool (accepted u); "functional", jbool (functional u); "firstPassAccepted", jbool (firstAccepted u)
                      "conflictSurfaced", jbool (verdict u.Score "conflictSurfaced"); "claimedCompleted", jbool (claimed u)
                      "falseCompletionFirst", jbool (falseCompletionFirst u); "earlierFailing", jarr (earlierFailing u |> List.map jstr)
                      "archPass", jbool (archPass u); "detFindings", jarr (detFindings u |> List.map (fun f -> jstr (sprintf "%s %s:%d" (str f "rule" |> Option.defaultValue "") (str f "file" |> Option.defaultValue "") (i64 f "line"))))
                      "oracleFailing", jarr (failingTests u |> List.map (fun (t, nm) -> jstr (t + ": " + nm)))
                      "costUsdCli", jopt (fun (c: decimal) -> jdec (Math.Round(c, 4))) (unitCost u); "contextLast", jopt jint (contextLast u)
                      "compactions", jint (int64 (compactions u)); "attempts", jint (int64 u.Attempts); "tier", jopt jstr (tier u)
                      "gatePassed", jarr (u.Gates |> List.map (fun g -> jbool (bool g "passed")))
                      "policySignals", jarr (u.Policy |> Option.map (fun p -> items p "signals" |> List.map (fun s -> jstr (str s "id" |> Option.defaultValue "")))|> Option.defaultValue []) ])) ]

let summary (results: string) (run: string) (fixture: string) (sealedDir: string) =
    let arms = loadRun fixture results run
    let propMap = tryParse (Path.Combine(sealedDir, "propagation-map.json"))
    let perArm = arms |> List.map (fun (a, us) -> a, armSummary fixture a us propMap)
    let km = arms |> List.map (fun (a, us) ->
        let first = us |> List.tryFind critical
        a, kaplanMeier [ (match first with Some u -> u.Position, true | None -> us.Length, false) ])
    jobj [ "schema", jstr "cbe.vac-002.analysis/1"; "run", jstr run; "generatedAt", jstr (DateTime.UtcNow.ToString("o"))
           "label", jstr "descriptive (one chain per arm); no hypothesis is tested on these data"
           "arms", jobj (perArm |> List.map (fun (a, s) -> a, s))
           "kaplanMeier", jobj (km |> List.map (fun (a, steps) -> a, jarr (steps |> List.map (fun (t, s) -> jobj [ "position", jint (int64 t); "survival", jdec (decimal (Math.Round(s, 4))) ])))) ]

// ---------- Layer 2 dataset and Layer 3 blinded bundle ----------
let datasetRows (results: string) (run: string) =
    Directory.GetDirectories(Path.Combine(results, run)) |> Array.sort |> Array.toList
    |> List.collect (fun dir ->
        let arm = Path.GetFileName dir
        Directory.GetFiles(dir, "score-*.json") |> Array.toList |> List.choose tryParse
        |> List.groupBy (fun s -> i64 s "unit") |> List.map (fun (_, ss) -> ss |> List.maxBy (fun s -> i64 s "attempt"))
        |> List.sortBy (fun s -> i64 s "unit")
        |> List.collect (fun s ->
            let failingReqs = items s["oracle"] "failing" |> List.collect (fun f -> strings f "requirements") |> Set.ofList
            items s["evidence"] "decisions" |> List.map (fun d ->
                let reqs = strings d "requirementIds"
                jobj [ "run", jstr run; "arm", jstr arm; "unit", jint (i64 s "unit"); "task", jstr (str s "task" |> Option.defaultValue ""); "fault", jstr (str s "fault" |> Option.defaultValue "none")
                       "attempt", jint (i64 s "attempt"); "head", jstr (str s "head" |> Option.defaultValue ""); "decisionId", jopt jstr (str d "id"); "statement", jopt jstr (str d "statement")
                       "basis", jopt jstr (str d "basis"); "evidence", jarr (items d "refs" |> List.choose (fun r -> str r "ref") |> List.map jstr)
                       "layer1", jopt jstr (str d "layer1"); "invalidRefs", jarr (items d "refs" |> List.filter (fun r -> r["valid"] <> null && not (r["valid"].GetValue<bool>())) |> List.choose (fun r -> str r "ref") |> List.map jstr)
                       "requirementIds", jarr (reqs |> List.map jstr)
                       "outcome", jobj [ "unitAccepted", jbool (bool s["verdict"] "accepted"); "requirementFailing", jarr (reqs |> List.filter (fun r -> failingReqs |> Set.exists (fun f -> f = r || f.StartsWith r)) |> List.map jstr) ]
                       "layer3", jnull ])))

let blind (results: string) (run: string) (work: string) (out: string) (seed: int) =
    let rows = datasetRows results run
    let key (r: JsonNode) = "K" + (Security.Cryptography.SHA256.HashData(Text.Encoding.UTF8.GetBytes(sprintf "%d|%s|%s|%d|%s" seed run (str r "arm" |> Option.get) (i64 r "unit") (str r "decisionId" |> Option.defaultValue ""))) |> Convert.ToHexString).Substring(0, 10).ToLowerInvariant()
    let treeKey (r: JsonNode) = "T" + (Security.Cryptography.SHA256.HashData(Text.Encoding.UTF8.GetBytes(sprintf "%d|%s|%s|%d" seed run (str r "arm" |> Option.get) (i64 r "unit"))) |> Convert.ToHexString).Substring(0, 8).ToLowerInvariant()
    let rnd = Random(seed)
    let must (r: JsonNode) = (str r "layer1" = Some "invalid-evidence" || str r "layer1" = Some "no-evidence" || str r "fault" <> Some "none" || List.contains (str r "task" |> Option.defaultValue "") [ "L04"; "L08" ])
    let chosen = rows |> List.filter (fun r -> must r || rnd.NextDouble() < 0.25) |> List.sortBy key
    Directory.CreateDirectory(Path.Combine(out, "trees")) |> ignore
    let trees =
        chosen |> List.map (fun r -> treeKey r, (str r "arm" |> Option.get, str r "head" |> Option.get)) |> List.distinct
    trees |> List.iter (fun (tk, (arm, head)) ->
        let dest = Path.Combine(out, "trees", tk)
        if not (Directory.Exists dest) then
            Directory.CreateDirectory dest |> ignore
            let repo = Path.Combine(work, run, arm, "repo")
            let p = Diagnostics.Process.Start(Diagnostics.ProcessStartInfo("bash", sprintf "-c \"git -C '%s' archive '%s' -- . ':(exclude).ros' ':(exclude).praxis' ':(exclude)docs/decisions/DECISIONS.md' ':(exclude).vac/verified-state.json' ':(exclude)contracts' | tar -x -C '%s'\"" repo head dest))
            p.WaitForExit())
    let itemsOut =
        chosen |> List.map (fun r ->
            let tk = treeKey r
            jobj [ "key", jstr (key r); "tree", jstr ("trees/" + tk); "task", jopt jstr (str r "task"); "requirement", jstr (sprintf "trees/%s/requirements/%s.md" tk (str r "task" |> Option.defaultValue ""))
                   "statement", jopt jstr (str r "statement"); "basis", jopt jstr (str r "basis"); "evidence", r["evidence"].DeepClone() ])
    File.WriteAllLines(Path.Combine(out, "items.jsonl"), itemsOut |> List.map (fun i -> i.ToJsonString()))
    let mapping = jobj [ "seed", jint (int64 seed); "items", jobj (chosen |> List.map (fun r -> key r, jobj [ "run", jstr run; "arm", r["arm"].DeepClone(); "unit", r["unit"].DeepClone(); "decisionId", (match r["decisionId"] with null -> jnull | d -> d.DeepClone()); "layer1", (match r["layer1"] with null -> jnull | d -> d.DeepClone()); "fault", r["fault"].DeepClone(); "task", r["task"].DeepClone() ])) ]
    chosen.Length, trees.Length, mapping


// ---------- Phase G: prevention, detection, correction, escape (from turn streams, gates and scores) ----------
/// (command, result text) for every Bash tool call in a turn stream.
let bashCalls (streamPath: string) =
    if not (File.Exists streamPath) then [] else
    let lines = File.ReadAllLines streamPath |> Array.toList |> List.choose (fun l -> try Some(JsonNode.Parse l) with _ -> None)
    let content (o: JsonNode) = match o["message"] with null -> [] | m -> items m "content"
    let uses = lines |> List.filter (fun o -> str o "type" = Some "assistant") |> List.collect content
               |> List.filter (fun c -> str c "type" = Some "tool_use" && str c "name" = Some "Bash")
               |> List.map (fun c -> str c "id" |> Option.defaultValue "", (match c["input"] with null -> "" | i -> str i "command" |> Option.defaultValue ""))
    let results = lines |> List.filter (fun o -> str o "type" = Some "user") |> List.collect content
                  |> List.filter (fun c -> str c "type" = Some "tool_result")
                  |> List.map (fun c -> str c "tool_use_id" |> Option.defaultValue "", (match c["content"] with :? JsonValue as v -> (try v.GetValue<string>() with _ -> "") | :? JsonArray as a -> a |> Seq.choose (fun x -> str x "text") |> String.concat "\n" | _ -> ""))
                  |> Map.ofList
    uses |> List.map (fun (id, cmd) -> cmd, results |> Map.tryFind id |> Option.defaultValue "")

let phaseG (state: string) (results: string) (run: string) (fixture: string) =
    loadRun fixture results run
    |> List.collect (fun (arm, units) ->
        units |> List.map (fun u ->
            let streams = Directory.GetFiles(Path.Combine(state, run, arm, "turns"), sprintf "unit-%d*.stream.jsonl" u.Position) |> Array.filter (fun f -> Regex.IsMatch(Path.GetFileName f, sprintf @"^unit-%d(-repair-\d+)?\.stream\.jsonl$" u.Position)) |> Array.sort |> Array.toList
            let calls = streams |> List.collect bashCalls
            let arch = calls |> List.filter (fun (c, _) -> c.Contains "archcheck")
            let archFail = arch |> List.filter (fun (_, r) -> Regex.IsMatch(r, @"summary: DET sev3=\d+ sev2=\d+.*FAIL") || Regex.IsMatch(r, @"ARC-(DEP|SYM|BND)-\d+ [23] "))
            let ordo = calls |> List.filter (fun (c, _) -> c.Contains "ordo ecir check")
            let ordoRefused = ordo |> List.exists (fun (_, r) -> r.Contains "ORDO.CONTRACT.UNRESOLVED_CONFLICT")
            let compilerRef = calls |> List.exists (fun (c, r) -> c.Contains "dotnet" && Regex.IsMatch(r, @"error (FS0039|MSB4006|NU1108)|cycle", RegexOptions.IgnoreCase) && r.Contains "Lending.")
            let gateArchFail = u.Gates |> List.exists (fun g -> items g "checks" |> List.exists (fun c -> str c "check" = Some "architecture" && not (bool c "passed")))
            let finalViolation = not (List.isEmpty (detFindings u))
            let firstViolation = u.FirstScore |> Option.map (fun s -> items s["architecture"] "findings" |> List.exists (fun f -> str f "class" = Some "DET" && i64 f "severity" >= 2L)) |> Option.defaultValue false
            let proposed = not (List.isEmpty archFail) || gateArchFail || firstViolation || finalViolation
            jobj [ "arm", jstr arm; "position", jint (int64 u.Position); "task", jstr u.Task; "kind", jstr u.Kind
                   "archcheckRuns", jint (int64 arch.Length); "archcheckFailedInLoop", jint (int64 archFail.Length)
                   "ordoRuns", jint (int64 ordo.Length); "ordoRefusedConflict", jbool ordoRefused; "compilerRejectedReference", jbool compilerRef
                   "invalidProposed", jbool proposed; "detectedInLoop", jbool (not (List.isEmpty archFail)); "detectedByGate", jbool gateArchFail
                   "corrected", jbool (proposed && not finalViolation); "escaped", jbool finalViolation ]))

match fsi.CommandLineArgs |> Array.toList |> List.tail with
| "units" :: results :: run :: fixture :: _ -> loadRun fixture results run |> List.iter (fun (a, us) -> printfn "%s: %d units" a us.Length)
| "summary" :: results :: run :: fixture :: sealedDir :: _ ->
    let s = summary results run fixture sealedDir
    File.WriteAllText(Path.Combine(results, run, "analysis.json"), pretty s)
    printfn "%s" (Path.Combine(results, run, "analysis.json"))
| "dataset" :: results :: run :: _ ->
    let rows = datasetRows results run
    File.WriteAllLines(Path.Combine(results, run, "decision-dataset.jsonl"), rows |> List.map (fun r -> r.ToJsonString()))
    printfn "%d" rows.Length
| "blind" :: results :: run :: work :: out :: seed :: mappingOut :: _ ->
    let n, t, mapping = blind results run work out (int seed)
    File.WriteAllText(mappingOut, pretty mapping)
    printfn "%d items, %d trees" n t
| "phaseg" :: state :: results :: run :: fixture :: _ ->
    let rows = phaseG state results run fixture
    File.WriteAllText(Path.Combine(results, run, "phase-g.json"), pretty (jarr rows))
    printfn "%d units" rows.Length
| _ -> eprintfn "usage: analyze.fsx units|summary|dataset|blind|phaseg ..."; exit 2
