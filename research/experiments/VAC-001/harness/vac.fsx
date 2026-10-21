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
    match r' with
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
    let trx = Directory.GetFiles(dir, "*.trx", SearchOption.AllDirectories) |> Array.tryHead
    match trx with
    | None -> []
    | Some f ->
        XDocument.Load(f).Descendants()
        |> Seq.filter (fun e -> e.Name.LocalName = "UnitTestResult")
        |> Seq.map (fun e ->
            let name = e.Attribute(XName.Get "testName").Value
            let task = Regex.Match(name, @"Oracle(V\d)").Groups[1].Value
            let req = Regex.Match(name, @"LEDGER-V\d-R\d").Value
            { Name = name; Task = task; Requirement = req; Outcome = e.Attribute(XName.Get "outcome").Value })
        |> Seq.toList

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
    let oracleLog = testSummary (Path.Combine(a["oracle-dir"], "..", "oracle.log"))
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
                                t, jobj [ "cases", jint (int64 (byTask t).Length); "failed", jint (int64 (byTask t |> List.filter (fun c -> c.Outcome <> "Passed")).Length) ]))
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
| _ -> eprintfn "usage: vac.fsx archcheck|evidence|observe|state|usage ..."; exit 2
