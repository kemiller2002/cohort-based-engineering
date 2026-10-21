// VAC-001 harness functions (F#, pure where possible; I/O at the edges).
//   dotnet fsi --quiet --exec vac.fsx archcheck TREE [--json]
//   dotnet fsi --quiet --exec vac.fsx evidence TREE UNIT
//   dotnet fsi --quiet --exec vac.fsx observe --run R --arm A --unit N ...   (see vac.sh verify)
//   dotnet fsi --quiet --exec vac.fsx state --observation OBS --previous PREV --report REPORT --rules RULES
//   dotnet fsi --quiet --exec vac.fsx usage --transcript T.jsonl [--from ISO] [--to ISO] [--prices TABLE]
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes
open System.Text.RegularExpressions
open System.Xml.Linq

// ---------- JSON helpers ----------
let jstr (s: string) = JsonValue.Create(s) :> JsonNode
let jint (i: int64) = JsonValue.Create(i) :> JsonNode
let jdec (d: decimal) = JsonValue.Create(d) :> JsonNode
let jbool (b: bool) = JsonValue.Create(b) :> JsonNode
let jnull : JsonNode = null
let jarr (xs: JsonNode seq) = JsonArray(Seq.toArray xs) :> JsonNode
let jobj (kvs: (string * JsonNode) list) =
    let o = JsonObject()
    kvs |> List.iter (fun (k, v) -> o[k] <- v)
    o :> JsonNode
let pretty (n: JsonNode) = n.ToJsonString(JsonSerializerOptions(WriteIndented = true))
let tryParse (path: string) =
    try if File.Exists path then Some(JsonNode.Parse(File.ReadAllText path)) else None with _ -> None
let str (n: JsonNode) (k: string) =
    match n with
    | null -> None
    | _ -> match n[k] with null -> None | v -> (try Some(v.GetValue<string>()) with _ -> Some(v.ToJsonString()))
let items (n: JsonNode) (k: string) : JsonNode list =
    match n with
    | null -> []
    | _ -> match n[k] with :? JsonArray as a -> a |> Seq.toList | _ -> []
let i64 (n: JsonNode) (k: string) =
    match n with null -> 0L | _ -> match n[k] with null -> 0L | v -> (try v.GetValue<int64>() with _ -> 0L)

// ---------- Architecture rules (VAC-RULES 1.0.0, docs/architecture/RULES.md) ----------
type Violation = { Rule: string; File: string; Line: int; Text: string }

let rulesVersion = "VAC-RULES 1.0.0"
let pins =
    {| Sdk = "10.0.100"; RollForward = "latestFeature"; Tfm = "net10.0"
       Packages = [ "Microsoft.NET.Test.Sdk", "17.11.1"; "xunit", "2.9.2"; "xunit.runner.visualstudio", "2.8.2" ] |}

/// Remove comments and string literals so rules match code only. Line structure is preserved.
let stripCode (src: string) =
    let noBlock = Regex.Replace(src, @"\(\*[\s\S]*?\*\)", fun m -> String(m.Value |> Seq.filter ((=) '\n') |> Seq.toArray))
    let noTriple = Regex.Replace(noBlock, "\"\"\"[\\s\\S]*?\"\"\"", fun m -> String(m.Value |> Seq.filter ((=) '\n') |> Seq.toArray))
    let noStrings = Regex.Replace(noTriple, "\"(?:\\\\.|[^\"\\\\\\n])*\"", "\"\"")
    Regex.Replace(noStrings, @"//[^\n]*", "")

let effectPatterns =
    [ @"\bSystem\.IO\b"; @"\bConsole\b"; @"\bprintfn?\b"; @"\beprintfn?\b"; @"\bDateTime\.(Now|UtcNow|Today)\b"
      @"\bDateOnly\.FromDateTime\b"; @"\bStopwatch\b"; @"\bRandom\b"; @"\bGuid\.NewGuid\b"; @"\bEnvironment\."
      @"\bThread\b"; @"\bTask\b"; @"\basync\b"; @"\bmutable\b"; @"\bref\b"; @"<-" ]
let throwPatterns = [ @"\bfailwithf?\b"; @"\braise\b"; @"\binvalidArg\b"; @"\binvalidOp\b"; @"\bexn\b" ]

let scan rule (patterns: string list) (file: string) (code: string) =
    code.Split('\n')
    |> Array.mapi (fun i line -> i + 1, line)
    |> Array.collect (fun (n, line) ->
        patterns
        |> List.filter (fun p -> Regex.IsMatch(line, p))
        |> List.map (fun _ -> { Rule = rule; File = file; Line = n; Text = line.Trim() })
        |> List.truncate 1 |> List.toArray)
    |> Array.toList

let archcheck (tree: string) : Violation list =
    let src = Path.Combine(tree, "src", "Ledger")
    let rel (p: string) = Path.GetRelativePath(tree, p).Replace('\\', '/')
    let fsproj = Path.Combine(src, "Ledger.fsproj")
    let compileOrder =
        if File.Exists fsproj then
            XDocument.Load(fsproj).Descendants(XName.Get "Compile")
            |> Seq.map (fun e -> e.Attribute(XName.Get "Include").Value) |> Seq.toList
        else []
    let ar1 =
        match compileOrder with
        | [] -> [ { Rule = "AR-1"; File = rel fsproj; Line = 0; Text = "no Compile items" } ]
        | first :: _ when first <> "Domain.fs" -> [ { Rule = "AR-1"; File = rel fsproj; Line = 0; Text = sprintf "first compiled file is %s" first } ]
        | xs when List.last xs <> "Store.fs" -> [ { Rule = "AR-1"; File = rel fsproj; Line = 0; Text = sprintf "last compiled file is %s" (List.last xs) } ]
        | _ -> []
    let sources =
        if Directory.Exists src then Directory.GetFiles(src, "*.fs") |> Array.sort |> Array.toList else []
    let tier12 = sources |> List.filter (fun f -> Path.GetFileName f <> "Store.fs")
    let code f = stripCode (File.ReadAllText f)
    let ar2 = tier12 |> List.collect (fun f -> scan "AR-2" effectPatterns (rel f) (code f))
    let ar3 = tier12 |> List.collect (fun f -> scan "AR-3" throwPatterns (rel f) (code f))
    let domain = Path.Combine(src, "Domain.fs")
    let ar4 =
        if File.Exists domain then
            let m = Regex.Match(code domain, @"type\s+LedgerState\s*=\s*\{([^}]*)\}")
            if not m.Success then [ { Rule = "AR-4"; File = rel domain; Line = 0; Text = "LedgerState record not found" } ]
            else
                Regex.Matches(m.Groups[1].Value, @"(\w+)\s*:") |> Seq.map (fun g -> g.Groups[1].Value)
                |> Seq.filter (fun name -> name.Contains "Balance")
                |> Seq.map (fun name -> { Rule = "AR-4"; File = rel domain; Line = 0; Text = sprintf "LedgerState field %s" name })
                |> Seq.toList
        else [ { Rule = "AR-4"; File = "src/Ledger/Domain.fs"; Line = 0; Text = "missing" } ]
    let ar5 =
        (if File.Exists domain then scan "AR-5" [ @"\bLedger\.[a-z]\w*"; @"\bStore\b" ] (rel domain) (code domain) else [])
        @ (tier12 |> List.filter (fun f -> f <> domain) |> List.collect (fun f -> scan "AR-5" [ @"\bStore\b" ] (rel f) (code f)))
    let fileText p = let path = Path.Combine(tree, p) in if File.Exists path then File.ReadAllText path else ""
    let globalJson = fileText "global.json"
    let props = fileText "Directory.Build.props"
    let projects = Directory.GetFiles(tree, "*.fsproj", SearchOption.AllDirectories) |> Array.toList
    let ar6 =
        [ if not (globalJson.Contains(sprintf "\"%s\"" pins.Sdk) && globalJson.Contains(sprintf "\"%s\"" pins.RollForward)) then
              yield { Rule = "AR-6"; File = "global.json"; Line = 0; Text = "SDK pin changed" }
          if not (props.Contains(sprintf "<TargetFramework>%s</TargetFramework>" pins.Tfm)) then
              yield { Rule = "AR-6"; File = "Directory.Build.props"; Line = 0; Text = "TargetFramework changed" }
          for p in projects do
              let t = File.ReadAllText p
              if Regex.IsMatch(t, "<TargetFrameworks?>") then
                  yield { Rule = "AR-6"; File = rel p; Line = 0; Text = "project overrides TargetFramework" }
              for m in Regex.Matches(t, "<PackageReference\\s+Include=\"([^\"]+)\"\\s+Version=\"([^\"]+)\"") do
                  let name, ver = m.Groups[1].Value, m.Groups[2].Value
                  match pins.Packages |> List.tryFind (fun (n, _) -> n = name) with
                  | Some(_, v) when v = ver -> ()
                  | Some(_, v) -> yield { Rule = "AR-6"; File = rel p; Line = 0; Text = sprintf "%s %s (pinned %s)" name ver v }
                  | None -> yield { Rule = "AR-6"; File = rel p; Line = 0; Text = sprintf "new package %s %s" name ver } ]
    ar1 @ ar2 @ ar3 @ ar4 @ ar5 @ ar6

let violationsJson (vs: Violation list) =
    jobj [ "schema", jstr "cbe.vac-001.archcheck/1"; "rules", jstr rulesVersion; "passed", jbool (List.isEmpty vs)
           "violations", jarr (vs |> List.map (fun v -> jobj [ "rule", jstr v.Rule; "file", jstr v.File; "line", jint (int64 v.Line); "text", jstr v.Text ])) ]

// ---------- Layer 1: deterministic evidence validation of a unit report ----------
type RefCheck = { Ref: string; Kind: string; Valid: bool option; Why: string }

let checkRef (tree: string) (knownIds: Set<string>) (r: string) : RefCheck =
    let exists p = File.Exists(Path.Combine(tree, p)) || Directory.Exists(Path.Combine(tree, p))
    let read p = let f = Path.Combine(tree, p) in if File.Exists f then File.ReadAllText f else ""
    let r' = r.Trim().Trim('`')
    // files the brief provides outside the repository (amendment A3)
    let briefProvided = [ "DIRECTIVES.md"; "env.sh" ]
    match r' with
    | _ when briefProvided |> List.exists (fun f -> r'.Split('#').[0].Trim() = f || r'.Split('#').[0].Trim().EndsWith("/" + f)) ->
        { Ref = r; Kind = "brief-provided"; Valid = Some true; Why = "" }
    | _ when Regex.IsMatch(r', @"^[0-9a-f]{7,40}$") -> { Ref = r; Kind = "commit"; Valid = None; Why = "commit refs are not checked from an exported tree" }
    | _ when Regex.IsMatch(r', @"^(DEC|U\d+-D|CONFLICT|VERIFY|LEDGER)-?[\w-]*$") && not (r'.Contains "/") ->
        { Ref = r; Kind = "record"; Valid = Some(knownIds.Contains r'); Why = if knownIds.Contains r' then "" else "identifier not found in requirements, contracts, decisions or reports" }
    | _ ->
        let path, anchor = match r'.Split('#', 2) with [| p; a |] -> p.Trim(), Some(a.Trim()) | a -> a[0].Trim(), None
        let path = Regex.Replace(path, @":\d+(-\d+)?$", "")
        if not (exists path) then { Ref = r; Kind = "file"; Valid = Some false; Why = "path does not exist" }
        else
            match anchor with
            | None -> { Ref = r; Kind = "file"; Valid = Some true; Why = "" }
            | Some a ->
                let symbol = Regex.Replace(a, @"^(L\d+.*|R\d+)$", "")
                let ok = symbol = "" || (read path).Contains(symbol.Split([| ' '; '('; ':' |], StringSplitOptions.RemoveEmptyEntries) |> Array.tryHead |> Option.defaultValue symbol)
                { Ref = r; Kind = "symbol"; Valid = Some ok; Why = if ok then "" else "anchor text not found in file" }

let knownIdsIn (tree: string) =
    let files =
        [ "requirements"; "contracts"; "docs"; ".vac/reports" ]
        |> List.map (fun d -> Path.Combine(tree, d))
        |> List.filter Directory.Exists
        |> List.collect (fun d -> Directory.GetFiles(d, "*", SearchOption.AllDirectories) |> Array.toList)
    files
    |> List.collect (fun f -> Regex.Matches(File.ReadAllText f, @"\b(?:DEC|CONFLICT|VERIFY|LEDGER)-[\w-]+|\bU\d+-D\d+\b") |> Seq.map (fun m -> m.Value.TrimEnd('-')) |> Seq.toList)
    |> Set.ofList

let evidence (tree: string) (unit: int) =
    let path = Path.Combine(tree, ".vac", "reports", sprintf "unit-%d.json" unit)
    match tryParse path with
    | None ->
        jobj [ "schema", jstr "cbe.vac-001.evidence/1"; "unit", jint (int64 unit); "reportPresent", jbool (File.Exists path); "reportParses", jbool false; "decisions", jarr [] ]
    | Some report ->
        let known = knownIdsIn tree
        let decisions =
            items report "decisions"
            |> List.map (fun d ->
                let refs = items d "evidence" |> List.choose (fun e -> try Some(e.GetValue<string>()) with _ -> None)
                let checks = refs |> List.map (checkRef tree known)
                let reqs = items d "requirementIds" |> List.choose (fun e -> try Some(e.GetValue<string>()) with _ -> None)
                let badReqs = reqs |> List.filter (fun r -> not (known.Contains r) && not (known |> Set.exists (fun k -> k.StartsWith r)))
                let basis = str d "basis" |> Option.defaultValue "unstated"
                let invalid = checks |> List.filter (fun c -> c.Valid = Some false)
                let supported =
                    match basis with
                    | "assumption" -> "recorded-assumption"
                    | _ when List.isEmpty refs -> "no-evidence"
                    | _ when not (List.isEmpty invalid) || not (List.isEmpty badReqs) -> "invalid-evidence"
                    | _ -> "evidence-valid"
                jobj [ "id", (str d "id" |> Option.map jstr |> Option.defaultValue jnull)
                       "statement", (str d "statement" |> Option.map jstr |> Option.defaultValue jnull)
                       "basis", jstr basis; "layer1", jstr supported
                       "refs", jarr (checks |> List.map (fun c -> jobj [ "ref", jstr c.Ref; "kind", jstr c.Kind; "valid", (match c.Valid with Some b -> jbool b | None -> jnull); "why", jstr c.Why ]))
                       "unknownRequirementIds", jarr (badReqs |> List.map jstr) ])
        jobj [ "schema", jstr "cbe.vac-001.evidence/1"; "unit", jint (int64 unit); "reportPresent", jbool true; "reportParses", jbool true
               "outcome", (str report "outcome" |> Option.map jstr |> Option.defaultValue jnull)
               "decisions", jarr decisions ]

// ---------- Observation: one independent verification of one unit ----------
type OracleCase = { Name: string; Task: string; Requirement: string; Outcome: string }

let oracleCases (dir: string) =
    let trx = if Directory.Exists dir then Directory.GetFiles(dir, "*.trx", SearchOption.AllDirectories) |> Array.toList else []
    trx |> List.collect (fun f ->
        XDocument.Load(f).Descendants()
        |> Seq.filter (fun e -> e.Name.LocalName = "UnitTestResult")
        |> Seq.map (fun e ->
            let name = e.Attribute(XName.Get "testName").Value
            let task = Regex.Match(name, @"Oracle(V\d)").Groups[1].Value
            let req = Regex.Match(name, @"LEDGER-V\d-R\d").Value
            { Name = name; Task = task; Requirement = req; Outcome = e.Attribute(XName.Get "outcome").Value })
        |> Seq.toList)

let testSummary (log: string) =
    let text = if File.Exists log then File.ReadAllText log else ""
    let m = Regex.Matches(text, @"(Passed|Failed)!\s+-\s+Failed:\s+(\d+),\s+Passed:\s+(\d+)")
    let errors = Regex.Matches(text, @" error FS\d+").Count
    let failed = m |> Seq.sumBy (fun x -> int x.Groups[2].Value)
    let passed = m |> Seq.sumBy (fun x -> int x.Groups[3].Value)
    {| Built = m.Count > 0; Passed = passed; Failed = failed; CompilerErrors = errors |}

let args (argv: string list) =
    let rec go acc = function
        | (k: string) :: v :: rest when k.StartsWith "--" -> go (Map.add (k.TrimStart('-')) v acc) rest
        | _ :: rest -> go acc rest
        | [] -> acc
    go Map.empty argv

let observe (a: Map<string, string>) =
    let unit = int a["unit"]
    let setup = tryParse a["setup"] |> Option.get
    let units = items setup "units"
    let thisUnit = units |> List.find (fun u -> i64 u "unit" = int64 unit)
    let task = str thisUnit "task" |> Option.get
    let fault = str thisUnit "fault" |> Option.defaultValue "none"
    let staged = units |> List.filter (fun u -> i64 u "unit" <= int64 unit) |> List.choose (fun u -> str u "task")
    let tests = testSummary a["tests-log"]
    let cases = oracleCases a["oracle-dir"]
    let oracleLogs = if Directory.Exists a["oracle-dir"] then Directory.GetFiles(a["oracle-dir"], "*.log") |> Array.toList else []
    let compileErrorsOf t = oracleLogs |> List.filter (fun f -> Path.GetFileNameWithoutExtension f = t) |> List.sumBy (fun f -> (testSummary f).CompilerErrors)
    let oracleLog = {| CompilerErrors = oracleLogs |> List.sumBy (fun f -> (testSummary f).CompilerErrors) |}
    let arch = tryParse a["arch"]
    let archPassed = arch |> Option.map (fun j -> j["passed"].GetValue<bool>()) |> Option.defaultValue false
    let ev = tryParse a["evidence"]
    let report = tryParse a["report"]
    let claimed = report |> Option.bind (fun r -> str r "outcome") |> Option.defaultValue "no-report"
    let blockedReason = report |> Option.bind (fun r -> str r "blockedReason") |> Option.defaultValue ""
    let taskJson = tryParse (Path.Combine(a["fixture"], "tasks", task, "task.json")) |> Option.get
    let expectedCompletion = taskJson["expectedOutcome"].["completion"].GetValue<string>()
    let byTask t = cases |> List.filter (fun c -> c.Task = t)
    let taskPass t = let cs = byTask t in not (List.isEmpty cs) && cs |> List.forall (fun c -> c.Outcome = "Passed")
    let oracleBuilt = not (List.isEmpty cases)
    let dirty = int a["dirty"]
    let buildOk = tests.Built && tests.CompilerErrors = 0
    let visibleOk = buildOk && tests.Failed = 0
    // V7: the correct outcome is a stop that names both conflicting decisions; no oracle applies.
    let conflictNamed = blockedReason.Contains "DEC-V7-EMPTY-NOOP" && blockedReason.Contains "DEC-V7-ONE-PAIR"
    let accepted =
        if expectedCompletion = "none" then claimed = "blocked" && (conflictNamed || blockedReason.Contains "CONFLICT" || blockedReason.ToLowerInvariant().Contains "conflict")
        else visibleOk && oracleBuilt && taskPass task && archPassed && dirty = 0
    // Earlier tasks whose oracle fails now. Whether that is a regression (the task was accepted at its own unit)
    // is decided by the analysis from the observation sequence, not here.
    let regressions = staged |> List.filter (fun t -> t <> task && t <> "V7") |> List.distinct |> List.filter (fun t -> not (taskPass t))
    let falseCompletion = claimed = "completed" && not accepted
    let failingCases = cases |> List.filter (fun c -> c.Outcome <> "Passed")
    jobj [ "schema", jstr "cbe.vac-001.observation/1"; "run", jstr a["run"]; "arm", jstr a["arm"]; "unit", jint (int64 unit)
           "attempt", jint (int64 (int a["attempt"])); "task", jstr task; "fault", jstr fault; "head", jstr a["head"]
           "verifiedAt", jstr (DateTime.UtcNow.ToString("o")); "verifyMs", jint (int64 a["verify-ms"])
           "stagedTasks", jarr (staged |> List.map jstr); "uncommittedPaths", jint (int64 dirty)
           "build", jobj [ "ok", jbool buildOk; "compilerErrors", jint (int64 tests.CompilerErrors) ]
           "visibleTests", jobj [ "passed", jint (int64 tests.Passed); "failed", jint (int64 tests.Failed); "exit", jint (int64 (int a["tests-rc"])) ]
           "oracle", jobj [ "built", jbool oracleBuilt; "exit", jint (int64 (int a["oracle-rc"])); "compilerErrors", jint (int64 oracleLog.CompilerErrors)
                            "cases", jint (int64 cases.Length); "failed", jint (int64 failingCases.Length)
                            "byTask", jobj (staged |> List.distinct |> List.filter ((<>) "V7") |> List.map (fun t ->
                                t, jobj [ "cases", jint (int64 (byTask t).Length); "failed", jint (int64 (byTask t |> List.filter (fun c -> c.Outcome <> "Passed")).Length); "compilerErrors", jint (int64 (compileErrorsOf t)) ]))
                            "failing", jarr (failingCases |> List.map (fun c -> jobj [ "test", jstr c.Name; "task", jstr c.Task; "requirement", jstr c.Requirement ])) ]
           "architecture", (match arch with Some j -> j.DeepClone() | None -> jnull)
           "evidence", (match ev with Some j -> j.DeepClone() | None -> jnull)
           "claim", jobj [ "outcome", jstr claimed; "blockedReason", jstr blockedReason ]
           "verdict", jobj [ "expectedCompletion", jstr expectedCompletion; "accepted", jbool accepted; "falseCompletion", jbool falseCompletion
                             "earlierTasksFailing", jarr (regressions |> List.map jstr)
                             "buildBroken", jbool (not buildOk) ] ]

// ---------- Arm D: verified state (Verified / Provisional / Rejected) ----------
let state (a: Map<string, string>) =
    let obs = tryParse a["observation"] |> Option.get
    let previous = tryParse a["previous"]
    let report = tryParse a["report"]
    let prevList k = previous |> Option.map (fun p -> items p k |> List.map (fun n -> n.DeepClone())) |> Option.defaultValue []
    let unit = i64 obs "unit"
    let task = str obs "task" |> Option.get
    let verdict = obs["verdict"]
    let accepted = verdict["accepted"].GetValue<bool>()
    let regressed = items verdict "earlierTasksFailing" |> List.map (fun n -> n.GetValue<string>()) |> Set.ofList
    let failingReqs = items obs["oracle"] "failing" |> List.choose (fun f -> str f "requirement") |> Set.ofList
    let evDecisions = items obs["evidence"] "decisions"
    let classify (d: JsonNode) =
        let l1 = str d "layer1" |> Option.defaultValue "no-evidence"
        match l1 with
        | "invalid-evidence" -> "rejected"
        | "evidence-valid" when accepted -> "verified"
        | _ -> "provisional"
    let decisionEntry (d: JsonNode) cls =
        jobj [ "id", (str d "id" |> Option.map jstr |> Option.defaultValue jnull); "statement", (str d "statement" |> Option.map jstr |> Option.defaultValue jnull)
               "unit", jint unit; "task", jstr task; "status", jstr cls
               "basis", (str d "basis" |> Option.map jstr |> Option.defaultValue jnull)
               "invalidRefs", jarr (items d "refs" |> List.filter (fun r -> r["valid"] <> null && not (r["valid"].GetValue<bool>())) |> List.choose (fun r -> str r "ref") |> List.map jstr) ]
    let newDecisions = evDecisions |> List.map (fun d -> classify d, decisionEntry d (classify d))
    let reqStatus =
        let reqIds = report |> Option.map (fun r -> items r "requirements" |> List.choose (fun q -> str q "id")) |> Option.defaultValue []
        reqIds |> List.map (fun id ->
            let s = if accepted && not (failingReqs.Contains id) then "verified" elif failingReqs.Contains id then "rejected" else "provisional"
            jobj [ "id", jstr id; "unit", jint unit; "status", jstr s ])
    // An earlier verified requirement whose oracle now fails is demoted, never silently kept.
    let carried =
        prevList "requirements"
        |> List.map (fun r ->
            let id = str r "id" |> Option.defaultValue ""
            let t = Regex.Match(id, @"LEDGER-(V\d)").Groups[1].Value
            if regressed.Contains t && str r "status" = Some "verified" then
                (r :?> JsonObject)["status"] <- jstr "rejected"; (r :?> JsonObject)["demotedAtUnit"] <- jint unit; r
            else r)
    let pick cls = newDecisions |> List.filter (fun (c, _) -> c = cls) |> List.map snd
    let failures =
        items obs["oracle"] "failing" |> List.map (fun f -> jobj [ "requirement", (str f "requirement" |> Option.map jstr |> Option.defaultValue jnull); "check", (str f "test" |> Option.map jstr |> Option.defaultValue jnull) ])
    jobj [ "schema", jstr "vac.verified-state/1"; "updatedAfterUnit", jint unit; "verifier", jstr "VAC-001 host verifier (hidden oracle, build, tests, VAC-RULES 1.0.0)"
           "head", jstr (str obs "head" |> Option.defaultValue "")
           "promotionRule", jstr "a decision is verified only when its Layer 1 evidence is valid and its unit was independently accepted; invalid evidence is rejected; everything else stays provisional"
           "requirements", jarr (carried @ reqStatus)
           "verified", jarr (prevList "verified" @ pick "verified")
           "provisional", jarr (prevList "provisional" @ pick "provisional")
           "rejected", jarr (prevList "rejected" @ pick "rejected")
           "constraints", jarr [ jstr (sprintf "%s: docs/architecture/RULES.md" rulesVersion) ]
           "lastUnit", jobj [ "unit", jint unit; "task", jstr task; "accepted", jbool accepted; "failingChecks", jarr failures
                              "architectureViolations", (match obs["architecture"] with null -> jarr [] | a -> (a["violations"] |> Option.ofObj |> Option.map (fun v -> v.DeepClone()) |> Option.defaultValue (jarr []))) ] ]

// ---------- Usage from a Claude Code transcript (per-request, de-duplicated by message id) ----------
type Req = { Id: string; At: DateTime; Model: string; Effort: string; Input: int64; Cw5: int64; Cw1h: int64; Cr: int64; Output: int64 }

let usage (a: Map<string, string>) =
    let from = a.TryFind "from" |> Option.map DateTime.Parse |> Option.defaultValue DateTime.MinValue
    let upto = a.TryFind "to" |> Option.map DateTime.Parse |> Option.defaultValue DateTime.MaxValue
    let lines = File.ReadAllLines a["transcript"] |> Array.choose (fun l -> try Some(JsonNode.Parse l) with _ -> None) |> Array.toList
    let at (o: JsonNode) = str o "timestamp" |> Option.map (fun t -> DateTime.Parse(t).ToUniversalTime()) |> Option.defaultValue DateTime.MinValue
    let window = lines |> List.filter (fun o -> let t = at o in t >= from.ToUniversalTime() && t <= upto.ToUniversalTime())
    let reqs =
        window
        |> List.choose (fun o ->
            match o["message"] with
            | :? JsonObject as m when m["usage"] <> null && m["id"] <> null ->
                let u = m["usage"]
                let cc = u["cache_creation"]
                let cw = i64 u "cache_creation_input_tokens"
                let cw1h = if cc = null then 0L else i64 cc "ephemeral_1h_input_tokens"
                Some { Id = m["id"].GetValue<string>(); At = at o; Model = str m "model" |> Option.defaultValue "unknown"
                       Effort = str o "effort" |> Option.defaultValue "unrecorded"
                       Input = i64 u "input_tokens"; Cw5 = cw - cw1h; Cw1h = cw1h; Cr = i64 u "cache_read_input_tokens"; Output = i64 u "output_tokens" }
            | _ -> None)
        |> List.groupBy (fun r -> r.Id)
        |> List.map (fun (_, rs) -> rs |> List.maxBy (fun r -> r.Output))
        |> List.sortBy (fun r -> r.At)
    let toolUses =
        window |> List.collect (fun o ->
            match o["message"] with
            | :? JsonObject as m -> (match m["content"] with :? JsonArray as c -> c |> Seq.filter (fun b -> b <> null && str b "type" = Some "tool_use") |> Seq.choose (fun b -> str b "id") |> Seq.toList | _ -> [])
            | _ -> [])
        |> List.distinct
    let compactions = window |> List.filter (fun o -> str o "subtype" = Some "compact_boundary" || (o["isCompactSummary"] <> null && o["isCompactSummary"].GetValue<bool>()))
    // X4 contamination scan: any tool input that names the hidden oracle, harness state or another arm's workspace.
    let forbidden = [ "/oracle"; "OracleTests"; "REL-001"; "cohort-based-engineering"; ".vac-state"; "task.json"; "/reference/" ]
    let own = a.TryFind "workspace" |> Option.defaultValue "\u0000"
    let toolInputs =
        window |> List.collect (fun o ->
            match o["message"] with
            | :? JsonObject as m -> (match m["content"] with :? JsonArray as c -> c |> Seq.filter (fun b -> b <> null && str b "type" = Some "tool_use" && List.contains (str b "name" |> Option.defaultValue "") [ "Bash"; "Read"; "Grep"; "Glob"; "Edit"; "Write"; "NotebookEdit" ]) |> Seq.map (fun b -> b["input"].ToJsonString()) |> Seq.toList | _ -> [])
            | _ -> [])
    let otherArm (s: string) = Regex.Matches(s, @"/home/user/vac-work/[^/\s""]+/[^/\s""]+") |> Seq.exists (fun m -> not (own.StartsWith m.Value))
    let hits = toolInputs |> List.filter (fun s -> forbidden |> List.exists s.Contains || otherArm s)
    let sum f = reqs |> List.sumBy f
    let ctx r = r.Input + r.Cw5 + r.Cw1h + r.Cr
    let prices = a.TryFind "prices" |> Option.bind tryParse
    let cost =
        prices |> Option.map (fun p ->
            let e = items p "entries" |> List.find (fun e -> str e "model" = Some "claude-opus-5-5")
            let rate (k: string) = e[k].GetValue<decimal>() / 1_000_000m
            decimal (sum (fun r -> r.Input)) * rate "input" + decimal (sum (fun r -> r.Cw5)) * rate "cacheWrite5m"
            + decimal (sum (fun r -> r.Cw1h)) * rate "cacheWrite1h" + decimal (sum (fun r -> r.Cr)) * rate "cacheRead"
            + decimal (sum (fun r -> r.Output)) * rate "output")
    jobj [ "schema", jstr "cbe.vac-001.usage/1"; "transcript", jstr a["transcript"]
           "window", jobj [ "from", jstr (a.TryFind "from" |> Option.defaultValue ""); "to", jstr (a.TryFind "to" |> Option.defaultValue "") ]
           "requests", jint (int64 reqs.Length); "toolUses", jint (int64 toolUses.Length)
           "tokens", jobj [ "input", jint (sum (fun r -> r.Input)); "cacheWrite5m", jint (sum (fun r -> r.Cw5)); "cacheWrite1h", jint (sum (fun r -> r.Cw1h))
                            "cacheRead", jint (sum (fun r -> r.Cr)); "output", jint (sum (fun r -> r.Output))
                            "total", jint (sum (fun r -> ctx r + r.Output)) ]
           "context", jobj [ "first", jint (reqs |> List.tryHead |> Option.map ctx |> Option.defaultValue 0L)
                             "last", jint (reqs |> List.tryLast |> Option.map ctx |> Option.defaultValue 0L)
                             "peak", jint (reqs |> List.map ctx |> List.fold max 0L) ]
           "compactions", jint (int64 compactions.Length)
           "models", jarr (reqs |> List.map (fun r -> r.Model) |> List.distinct |> List.map jstr)
           "efforts", jarr (reqs |> List.map (fun r -> r.Effort) |> List.distinct |> List.map jstr)
           "costUsd", (match cost with Some c -> jdec (Math.Round(c, 6)) | None -> jnull)
           "priceTable", (prices |> Option.bind (fun p -> str p "tableVersion") |> Option.map jstr |> Option.defaultValue jnull)
           "contaminationHits", jarr (hits |> List.truncate 20 |> List.map (fun s -> jstr (if s.Length > 300 then s.Substring(0, 300) else s))) ]

// ---------- Analysis (research-protocol.md section 9) ----------
type UnitRow =
    { Unit: int; Task: string; Fault: string; Claimed: string; FirstAccepted: bool; FinalAccepted: bool; Attempts: int
      FalseFirst: bool; FalseFinal: bool; ClaimedFinal: string; EarlierFailing: string list; ArchRules: string list; BuildOk: bool
      Decisions: int; Unsupported: int; Tokens: int64[]; Cost: decimal; Requests: int64; ToolUses: int64; CtxLast: int64
      Compactions: int64; VerifyMs: int64; RepairTokens: int64; RepairCost: decimal; Models: string list; Efforts: string list; X4: int }

let loadArm (dir: string) : UnitRow list =
    let file (p: string) = tryParse (Path.Combine(dir, p))
    let setup = file "setup.json" |> Option.get
    items setup "units"
    |> List.map (fun u -> int (i64 u "unit"))
    |> List.filter (fun n -> File.Exists(Path.Combine(dir, sprintf "verify-%d-1.json" n)))
    |> List.map (fun n ->
        let attempts =
            Seq.initInfinite ((+) 1) |> Seq.takeWhile (fun t -> File.Exists(Path.Combine(dir, sprintf "verify-%d-%d.json" n t))) |> Seq.toList
        let obs t = file (sprintf "verify-%d-%d.json" n t) |> Option.get
        let usageOf t = file (sprintf "usage-%d-%d.json" n t)
        let first, last = obs 1, obs (List.last attempts)
        let b (o: JsonNode) (k: string) = o["verdict"].[k].GetValue<bool>()
        let tok (u: JsonNode) = [| "input"; "cacheWrite5m"; "cacheWrite1h"; "cacheRead"; "output"; "total" |] |> Array.map (fun k -> i64 u["tokens"] k)
        let usages = attempts |> List.choose usageOf
        let sumTok us = us |> List.map tok |> List.fold (Array.map2 (+)) (Array.zeroCreate 6)
        let costOf (u: JsonNode) = match u["costUsd"] with null -> 0m | v -> v.GetValue<decimal>()
        let decisions = items last["evidence"] "decisions"
        let unsupported = decisions |> List.filter (fun d -> str d "layer1" = Some "invalid-evidence" || str d "layer1" = Some "no-evidence") |> List.length
        let strs (n: JsonNode) k = items n k |> List.map (fun x -> x.GetValue<string>())
        { Unit = n; Task = str first "task" |> Option.get; Fault = str first "fault" |> Option.defaultValue "none"
          Claimed = first["claim"].["outcome"].GetValue<string>(); ClaimedFinal = last["claim"].["outcome"].GetValue<string>()
          FirstAccepted = b first "accepted"; FinalAccepted = b last "accepted"; Attempts = attempts.Length
          FalseFirst = b first "falseCompletion"; FalseFinal = b last "falseCompletion"
          EarlierFailing = strs last["verdict"] "earlierTasksFailing"
          ArchRules = (match last["architecture"] with null -> [] | a -> items a "violations" |> List.choose (fun v -> str v "rule") |> List.distinct)
          BuildOk = last["build"].["ok"].GetValue<bool>()
          Decisions = decisions.Length; Unsupported = unsupported
          Tokens = sumTok usages; Cost = usages |> List.sumBy costOf
          Requests = usages |> List.sumBy (fun u -> i64 u "requests"); ToolUses = usages |> List.sumBy (fun u -> i64 u "toolUses")
          CtxLast = (match List.tryLast usages with Some u -> i64 u["context"] "last" | None -> 0L)
          Compactions = usages |> List.sumBy (fun u -> i64 u "compactions")
          VerifyMs = attempts |> List.sumBy (fun t -> i64 (obs t) "verifyMs")
          RepairTokens = (usages |> List.skip (min 1 usages.Length) |> sumTok).[5]
          RepairCost = usages |> List.skip (min 1 usages.Length) |> List.sumBy costOf
          Models = usages |> List.collect (fun u -> strs u "models") |> List.distinct
          Efforts = usages |> List.collect (fun u -> strs u "efforts") |> List.distinct
          X4 = usages |> List.sumBy (fun u -> (items u "contaminationHits").Length) })

let ratio (num: int) (den: int) =
    jobj [ "numerator", jint (int64 num); "denominator", jint (int64 den); "value", (if den = 0 then jnull else jdec (Math.Round(decimal num / decimal den, 4))) ]

let decisionIdsOf (fixture: string) (task: string) =
    tryParse (Path.Combine(fixture, "tasks", task, "task.json")) |> Option.map (fun t -> items t "decisionIds" |> List.map (fun d -> d.GetValue<string>())) |> Option.defaultValue []

/// Per-unit derived facts that need the sequence: regressions vs carried defects, critical failures, decision drift.
let derive (fixture: string) (rows: UnitRow list) =
    rows |> List.map (fun r ->
        let acceptedBefore = rows |> List.filter (fun p -> p.Unit < r.Unit && p.FinalAccepted && p.Task <> "V7") |> List.map (fun p -> p.Task) |> Set.ofList
        let regressed = r.EarlierFailing |> List.filter acceptedBefore.Contains
        let carried = r.EarlierFailing |> List.filter (acceptedBefore.Contains >> not)
        let buildBroken = not r.BuildOk && r.Task <> "V7"
        let critical = r.FalseFirst || not (List.isEmpty regressed) || buildBroken
        // DDR: established decisions = DEC-BASE-REFUSALS-AS-DATA (AR-3), DEC-BASE-DERIVED-BALANCES (AR-4), plus the
        // decisions of every task accepted at an earlier unit. A reversal = the rule violated / that task's oracle failing.
        let established = 2 + (acceptedBefore |> Set.toList |> List.sumBy (fun t -> max 1 (decisionIdsOf fixture t).Length))
        let reversals =
            (r.ArchRules |> List.filter (fun x -> x = "AR-3" || x = "AR-4") |> List.length)
            + (regressed |> List.sumBy (fun t -> max 1 (decisionIdsOf fixture t).Length))
        r, regressed, carried, critical, established, reversals)

let armMetrics (fixture: string) (run: string) (arm: string) (rows: UnitRow list) =
    let d = derive fixture rows
    let sumTok = rows |> List.map (fun r -> r.Tokens) |> List.fold (Array.map2 (+)) (Array.zeroCreate 6)
    let tokObj (t: int64[]) = jobj [ "input", jint t[0]; "cacheWrite5m", jint t[1]; "cacheWrite1h", jint t[2]; "cacheRead", jint t[3]; "output", jint t[4]; "total", jint t[5] ]
    let cost = rows |> List.sumBy (fun r -> r.Cost)
    let accepted = rows |> List.filter (fun r -> r.FinalAccepted) |> List.length
    let claimedFirst = rows |> List.filter (fun r -> r.Claimed = "completed")
    let claimedFinal = rows |> List.filter (fun r -> r.ClaimedFinal = "completed")
    let firstCritical = d |> List.tryFind (fun (_, _, _, c, _, _) -> c) |> Option.map (fun (r, _, _, _, _, _) -> r.Unit)
    let unitJson (r: UnitRow, regressed: string list, carried: string list, critical, _, _) =
        jobj [ "unit", jint (int64 r.Unit); "task", jstr r.Task; "fault", jstr r.Fault; "claimed", jstr r.Claimed
               "acceptedFirstPass", jbool r.FirstAccepted; "acceptedFinal", jbool r.FinalAccepted; "attempts", jint (int64 r.Attempts)
               "falseCompletionFirstPass", jbool r.FalseFirst; "regressedTasks", jarr (regressed |> List.map jstr); "carriedDefects", jarr (carried |> List.map jstr)
               "architectureViolations", jarr (r.ArchRules |> List.map jstr); "decisions", jint (int64 r.Decisions); "unsupportedDecisions", jint (int64 r.Unsupported)
               "criticalFailure", jbool critical; "tokens", tokObj r.Tokens; "costUsd", jdec (Math.Round(r.Cost, 6)); "requests", jint r.Requests
               "toolUses", jint r.ToolUses; "contextLast", jint r.CtxLast; "compactions", jint r.Compactions; "wallMs", jnull; "verifyMs", jint r.VerifyMs
               "excluded", (if r.X4 > 0 then jstr (sprintf "X4: %d contamination hit(s)" r.X4) elif r.Models |> List.exists ((<>) "claude-opus-5-5") then jstr "X2" else jnull) ]
    jobj [ "schema", jstr "cbe.vac-001.metrics/1"; "run", jstr run; "arm", jstr arm
           "model", jarr (rows |> List.collect (fun r -> r.Models) |> List.distinct |> List.map jstr)
           "effort", jarr (rows |> List.collect (fun r -> r.Efforts) |> List.distinct |> List.map jstr)
           "priceTable", jstr "2026-10-20.1"
           "units", jarr (d |> List.map unitJson)
           "metrics", jobj [
               "UDR", ratio (rows |> List.sumBy (fun r -> r.Unsupported)) (rows |> List.sumBy (fun r -> r.Decisions)); "udrLayer", jstr "layer1"
               "AVR", ratio (rows |> List.filter (fun r -> not (List.isEmpty r.ArchRules)) |> List.length) rows.Length
               "DDR", ratio (d |> List.sumBy (fun (_, _, _, _, _, x) -> x)) (d |> List.sumBy (fun (_, _, _, _, e, _) -> e))
               "FCR", jobj [ "firstPass", ratio (claimedFirst |> List.filter (fun r -> r.FalseFirst) |> List.length) claimedFirst.Length
                             "delivered", ratio (claimedFinal |> List.filter (fun r -> r.FalseFinal) |> List.length) claimedFinal.Length ]
               "CCR", jobj [ "costUsd", jdec (Math.Round(cost, 6)); "acceptedUnits", jint (int64 accepted)
                             "usdPerAccepted", (if accepted = 0 then jnull else jdec (Math.Round(cost / decimal accepted, 6)))
                             "tokensPerAccepted", (if accepted = 0 then jnull else jdec (Math.Round(decimal sumTok[5] / decimal accepted, 1))); "tokens", tokObj sumTok ]
               "firstPassAcceptance", ratio (rows |> List.filter (fun r -> r.FirstAccepted) |> List.length) rows.Length
               "finalAcceptance", ratio accepted rows.Length
               "longevity", jobj [ "firstCriticalFailureUnit", (match firstCritical with Some u -> jint (int64 u) | None -> jnull)
                                   "censored", jbool firstCritical.IsNone
                                   "recoverableFailures", jarr (d |> List.filter (fun (r, _, _, c, _, _) -> not r.FirstAccepted && not c) |> List.map (fun (r, _, _, _, _, _) -> jint (int64 r.Unit)))
                                   "repairTokens", jint (rows |> List.sumBy (fun r -> r.RepairTokens)); "repairCostUsd", jdec (Math.Round(rows |> List.sumBy (fun r -> r.RepairCost), 6))
                                   "contextByUnit", jarr (rows |> List.map (fun r -> jint r.CtxLast)); "compactions", jint (rows |> List.sumBy (fun r -> r.Compactions))
                                   "carriedDefectsByUnit", jarr (d |> List.map (fun (_, reg, car, _, _, _) -> jint (int64 (reg.Length + car.Length)))) ] ]
           "unavailable", jobj [ "wallMs", jstr "per-unit agent wall-clock is not separable from transcript timestamps under concurrent arms; exploratory only"
                                 "UDR.layer3", jstr "Layer 3 adjudication is reported in hallucination-evaluation.md" ] ]

/// Paired percentile bootstrap over blocks (run x unit position): cost per accepted unit, arm X / arm Y.
let bootstrap (blocks: (decimal * int * decimal * int) list) (seed: int) (n: int) =
    let rnd = Random(seed)
    let stat (bs: (decimal * int * decimal * int) list) =
        let cx, ax, cy, ay = bs |> List.fold (fun (a, b, c, d) (w, x, y, z) -> a + w, b + x, c + y, d + z) (0m, 0, 0m, 0)
        if ax = 0 || ay = 0 || cy = 0m then None else Some(float ((cx / decimal ax) / (cy / decimal ay)) - 1.0)
    let arr = List.toArray blocks
    let samples =
        List.init n (fun _ -> List.init arr.Length (fun _ -> arr[rnd.Next arr.Length]) |> stat) |> List.choose id |> List.sort |> List.toArray
    let point = stat blocks
    let pct (p: float) = if samples.Length = 0 then nan else samples[min (samples.Length - 1) (int (p * float samples.Length))]
    point, pct 0.025, pct 0.975, samples.Length

let analyze (resultsDir: string) (runs: string list) (fixture: string) =
    let arms = [ "A"; "B"; "C"; "D"; "DR" ]
    let data =
        [ for run in runs do
            for arm in arms do
                let dir = Path.Combine(resultsDir, run, arm)
                if Directory.Exists dir && File.Exists(Path.Combine(dir, "setup.json")) then yield (run, arm), loadArm dir ]
    let perArm = data |> List.map (fun ((run, arm), rows) -> armMetrics fixture run arm rows)
    let contrast x y =
        let blocks =
            [ for run in runs do
                match data |> List.tryFind (fun ((r, a), _) -> r = run && a = x), data |> List.tryFind (fun ((r, a), _) -> r = run && a = y) with
                | Some(_, rx), Some(_, ry) ->
                    for ux in rx do
                        match ry |> List.tryFind (fun uy -> uy.Unit = ux.Unit) with
                        | Some uy -> yield ux.Cost, (if ux.FinalAccepted then 1 else 0), uy.Cost, (if uy.FinalAccepted then 1 else 0)
                        | None -> ()
                | _ -> () ]
        let point, lo, hi, valid = bootstrap blocks 20261021 10000
        jobj [ "comparison", jstr (sprintf "%s vs %s" x y); "measure", jstr "cost per accepted unit, relative difference"; "blocks", jint (int64 blocks.Length)
               "point", (match point with Some p -> jdec (Math.Round(decimal p, 4)) | None -> jnull)
               "ci95", jarr [ (if Double.IsNaN lo then jnull else jdec (Math.Round(decimal lo, 4))); (if Double.IsNaN hi then jnull else jdec (Math.Round(decimal hi, 4))) ]
               "validResamples", jint (int64 valid); "resamples", jint 10000L; "seed", jint 20261021L ]
    jobj [ "schema", jstr "cbe.vac-001.analysis/1"; "runs", jarr (runs |> List.map jstr); "generatedAt", jstr (DateTime.UtcNow.ToString("o"))
           "arms", jarr perArm
           "contrasts", jarr ([ "B", "A"; "C", "B"; "D", "B"; "D", "A"; "DR", "A"; "D", "DR" ] |> List.map (fun (x, y) -> contrast x y)) ]

// ---------- Dispatch ----------
match fsi.CommandLineArgs |> Array.toList |> List.tail with
| "archcheck" :: tree :: rest ->
    let vs = archcheck tree
    if List.contains "--json" rest then printfn "%s" (pretty (violationsJson vs))
    else
        vs |> List.iter (fun v -> printfn "%s %s:%d %s" v.Rule v.File v.Line v.Text)
        printfn "%s: %s (%d violation(s))" rulesVersion (if List.isEmpty vs then "PASS" else "FAIL") vs.Length
    exit (if List.isEmpty vs then 0 else 1)
| "evidence" :: tree :: unit :: _ -> printfn "%s" (pretty (evidence tree (int unit)))
| "observe" :: rest -> printfn "%s" (pretty (observe (args rest)))
| "state" :: rest -> printfn "%s" (pretty (state (args rest)))
| "usage" :: rest -> printfn "%s" (pretty (usage (args rest)))
| "analyze" :: results :: fixture :: runs -> printfn "%s" (pretty (analyze results runs fixture))
| _ -> eprintfn "usage: vac.fsx archcheck|evidence|observe|state|usage ..."; exit 2
