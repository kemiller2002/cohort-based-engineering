// VAC-002 harness functions (F#; pure where possible, I/O at the edges). Adapted from VAC-001 harness/vac.fsx
// (JSON helpers, Layer 1 evidence, observation, verified state), with VAC-002's task ids, gate, adaptive policy
// and K1 usage. Transcript-level usage and the X4 contamination scan are delegated to VAC-001 vac.fsx `usage`.
//
//   dotnet fsi --quiet --exec vac2.fsx render   --arm A --unit N --task L01 ... (see vac2.sh stage)
//   dotnet fsi --quiet --exec vac2.fsx evidence TREE UNIT
//   dotnet fsi --quiet --exec vac2.fsx observe  --run R --arm A --unit N --attempt K ... (scoring; hidden oracle)
//   dotnet fsi --quiet --exec vac2.fsx gate     --tier T --tests-log L --arch A.json --evidence E.json ... (no oracle)
//   dotnet fsi --quiet --exec vac2.fsx policy   --policy P.json --pre PRE.json --post POST.json
//   dotnet fsi --quiet --exec vac2.fsx state    --gate G.json --previous PREV --report R --unit N --task T --external X
//   dotnet fsi --quiet --exec vac2.fsx stream   --stream S.jsonl --prices TABLE    (K1 result events: final usage, cost)
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes
open System.Text.RegularExpressions
open System.Xml.Linq

// ---------- JSON helpers (as VAC-001) ----------
let jstr (s: string) = JsonValue.Create(s) :> JsonNode
let jint (i: int64) = JsonValue.Create(i) :> JsonNode
let jdec (d: decimal) = JsonValue.Create(d) :> JsonNode
let jbool (b: bool) = JsonValue.Create(b) :> JsonNode
let jnull: JsonNode = null
let jarr (xs: JsonNode seq) = JsonArray(Seq.toArray xs) :> JsonNode
let jobj (kvs: (string * JsonNode) list) =
    let o = JsonObject()
    kvs |> List.iter (fun (k, v) -> o[k] <- v)
    o :> JsonNode
let pretty (n: JsonNode) = n.ToJsonString(JsonSerializerOptions(WriteIndented = true))
let tryParse (path: string) =
    if File.Exists path then (try Some(JsonNode.Parse(File.ReadAllText path)) with _ -> None) else None
let str (n: JsonNode) (k: string) =
    match n with
    | null -> None
    | _ -> match n[k] with :? JsonValue as v -> (try Some(v.GetValue<string>()) with _ -> None) | _ -> None
let items (n: JsonNode) (k: string) : JsonNode list =
    match n with
    | null -> []
    | _ -> match n[k] with :? JsonArray as a -> a |> Seq.filter (fun x -> not (isNull x)) |> Seq.toList | _ -> []
let i64 (n: JsonNode) (k: string) =
    match n with
    | null -> 0L
    | _ -> match n[k] with :? JsonValue as v -> (try v.GetValue<int64>() with _ -> (try int64 (v.GetValue<decimal>()) with _ -> 0L)) | _ -> 0L
let bool (n: JsonNode) (k: string) =
    match n with
    | null -> false
    | _ -> match n[k] with :? JsonValue as v -> (try v.GetValue<bool>() with _ -> false) | _ -> false
let strings (n: JsonNode) (k: string) = items n k |> List.choose (fun x -> try Some(x.GetValue<string>()) with _ -> Some(x.ToJsonString()))
let args (argv: string list) =
    let rec go acc =
        function
        | (k: string) :: v :: rest when k.StartsWith "--" -> go (Map.add (k.TrimStart('-')) v acc) rest
        | _ :: rest -> go acc rest
        | [] -> acc
    go Map.empty argv
let readText (path: string) = if File.Exists path then File.ReadAllText path else ""

// ---------- Brief rendering (pure: template sections + values) ----------
let sections (text: string) =
    let parts = Regex.Split(text, @"<!-- section: ([a-zA-Z-]+) -->\n")
    [ for i in 1..2 .. parts.Length - 2 -> parts[i], parts[i + 1] ] |> Map.ofList
let fill (values: Map<string, string>) (template: string) =
    Regex.Replace(template, @"\{\{([A-Z_]+)\}\}", fun m -> values |> Map.tryFind m.Groups[1].Value |> Option.defaultValue m.Value)

let faultNote (faultsPath: string) (fault: string) =
    if fault = "none" then ""
    else
        let faults = tryParse faultsPath |> Option.get
        let f = items faults "faults" |> List.find (fun f -> str f "id" = Some fault)
        "## Context from the team lead\n\n" + (str f "note" |> Option.defaultValue "") + "\n"

/// Arms: A fresh per unit; B long-lived; C long-lived + Ordo; D long-lived + full; E long-lived + adaptive; F restarted + full.
let render (a: Map<string, string>) =
    let s = sections (File.ReadAllText(Path.Combine(a["briefs"], "brief.md")))
    let arm, unit, task = a["arm"], int a["unit"], a["task"]
    let restart = a.TryFind "restart" = Some "yes"
    let previous = if unit > 1 then sprintf "The previous unit's report is `.vac/reports/unit-%d.json`." (unit - 1) else "This is the first unit."
    let values =
        Map.ofList [ "UNIT", string unit; "TASK", task; "ITEM", "LEND-" + task; "REPO", a["repo"]; "ENV", a["env"]
                     "WORKSPACE", a["workspace"]; "DIRECTIVES", a["directives"]; "PREVIOUS", previous
                     "NOTE", faultNote a["faults"] a["fault"] ]
    let continuity =
        match arm with
        | "A" -> s["continuity-A"]
        | "F" when restart && unit > 1 -> s["continuity-F"]
        | _ -> s["continuity-L"]
    let first = arm = "A" || unit = 1 || restart
    let intro = if first then s["intro-first"] else s["intro-next"]
    let controls =
        match arm with
        | "C" -> [ s["controls-C"] ]
        | "D" | "F" -> [ s["controls-C"]; s["controls-D"] ]
        | "E" -> [ s["controls-C"]; s["controls-E"] ]
        | _ -> []
    let values = values |> Map.add "CONTINUITY" (fill values continuity |> fun t -> t.Trim())
    [ intro; s["task"] ] @ controls @ [ s["report"] ]
    |> List.map (fun part -> (fill values part).Trim() + "\n")
    |> String.concat "\n"

let renderRepair (a: Map<string, string>) =
    let s = sections (File.ReadAllText(Path.Combine(a["briefs"], "brief.md")))
    let gate = tryParse a["gate"] |> Option.get
    let failures = items gate "feedback" |> List.choose (fun f -> try Some("- " + f.GetValue<string>()) with _ -> None) |> String.concat "\n"
    let values =
        Map.ofList [ "UNIT", a["unit"]; "HEAD", (str gate "head" |> Option.defaultValue ""); "FAILURES", failures
                     "PRAXIS", (if a.TryFind "praxis" = Some "yes" then " (and the Praxis state)" else "") ]
    (fill values s["repair"]).Trim() + "\n"

// ---------- Layer 1: deterministic evidence validation of a unit report (VAC-001 rule, LEND identifiers) ----------
type RefCheck = { Ref: string; Kind: string; Valid: bool option; Why: string }
let idPattern = @"\b(?:DEC|CONFLICT|VERIFY|LEND|COHORT)-[\w-]+|\bU\d+-D\d+\b"
let knownIdsIn (tree: string) =
    [ "requirements"; "contracts"; "docs"; ".vac/reports" ]
    |> List.map (fun d -> Path.Combine(tree, d))
    |> List.filter Directory.Exists
    |> List.collect (fun d -> Directory.GetFiles(d, "*", SearchOption.AllDirectories) |> Array.toList)
    |> List.collect (fun f -> Regex.Matches(File.ReadAllText f, idPattern) |> Seq.map (fun m -> m.Value.TrimEnd('-')) |> Seq.toList)
    |> Set.ofList
let checkRef (tree: string) (knownIds: Set<string>) (r: string) : RefCheck =
    let exists p = File.Exists(Path.Combine(tree, p)) || Directory.Exists(Path.Combine(tree, p))
    let read p = readText (Path.Combine(tree, p))
    let r' = r.Trim().Trim('`')
    let briefProvided = [ "DIRECTIVES.md"; "env.sh" ]
    let pathPart = r'.Split('#').[0].Trim()
    match r' with
    | _ when briefProvided |> List.exists (fun f -> pathPart = f || pathPart.EndsWith("/" + f)) -> { Ref = r; Kind = "brief-provided"; Valid = Some true; Why = "" }
    | _ when Regex.IsMatch(r', @"^[0-9a-f]{7,40}$") -> { Ref = r; Kind = "commit"; Valid = None; Why = "commit refs are not checked from an exported tree" }
    | _ when Regex.IsMatch(r', @"^(DEC|U\d+-D|CONFLICT|VERIFY|LEND|COHORT)-?[\w-]*$") && not (r'.Contains "/") ->
        { Ref = r; Kind = "record"; Valid = Some(knownIds.Contains r'); Why = if knownIds.Contains r' then "" else "identifier not found in requirements, contracts, decisions or reports" }
    | _ ->
        let path, anchor = match r'.Split('#', 2) with [| p; a |] -> p.Trim(), Some(a.Trim()) | x -> x[0].Trim(), None
        let path = Regex.Replace(path, @":\d+(-\d+)?$", "")
        if not (exists path) then { Ref = r; Kind = "file"; Valid = Some false; Why = "path does not exist" }
        else
            match anchor with
            | None -> { Ref = r; Kind = "file"; Valid = Some true; Why = "" }
            | Some a ->
                let symbol = Regex.Replace(a, @"^(L\d+.*|R\d+)$", "")
                let token = symbol.Split([| ' '; '('; ':' |], StringSplitOptions.RemoveEmptyEntries) |> Array.tryHead |> Option.defaultValue symbol
                let ok = symbol = "" || (read path).Contains token
                { Ref = r; Kind = "symbol"; Valid = Some ok; Why = if ok then "" else "anchor text not found in file" }
let evidence (tree: string) (unit: int) =
    let path = Path.Combine(tree, ".vac", "reports", sprintf "unit-%d.json" unit)
    match tryParse path with
    | None -> jobj [ "schema", jstr "cbe.vac-002.evidence/1"; "unit", jint (int64 unit); "reportPresent", jbool (File.Exists path); "reportParses", jbool false; "decisions", jarr [] ]
    | Some report ->
        let known = knownIdsIn tree
        let decisions =
            items report "decisions"
            |> List.map (fun d ->
                let refs = strings d "evidence"
                let checks = refs |> List.map (checkRef tree known)
                let reqs = strings d "requirementIds"
                let badReqs = reqs |> List.filter (fun r -> not (known.Contains r) && not (known |> Set.exists (fun k -> k.StartsWith r)))
                let basis = str d "basis" |> Option.defaultValue "unstated"
                let invalid = checks |> List.filter (fun c -> c.Valid = Some false)
                let layer1 =
                    match basis with
                    | "assumption" -> "recorded-assumption"
                    | _ when List.isEmpty refs -> "no-evidence"
                    | _ when not (List.isEmpty invalid) || not (List.isEmpty badReqs) -> "invalid-evidence"
                    | _ -> "evidence-valid"
                jobj [ "id", (str d "id" |> Option.map jstr |> Option.defaultValue jnull)
                       "statement", (str d "statement" |> Option.map jstr |> Option.defaultValue jnull)
                       "basis", jstr basis; "layer1", jstr layer1
                       "requirementIds", jarr (reqs |> List.map jstr)
                       "refs", jarr (checks |> List.map (fun c -> jobj [ "ref", jstr c.Ref; "kind", jstr c.Kind; "valid", (match c.Valid with Some b -> jbool b | None -> jnull); "why", jstr c.Why ]))
                       "unknownRequirementIds", jarr (badReqs |> List.map jstr) ])
        jobj [ "schema", jstr "cbe.vac-002.evidence/1"; "unit", jint (int64 unit); "reportPresent", jbool true; "reportParses", jbool true
               "outcome", (str report "outcome" |> Option.map jstr |> Option.defaultValue jnull)
               "decisions", jarr decisions ]

// ---------- Test results (repository tests and hidden oracle) ----------
type Case = { Name: string; Outcome: string }
let trxCases (path: string) =
    if File.Exists path then
        XDocument.Load(path).Descendants()
        |> Seq.filter (fun e -> e.Name.LocalName = "UnitTestResult")
        |> Seq.map (fun e -> { Name = e.Attribute(XName.Get "testName").Value; Outcome = e.Attribute(XName.Get "outcome").Value })
        |> Seq.toList
    else []
let testSummary (log: string) =
    let text = readText log
    let m = Regex.Matches(text, @"(Passed|Failed)!\s+-\s+Failed:\s+(\d+),\s+Passed:\s+(\d+)")
    {| Built = m.Count > 0
       Passed = m |> Seq.sumBy (fun x -> int x.Groups[3].Value)
       Failed = m |> Seq.sumBy (fun x -> int x.Groups[2].Value)
       CompilerErrors = Regex.Matches(text, @" error FS\d+").Count
       FailedNames = Regex.Matches(text, @"^\s+Failed (\S.*?) \[[^\]]*\]\s*$", RegexOptions.Multiline) |> Seq.map (fun x -> x.Groups[1].Value) |> Seq.distinct |> Seq.toList |}

// ---------- Report text and conflict surfacing ----------
let reportText (report: JsonNode option) =
    report
    |> Option.map (fun r ->
        [ str r "blockedReason" |> Option.defaultValue ""; str r "handoff" |> Option.defaultValue "" ]
        @ strings r "openQuestions" @ strings r "knownIssues" @ strings r "rejectedAssumptions"
        @ (items r "decisions" |> List.collect (fun d -> [ str d "statement" |> Option.defaultValue "" ] @ strings d "evidence"))
        |> String.concat "\n")
    |> Option.defaultValue ""
/// A conflict counts as surfaced when the report names the conflicting requirement, names at least one rule it
/// conflicts with, and calls it a conflict (or contradiction, or an open/unresolved question). Layer 3 confirms.
let conflictSurfaced (task: JsonNode) (text: string) =
    let lower = text.ToLowerInvariant()
    let named = strings task "conflictRequirementIds" |> List.forall (fun r -> text.Contains r)
    let counterpart =
        match str task "id" with
        | Some "L04" -> [ "LEND-L04-R2"; "LEND-L01-R2"; "DEC-005"; "owes more than 5"; "suspend" ] |> List.exists (fun k -> lower.Contains(k.ToLowerInvariant()))
        | Some "L08" -> text.Contains "DEC-008"
        | _ -> true
    let word = [ "conflict"; "contradict"; "inconsisten"; "unresolved"; "incompatible"; "cannot both" ] |> List.exists lower.Contains
    named && counterpart && word

// ---------- Scoring observation (hidden oracle; never shown to an agent) ----------
let findingJson (f: JsonNode) =
    let s k = str f k |> Option.map jstr |> Option.defaultValue jnull
    jobj [ "rule", s "ruleId"; "class", s "class"; "severity", jint (i64 f "severity"); "file", s "file"; "line", jint (i64 f "line"); "message", s "message" ]
let archJson (arch: JsonNode option) (passed: bool) =
    match arch with
    | Some j ->
        jobj [ "pass", jbool passed
               "summary", j["summary"].DeepClone()
               "errors", (match j["errors"] with null -> jarr [] | e -> e.DeepClone())
               "findings", jarr (items j "findings" |> List.map findingJson) ]
    | None -> jobj [ "pass", jbool false; "summary", jnull; "errors", jarr [ jstr "no archcheck report" ] ]
let observe (a: Map<string, string>) =
    let unit = int a["unit"]
    let task = a["task"]
    let staged = a["staged"].Split(',', StringSplitOptions.RemoveEmptyEntries) |> Array.toList
    let taskJson = tryParse (Path.Combine(a["fixture"], "tasks", task, "task.json")) |> Option.get
    let tests = testSummary a["tests-log"]
    let oracleDir = a["oracle-dir"]
    let byTask t =
        let cases = trxCases (Path.Combine(oracleDir, t + ".trx"))
        let log = testSummary (Path.Combine(oracleDir, t + ".log"))
        t, cases, log.CompilerErrors
    let oracle = staged |> List.map byTask
    let taskPass t = oracle |> List.exists (fun (t', cs, _) -> t' = t && not (List.isEmpty cs) && cs |> List.forall (fun c -> c.Outcome = "Passed"))
    let arch = tryParse a["arch"]
    let archPassed = arch |> Option.map (fun j -> bool j["summary"] "pass") |> Option.defaultValue false
    let report = tryParse a["report"]
    let claimed = report |> Option.bind (fun r -> str r "outcome") |> Option.defaultValue "no-report"
    let finalLine = readText a["final"] |> fun t -> Regex.Match(t, @"OUTCOME:\s*(completed|blocked)").Groups[1].Value
    let dirty = int a["dirty"]
    let buildOk = tests.Built && tests.CompilerErrors = 0
    let visibleOk = buildOk && tests.Failed = 0
    let text = reportText report
    let isConflictTask = not (List.isEmpty (strings taskJson "conflictRequirementIds"))
    let surfaced = isConflictTask && conflictSurfaced taskJson text
    let functional = visibleOk && taskPass task && archPassed && dirty = 0
    let accepted = functional && (not isConflictTask || surfaced)
    let regressions = staged |> List.filter (fun t -> t <> task) |> List.filter (taskPass >> not)
    let claimedCompleted = claimed = "completed" || finalLine = "completed"
    let failing = oracle |> List.collect (fun (t, cs, _) -> cs |> List.filter (fun c -> c.Outcome <> "Passed") |> List.map (fun c -> t, c.Name))
    let reqOf (name: string) = Regex.Matches(name, @"LEND-L\d+(-R\d+)?") |> Seq.map (fun m -> m.Value) |> Seq.toList
    jobj [ "schema", jstr "cbe.vac-002.observation/1"; "run", jstr a["run"]; "arm", jstr a["arm"]; "unit", jint (int64 unit)
           "attempt", jint (int64 (int a["attempt"])); "task", jstr task; "fault", jstr a["fault"]; "head", jstr a["head"]
           "verifiedAt", jstr (DateTime.UtcNow.ToString("o")); "verifyMs", jint (int64 a["verify-ms"])
           "stagedTasks", jarr (staged |> List.map jstr); "uncommittedPaths", jint (int64 dirty)
           "build", jobj [ "ok", jbool buildOk; "compilerErrors", jint (int64 tests.CompilerErrors) ]
           "visibleTests", jobj [ "passed", jint (int64 tests.Passed); "failed", jint (int64 tests.Failed); "failedNames", jarr (tests.FailedNames |> List.map jstr) ]
           "oracle", jobj [ "byTask", jobj (oracle |> List.map (fun (t, cs, ce) ->
                                t, jobj [ "cases", jint (int64 cs.Length); "failed", jint (int64 (cs |> List.filter (fun c -> c.Outcome <> "Passed")).Length); "compilerErrors", jint (int64 ce) ]))
                            "failing", jarr (failing |> List.map (fun (t, n) -> jobj [ "task", jstr t; "test", jstr n; "requirements", jarr (reqOf n |> List.map jstr) ])) ]
           "architecture", archJson arch archPassed
           "evidence", (match tryParse a["evidence"] with Some j -> j.DeepClone() | None -> jnull)
           "claim", jobj [ "report", jstr claimed; "finalLine", jstr finalLine; "blockedReason", (report |> Option.bind (fun r -> str r "blockedReason") |> Option.map jstr |> Option.defaultValue jnull)
                           "openQuestions", jarr (report |> Option.map (fun r -> strings r "openQuestions") |> Option.defaultValue [] |> List.map jstr)
                           "rejectedAssumptions", jarr (report |> Option.map (fun r -> strings r "rejectedAssumptions") |> Option.defaultValue [] |> List.map jstr) ]
           "verdict", jobj [ "functional", jbool functional; "conflictTask", jbool isConflictTask; "conflictSurfaced", jbool surfaced
                             "accepted", jbool accepted; "claimedCompleted", jbool claimedCompleted
                             "falseCompletion", jbool (claimedCompleted && not functional)
                             "earlierTasksFailing", jarr (regressions |> List.map jstr); "buildBroken", jbool (not buildOk) ] ]

// ---------- Gate (Dokimos role; host-run, independent of the agent, never the hidden oracle) ----------
let checkNames =
    Map.ofList [ "build", "the solution builds"; "repositoryTests", "every repository test passes"; "cleanTree", "the worktree is clean"
                 "architecture", "archcheck (full Lending policy) passes"; "contractAdmission", "the staged contract is re-checked with Ordo"
                 "conflictRecorded", "a contract conflict is recorded in the report"; "reportEvidence", "every decision's evidence exists"
                 "claimConsistency", "the report's claim agrees with the checks" ]
let gate (a: Map<string, string>) =
    let policy = tryParse a["policy"] |> Option.get
    let tier = a["tier"]
    let checks = strings policy["tiers"].[tier] "checks"
    let tests = testSummary a["tests-log"]
    let arch = tryParse a["arch"]
    let ev = tryParse a["evidence"]
    let report = tryParse a["report"]
    let taskJson = tryParse a["task"] |> Option.get
    let ordoAdmits = a.TryFind "ordo-admits" |> Option.map ((=) "true")
    let buildOk = tests.Built && tests.CompilerErrors = 0
    let claimed = report |> Option.bind (fun r -> str r "outcome") |> Option.defaultValue "no-report"
    let result name : bool * string list =
        match name with
        | "build" -> buildOk, (if buildOk then [] else [ sprintf "The solution does not build (%d compiler errors)." tests.CompilerErrors ])
        | "repositoryTests" ->
            let ok = buildOk && tests.Failed = 0
            ok, (if ok || not buildOk then [] else (sprintf "%d repository test(s) fail:" tests.Failed) :: (tests.FailedNames |> List.truncate 20 |> List.map (sprintf "  failing test `%s`")))
        | "cleanTree" -> let d = int a["dirty"] in d = 0, (if d = 0 then [] else [ sprintf "The worktree has %d uncommitted path(s)." d ])
        | "architecture" ->
            let ok = arch |> Option.map (fun j -> bool j["summary"] "pass") |> Option.defaultValue false
            let fs = arch |> Option.map (fun j -> items j "findings" |> List.filter (fun f -> str f "class" = Some "DET" && i64 f "severity" >= 2L)) |> Option.defaultValue []
            let errs = arch |> Option.map (fun j -> strings j "errors") |> Option.defaultValue [ "archcheck produced no report" ]
            ok, (if ok then [] else (fs |> List.map (fun f -> sprintf "Architecture %s: %s:%d %s" (str f "ruleId" |> Option.defaultValue "") (str f "file" |> Option.defaultValue "") (i64 f "line") (str f "message" |> Option.defaultValue ""))) @ (errs |> List.map (sprintf "Architecture check could not evaluate: %s")))
        | "contractAdmission" -> true, []
        | "conflictRecorded" ->
            let conflict = ordoAdmits = Some false || not (List.isEmpty (strings taskJson "conflictRequirementIds"))
            let ok = not conflict || (ordoAdmits = Some false && (let t = reportText report in strings taskJson "conflictIds" |> List.exists t.Contains || strings taskJson "conflictRequirementIds" |> List.forall t.Contains))
            ok, (if ok then [] else [ "Ordo refuses the contract for this unit (an unresolved conflict), and the report does not record the conflict and the requirements it names under openQuestions." ])
        | "reportEvidence" ->
            let bad = ev |> Option.map (fun e -> items e "decisions" |> List.filter (fun d -> str d "layer1" = Some "invalid-evidence")) |> Option.defaultValue []
            let present = ev |> Option.map (fun e -> bool e "reportParses") |> Option.defaultValue false
            present && List.isEmpty bad,
            (if not present then [ "The completion report is missing or is not valid JSON." ] else [])
            @ (bad |> List.map (fun d -> sprintf "Decision %s cites evidence that does not exist: %s" (str d "id" |> Option.defaultValue "?") (items d "refs" |> List.filter (fun r -> r["valid"] <> null && not (r["valid"].GetValue<bool>())) |> List.choose (fun r -> str r "ref") |> String.concat ", ")))
        | "claimConsistency" ->
            let ok = not (claimed = "completed" && not (buildOk && tests.Failed = 0))
            ok, (if ok then [] else [ "The report claims the unit completed, but the build or the repository tests fail." ])
        | other -> true, [ sprintf "unknown check %s" other ]
    let results = checks |> List.map (fun c -> c, result c)
    let passed = results |> List.forall (fun (_, (ok, _)) -> ok)
    jobj [ "schema", jstr "cbe.vac-002.gate/1"; "unit", jint (int64 (int a["unit"])); "attempt", jint (int64 (int a["attempt"])); "tier", jstr tier
           "head", jstr a["head"]; "verifyMs", jint (int64 a["verify-ms"]); "passed", jbool passed
           "checks", jarr (results |> List.map (fun (c, (ok, _)) -> jobj [ "check", jstr c; "description", jstr (checkNames |> Map.tryFind c |> Option.defaultValue c); "passed", jbool ok ]))
           "feedback", jarr (results |> List.collect (fun (_, (_, fb)) -> fb) |> List.map jstr)
           "repositoryTests", jobj [ "passed", jint (int64 tests.Passed); "failed", jint (int64 tests.Failed); "failedNames", jarr (tests.FailedNames |> List.map jstr) ] ]

// ---------- Adaptive policy (Arm E): observable pre-decision signals -> tier ----------
let tierRank = function "high" -> 2 | "medium" -> 1 | _ -> 0
let tierName = function 2 -> "high" | 1 -> "medium" | _ -> "low"
let policy (a: Map<string, string>) =
    let p = tryParse a["policy"] |> Option.get
    let pre = tryParse a["pre"] |> Option.get
    let post = a.TryFind "post" |> Option.bind tryParse
    let signal id = items p "signals" |> List.find (fun s -> str s "id" = Some id)
    let tierOf id = signal id |> fun s -> str s "tier" |> Option.defaultValue "low"
    let preSignals =
        [ if bool pre "contractRefused" then "S1-CONTRACT-CONFLICT", "Ordo refuses the staged contract", tierOf "S1-CONTRACT-CONFLICT"
          if i64 pre "decisionFilesStaged" > 0L then "S2-DECISION-REVISION", sprintf "%d decision record(s) staged" (i64 pre "decisionFilesStaged"), tierOf "S2-DECISION-REVISION"
          if i64 pre "externalSrcChanges" > 0L then "S3-EXTERNAL-CHANGE", sprintf "%d src file(s) changed by others since the last verification" (i64 pre "externalSrcChanges"), tierOf "S3-EXTERNAL-CHANGE"
          if bool pre "sensitive" then "S4-SENSITIVE", "money or authority terms in the requirement", tierOf "S4-SENSITIVE"
          if i64 pre "newCommands" >= 2L then "S5-NEW-PUBLIC-CONTRACT", sprintf "%d new commands" (i64 pre "newCommands"), tierOf "S5-NEW-PUBLIC-CONTRACT" ]
    let postSignals (post: JsonNode) =
        let s6 = signal "S6-CROSS-BOUNDARY"
        let s12 = signal "S12-FAN-OUT"
        let tiers = i64 post "tiersTouched"
        [ if tiers >= i64 s6["thresholds"] "high" then "S6-CROSS-BOUNDARY", sprintf "%d tiers touched" tiers, "high"
          elif tiers >= i64 s6["thresholds"] "medium" then "S6-CROSS-BOUNDARY", sprintf "%d tiers touched" tiers, "medium"
          if bool post "buildSurfaceChanged" then "S7-BUILD-SURFACE", "project, SDK or vendored file changed", tierOf "S7-BUILD-SURFACE"
          if bool post "assumptions" then "S8-UNVERIFIED-ASSUMPTION", "assumptions, open questions or known issues in the report", tierOf "S8-UNVERIFIED-ASSUMPTION"
          if bool post "blocked" then "S9-BLOCKED", "the agent stopped blocked", tierOf "S9-BLOCKED"
          if bool post "previousUnresolved" then "S10-UNRESOLVED-DEFECT", "the previous gate ended with a failing check", tierOf "S10-UNRESOLVED-DEFECT"
          if bool post "decisionRecordEdited" then "S11-DECISION-EDIT", "an accepted decision record was edited", tierOf "S11-DECISION-EDIT"
          if i64 post "filesChanged" > i64 s12["thresholds"] "files" || i64 post "linesChanged" > i64 s12["thresholds"] "lines" then
              "S12-FAN-OUT", sprintf "%d files, %d lines" (i64 post "filesChanged") (i64 post "linesChanged"), tierOf "S12-FAN-OUT" ]
    let signals = preSignals @ (post |> Option.map postSignals |> Option.defaultValue [])
    let tier = signals |> List.map (fun (_, _, t) -> tierRank t) |> List.fold max 0 |> tierName
    jobj [ "schema", jstr "cbe.vac-002.policy-decision/1"; "policyVersion", (str p "version" |> Option.map jstr |> Option.defaultValue jnull)
           "tier", jstr tier; "signals", jarr (signals |> List.map (fun (id, why, t) -> jobj [ "id", jstr id; "reason", jstr why; "tier", jstr t ]))
           "inputs", jobj [ "pre", pre.DeepClone(); "post", (match post with Some p -> p.DeepClone() | None -> jnull) ] ]

// ---------- Verified state (Arms D, F; E at high tier). Derived only from gate checks (R-ORDO-1). ----------
let state (a: Map<string, string>) =
    let gateObs = tryParse a["gate"] |> Option.get
    let previous = tryParse a["previous"]
    let report = tryParse a["report"]
    let ev = tryParse a["evidence"]
    let unit = int64 (int a["unit"])
    let task = a["task"]
    let prevList k = previous |> Option.map (fun p -> items p k |> List.map (fun n -> n.DeepClone())) |> Option.defaultValue []
    let failingTests = strings gateObs["repositoryTests"] "failedNames"
    let gatePassed = bool gateObs "passed"
    let testsRan = i64 gateObs["repositoryTests"] "passed" + i64 gateObs["repositoryTests"] "failed" > 0L
    let visibleIds = a["visible-ids"].Split(',', StringSplitOptions.RemoveEmptyEntries) |> Set.ofArray
    let covered (rid: string) = visibleIds.Contains rid
    let failingIds = failingTests |> List.collect (fun n -> Regex.Matches(n, @"LEND-L\d+-R\d+") |> Seq.map (fun m -> m.Value) |> Seq.toList) |> Set.ofList
    let reqStatus (rid: string) =
        if failingIds.Contains rid then "rejected"
        elif gatePassed && testsRan && covered rid then "verified"
        else "provisional"
    let reqIds = report |> Option.map (fun r -> items r "requirements" |> List.choose (fun q -> str q "id")) |> Option.defaultValue []
    let newReqs = reqIds |> List.map (fun id -> jobj [ "id", jstr id; "unit", jint unit; "status", jstr (reqStatus id); "coveredBy", jstr (if covered id then "visible acceptance test" else "no independent check") ])
    let carried =
        prevList "requirements"
        |> List.map (fun r ->
            let id = str r "id" |> Option.defaultValue ""
            if failingIds.Contains id && str r "status" = Some "verified" then
                (r :?> JsonObject)["status"] <- jstr "rejected"; (r :?> JsonObject)["demotedAtUnit"] <- jint unit; r
            else r)
    let classify (d: JsonNode) =
        let l1 = str d "layer1" |> Option.defaultValue "no-evidence"
        let rids = strings d "requirementIds"
        match l1 with
        | "invalid-evidence" -> "rejected"
        | "evidence-valid" when gatePassed && not (List.isEmpty rids) && rids |> List.forall (fun r -> covered r && not (failingIds.Contains r)) -> "verified"
        | _ -> "provisional"
    let entry (d: JsonNode) cls =
        jobj [ "id", (str d "id" |> Option.map jstr |> Option.defaultValue jnull); "statement", (str d "statement" |> Option.map jstr |> Option.defaultValue jnull)
               "unit", jint unit; "task", jstr task; "status", jstr cls; "basis", (str d "basis" |> Option.map jstr |> Option.defaultValue jnull)
               "requirementIds", jarr (strings d "requirementIds" |> List.map jstr) ]
    let decisions = ev |> Option.map (fun e -> items e "decisions") |> Option.defaultValue [] |> List.map (fun d -> classify d, entry d (classify d))
    let pick cls = decisions |> List.filter (fun (c, _) -> c = cls) |> List.map snd
    let external = readText a["external"] |> fun t -> t.Split('\n', StringSplitOptions.RemoveEmptyEntries) |> Array.toList
    jobj [ "schema", jstr "vac.verified-state/2"; "updatedAfterUnit", jint unit
           "verifier", jstr "VAC-002 host gate (build, repository tests, archcheck, Ordo contract, report evidence); the hidden evaluation oracle is never used"
           "head", jstr (str gateObs "head" |> Option.defaultValue "")
           "promotionRule", jstr "a requirement is verified only when the gate passed and a repository acceptance test named with its id passed; a decision is verified only when its evidence exists and every requirement it serves is so verified; invalid evidence is rejected; everything else is provisional"
           "requirements", jarr (carried @ newReqs)
           "verified", jarr (prevList "verified" @ pick "verified")
           "provisional", jarr (prevList "provisional" @ pick "provisional")
           "rejected", jarr (prevList "rejected" @ pick "rejected")
           "externalChanges", jarr (prevList "externalChanges" @ (external |> List.map (fun l -> jobj [ "unit", jint unit; "change", jstr l ])))
           "lastUnit", jobj [ "unit", jint unit; "task", jstr task; "gatePassed", jbool gatePassed; "failingChecks", (match gateObs["feedback"] with null -> jarr [] | f -> f.DeepClone()) ] ]

// ---------- K1 stream: final per-turn usage and cost from the CLI's result events ----------
let stream (a: Map<string, string>) =
    let lines = readText a["stream"] |> fun t -> t.Split('\n', StringSplitOptions.RemoveEmptyEntries) |> Array.toList |> List.choose (fun l -> try Some(JsonNode.Parse l) with _ -> None)
    let results = lines |> List.filter (fun o -> str o "type" = Some "result")
    let r = results |> List.tryLast
    let modelUsage = r |> Option.bind (fun r -> match r["modelUsage"] with :? JsonObject as m -> Some m | _ -> None)
    let models =
        modelUsage |> Option.map (fun m -> m |> Seq.map (fun kv ->
            kv.Key, jobj [ "input", jint (i64 kv.Value "inputTokens"); "output", jint (i64 kv.Value "outputTokens"); "cacheRead", jint (i64 kv.Value "cacheReadInputTokens")
                           "cacheWrite", jint (i64 kv.Value "cacheCreationInputTokens"); "costUsd", (match kv.Value["costUSD"] with null -> jnull | v -> jdec (v.GetValue<decimal>())) ]) |> Seq.toList)
        |> Option.defaultValue []
    let usage = r |> Option.map (fun r -> r["usage"])
    let compactions = lines |> List.filter (fun o -> str o "subtype" = Some "compact_boundary") |> List.length
    // X4 (VAC-002 list): tool inputs naming the sealed store, harness state, the experiment repository, the fault
    // catalogue or another arm's workspace.
    let toolInputs =
        lines
        |> List.filter (fun o -> str o "type" = Some "assistant")
        |> List.collect (fun o -> match o["message"] with null -> [] | m -> items m "content" |> List.filter (fun c -> str c "type" = Some "tool_use"))
        |> List.map (fun c -> match c["input"] with null -> "" | i -> i.ToJsonString())
    let own = a.TryFind "workspace" |> Option.defaultValue "\u0000"
    let forbidden = [ ".vac2-sealed"; ".vac2-state"; ".vac2-key"; "/sealed/"; "cohort-based-engineering"; "/oracle"; "OracleTests"; "task.json"; "faults.json"; "tasks-meta.json"; "propagation-map" ]
    let otherArm (s: string) = Regex.Matches(s, @"/home/user/vac-work/[\w.-]+/[\w.-]+") |> Seq.exists (fun m -> not (own.StartsWith m.Value))
    let hits = toolInputs |> List.filter (fun s -> forbidden |> List.exists s.Contains || otherArm s)
    jobj [ "schema", jstr "cbe.vac-002.turn-usage/1"; "stream", jstr a["stream"]
           "resultEvents", jint (int64 results.Length)
           "sessionId", (r |> Option.bind (fun r -> str r "session_id") |> Option.map jstr |> Option.defaultValue jnull)
           "isError", jbool (r |> Option.map (fun r -> bool r "is_error") |> Option.defaultValue true)
           "terminalReason", (r |> Option.bind (fun r -> str r "terminal_reason") |> Option.map jstr |> Option.defaultValue jnull)
           "numTurns", jint (r |> Option.map (fun r -> i64 r "num_turns") |> Option.defaultValue 0L)
           "durationMs", jint (r |> Option.map (fun r -> i64 r "duration_ms") |> Option.defaultValue 0L)
           "durationApiMs", jint (r |> Option.map (fun r -> i64 r "duration_api_ms") |> Option.defaultValue 0L)
           "costUsdCli", (match r |> Option.map (fun r -> r["total_cost_usd"]) with Some v when not (isNull v) -> jdec (v.GetValue<decimal>()) | _ -> jnull)
           "costBasis", jstr "CLI-reported list-price estimate (total_cost_usd); not provider-billed"
           "usage", (match usage with Some u when not (isNull u) -> jobj [ "input", jint (i64 u "input_tokens"); "output", jint (i64 u "output_tokens"); "cacheRead", jint (i64 u "cache_read_input_tokens"); "cacheWrite", jint (i64 u "cache_creation_input_tokens") ] | _ -> jnull)
           "models", jobj models
           "compactBoundaries", jint (int64 compactions)
           "contaminationHits", jarr (hits |> List.truncate 20 |> List.map (fun s -> jstr (if s.Length > 300 then s.Substring(0, 300) else s)))
           "toolUses", jint (lines |> List.filter (fun o -> str o "type" = Some "assistant") |> List.sumBy (fun o -> match o["message"] with null -> 0L | m -> items m "content" |> List.filter (fun c -> str c "type" = Some "tool_use") |> List.length |> int64))
           "finalMessage", (r |> Option.bind (fun r -> str r "result") |> Option.map (fun s -> jstr (if s.Length > 2000 then s.Substring(0, 2000) else s)) |> Option.defaultValue jnull) ]

// ---------- Dispatch ----------
match fsi.CommandLineArgs |> Array.toList |> List.tail with
| "render" :: rest -> printf "%s" (render (args rest))
| "repair" :: rest -> printf "%s" (renderRepair (args rest))
| "evidence" :: tree :: unit :: _ -> printfn "%s" (pretty (evidence tree (int unit)))
| "observe" :: rest -> printfn "%s" (pretty (observe (args rest)))
| "gate" :: rest -> printfn "%s" (pretty (gate (args rest)))
| "policy" :: rest -> printfn "%s" (pretty (policy (args rest)))
| "state" :: rest -> printfn "%s" (pretty (state (args rest)))
| "stream" :: rest -> printfn "%s" (pretty (stream (args rest)))
| _ -> eprintfn "usage: vac2.fsx render|repair|evidence|observe|gate|policy|state|stream ..."; exit 2
