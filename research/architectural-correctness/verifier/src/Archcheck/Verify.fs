/// `archcheck verify`: the effectful pipeline. Loads inputs, binds the evaluated revision,
/// builds, type-checks, then hands immutable facts to the pure rules.
module Archcheck.Verify

open System
open System.Diagnostics
open System.IO
open System.Reflection
open Archcheck.Domain
open Archcheck.Policy
open Archcheck.Report

type Options =
    { Repo: string
      Policy: string
      Contract: string option
      Probes: string option
      RequireClean: bool }

type Outcome = { Report: Report; ExitCode: int }

let private assemblyInfo () =
    let asm = Assembly.GetExecutingAssembly()

    let informational (a: Assembly) =
        match a.GetCustomAttribute<AssemblyInformationalVersionAttribute>() with
        | null -> string (a.GetName().Version)
        | attr -> attr.InformationalVersion.Split('+')[0]

    let fcs = typeof<FSharp.Compiler.CodeAnalysis.FSharpChecker>.Assembly
    let sha = if File.Exists asm.Location then Provenance.sha256File asm.Location else ""
    informational asm, sha, informational fcs

/// Evaluation could not proceed: exit 2 with the reasons in `errors`.
exception NotEvaluable of string list

let private require (ok: bool) (message: string) =
    if not ok then raise (NotEvaluable [ message ])

let private ofResult (context: string) =
    function
    | Ok v -> v
    | Error (e: string) -> raise (NotEvaluable [ $"{context}: {e}" ])

let private readInput (repo: string) (label: string) (path: string) =
    let full = Paths.full path
    require (File.Exists full) $"{label} file not found: {path}"
    // Integrity: nothing that parameterises the check may come from the evaluated tree.
    require (not (Paths.isUnder repo full)) $"{label} {path} is inside --repo; it must be supplied from outside the evaluated repository"
    let text = File.ReadAllText full
    full, text, Provenance.sha256Hex (Text.Encoding.UTF8.GetBytes text)

let private isProjectFile (p: string) =
    (p.EndsWith ".fsproj" || p.EndsWith ".csproj")
    && not (p.Split('/') |> Array.exists Paths.isIgnoredSegment)

/// Classify a discovered project by the policy's tier map and test prefixes.
let classify (policy: Policy) (path: string) : Result<ProjectRole * int option, string> =
    match policy.Projects |> List.tryFind (fun e -> e.Path = path) with
    | Some e -> Ok(Production, Some e.Tier)
    | None when policy.TestProjects |> List.exists (fun prefix -> path = prefix || path.StartsWith(prefix.TrimEnd('/') + "/")) ->
        Ok(Test, None)
    | None -> Error $"project {path} is not in the policy tier map (A1: unmapped projects are not guessed)"

let private timed (timings: ResizeArray<string * int64>) (name: string) (f: unit -> 'a) : 'a =
    let sw = Stopwatch.StartNew()
    let r = f ()
    timings.Add(name, sw.ElapsedMilliseconds)
    r

let private assemblyKind (item: MsBuild.Item) =
    if item.Meta "FrameworkReferenceName" <> "" then Framework
    elif item.Meta "ReferenceSourceTarget" = "ProjectReference" then ProjectOutput
    elif item.Meta "NuGetPackageId" <> "" then Package(item.Meta "NuGetPackageId")
    else Raw

let private lineOf (declared: Map<string, MsBuild.DeclaredItem list>) (kind: string) (definedIn: string) (matches: MsBuild.DeclaredItem -> bool) =
    declared
    |> Map.tryFind definedIn
    |> Option.defaultValue []
    |> List.tryFind (fun d -> d.Kind = kind && matches d)
    |> Option.map _.Line
    |> Option.defaultValue 1

let private sourceFile (repo: string) (f: Symbols.CheckedFile) : SourceFile =
    let s = f.Syntax

    { Path = Paths.relative repo f.FullPath
      Lines =
        let t = f.Source.Replace("\r\n", "\n")
        let n = t.Split('\n').Length
        if t.EndsWith "\n" then n - 1 else n
      Uses = f.Uses
      Comments = s.Comments
      BindingNames = s.BindingNames
      StringLiterals = s.StringLiterals
      Handlers = s.Handlers
      Arms = s.Arms
      Literals = s.Literals
      BinaryOps = s.BinaryOps }

let private evaluateRepo (dotnet: string) (repo: string) (policy: Policy) (files: string list) (timings: ResizeArray<string * int64>) (built: bool ref) : Facts =
    let projects =
        files
        |> List.filter isProjectFile
        |> List.map (fun p -> p, classify policy p)

    match projects |> List.choose (fun (_, r) -> match r with Error e -> Some e | Ok _ -> None) with
    | [] -> ()
    | errors -> raise (NotEvaluable errors)

    let projects =
        projects |> List.map (fun (p, r) -> p, (match r with Ok v -> v | Error _ -> failwith "unreachable"))

    require (projects |> List.exists (fun (_, (role, _)) -> role = Production)) "no production project found"

    // Declared items (XML) of every MSBuild file in the evaluated content, for locations.
    let declared =
        files
        |> List.filter (fun p ->
            isProjectFile p || p.EndsWith ".props" || p.EndsWith ".targets")
        |> List.map (fun p ->
            p,
            (try
                MsBuild.declaredItems (Path.Combine(repo, p))
             with ex ->
                 raise (NotEvaluable [ $"{p} is not well-formed MSBuild XML: {ex.Message}" ])))
        |> Map.ofList

    let production = projects |> List.filter (fun (_, (role, _)) -> role = Production) |> List.map fst

    // Roots: production projects no other production project references directly.
    let referenced =
        production
        |> List.collect (fun p ->
            declared[p]
            |> List.filter (fun d -> d.Kind = "ProjectReference")
            |> List.map (fun d ->
                Paths.relative repo (Path.GetFullPath(Path.Combine(repo, Path.GetDirectoryName p, d.Include.Replace('\\', '/'))))))
        |> Set.ofList

    let roots = production |> List.filter (fun p -> not (referenced.Contains p))
    let roots = if roots.IsEmpty then production else roots

    timed timings "buildMs" (fun () ->
        for root in roots do
            MsBuild.build dotnet repo (Path.Combine(repo, root)) |> ofResult "build")

    built.Value <- true

    let evaluations =
        timed timings "designTimeMs" (fun () ->
            projects
            |> Array.ofList
            |> Array.Parallel.map (fun (p, (role, _)) ->
                let full = Path.Combine(repo, p)

                p,
                (if role = Production then
                     MsBuild.designTime dotnet repo full
                 else
                     MsBuild.evaluate dotnet repo full)
                |> ofResult p)
            |> Map.ofArray)

    let insideRepoSource (path: string) =
        Paths.isUnder repo path
        && not ((Paths.relative repo path).Split('/') |> Array.exists Paths.isIgnoredSegment)

    let typeChecked =
        timed timings "typeCheckMs" (fun () ->
            [ for p in production do
                  let ev = evaluations[p]

                  if p.EndsWith ".fsproj" then
                      let args = ev.ItemsOf "FscCommandLineArgs" |> List.map _.Identity
                      require (not args.IsEmpty) $"{p}: MSBuild returned no compiler arguments"
                      let projectDir = Path.GetDirectoryName(Path.Combine(repo, p))
                      let options, sources = MsBuild.splitCompilerArgs projectDir args
                      let result = Symbols.check (Path.Combine(repo, p)) (options @ sources) insideRepoSource

                      if not result.Errors.IsEmpty then
                          raise (NotEvaluable(result.Errors |> List.map (fun e -> $"{p}: type-check: {e}")))

                      yield p, result.Files
                  else
                      yield p, [] ]
            |> Map.ofList)

    let testFiles =
        projects
        |> List.filter (fun (_, (role, _)) -> role = Test)
        |> List.map (fun (p, _) ->
            let projectDir = Path.GetDirectoryName(Path.Combine(repo, p))

            p,
            evaluations[p].ItemsOf "Compile"
            |> List.map (fun i -> Path.GetFullPath(Path.Combine(projectDir, i.Identity)))
            |> List.filter (fun f -> insideRepoSource f && File.Exists f && (f.EndsWith ".fs" || f.EndsWith ".fsi"))
            |> List.distinct
            |> List.map Symbols.parseOnly)
        |> Map.ofList

    let underRepo (path: string) = path <> "" && Paths.isUnder repo path

    { Projects =
        [ for (p, (role, tier)) in projects do
              let ev = evaluations[p]

              let projectRefs =
                  ev.ItemsOf "ProjectReference"
                  |> List.filter (fun i -> underRepo (i.Meta "DefiningProjectFullPath"))
                  |> List.map (fun i ->
                      let target = Paths.relative repo (i.Meta "FullPath")
                      let definedIn = Paths.relative repo (i.Meta "DefiningProjectFullPath")
                      let projectDir = Path.GetDirectoryName(Path.Combine(repo, p))

                      { Target = target
                        DefinedIn = definedIn
                        Line =
                          lineOf declared "ProjectReference" definedIn (fun d ->
                              Paths.full (Path.Combine(projectDir, d.Include.Replace('\\', '/'))) = Paths.full (i.Meta "FullPath")) })
                  |> List.distinct

              let packages =
                  ev.ItemsOf "PackageReference"
                  |> List.map (fun i ->
                      let definedAt = i.Meta "DefiningProjectFullPath"
                      let direct = underRepo definedAt
                      let definedIn = if direct then Paths.relative repo definedAt else p

                      { Id = i.Identity
                        Version = i.Meta "Version"
                        Direct = direct
                        DefinedIn = definedIn
                        Line = if direct then lineOf declared "PackageReference" definedIn (fun d -> d.Include = i.Identity) else 1 })
                  |> List.distinct

              let assemblyRefs =
                  ev.ItemsOf "ReferencePath"
                  |> List.map (fun i -> { Path = i.Identity; Kind = assemblyKind i })
                  |> List.distinct

              let files =
                  match role with
                  | Production -> typeChecked[p] |> List.map (sourceFile repo)
                  | Test -> testFiles[p] |> List.map (sourceFile repo)

              yield
                  { Path = p
                    Tier = tier
                    Role = role
                    AssemblyName = ev.Property "AssemblyName"
                    ProjectRefs = projectRefs
                    Packages = packages
                    AssemblyRefs = assemblyRefs
                    Files = files |> List.sortBy _.Path } ] }

/// All findings for the given facts: pure.
let findings (instances: RuleInstance list) (decisions: string list option) (facts: Facts) : Finding list =
    instances
    |> List.collect (fun i ->
        match i.Rule.Class with
        | Det -> Rules.evaluate decisions facts i
        | Heu -> Heuristics.evaluate facts i)
    |> consolidate

let run (opts: Options) : Outcome =
    let total = Stopwatch.StartNew()
    let timings = ResizeArray<string * int64>()
    let version, sha, fcs = assemblyInfo ()
    let dotnet = Exec.dotnetHost ()
    let repo = Paths.full opts.Repo

    let empty =
        { Verifier = { Version = version; Sha256 = sha; Fcs = fcs; DotnetSdk = "" }
          Policy = { Id = ""; Sha256 = "" }
          Probes = None
          Contract = None
          Repo = { GitHead = None; TreeClean = false; TreeHash = "" }
          BuildOk = false
          Errors = []
          Projects = []
          Findings = []
          EvaluatedAt = DateTimeOffset.UtcNow
          TimingsMs = [] }

    let mutable report = empty

    let finish exitCode =
        timings.Add("totalMs", total.ElapsedMilliseconds)
        { Report = { report with TimingsMs = List.ofSeq timings }; ExitCode = exitCode }

    try
        require (Directory.Exists repo) $"--repo {opts.Repo} is not a directory"
        let _, policyText, policySha = readInput repo "policy" opts.Policy
        let policy = Policy.decode policyText |> ofResult "policy"
        report <- { report with Policy = { Id = policy.Id; Sha256 = policySha } }

        let probes =
            opts.Probes
            |> Option.map (fun path ->
                let _, text, digest = readInput repo "probes" path
                let instances = Policy.decodeProbes text |> ofResult "probes"
                report <- { report with Probes = Some { Id = Path.GetFileName path; Sha256 = digest } }
                instances)
            |> Option.defaultValue []

        let decisions =
            opts.Contract
            |> Option.map (fun path ->
                let _, text, digest = readInput repo "contract" path
                let ids = Policy.decodeContract text |> ofResult "contract"
                report <- { report with Contract = Some({ Id = Path.GetFileName path; Sha256 = digest }, ids) }
                ids)

        let files, repoInfo =
            timed timings "provenanceMs" (fun () ->
                let isGit = Provenance.isGitWorkTree repo
                let files = Provenance.contentFiles repo

                files,
                { GitHead = (if isGit then Provenance.gitHead repo else None)
                  TreeClean = isGit && Provenance.treeClean repo
                  TreeHash = Provenance.treeHash repo files })

        report <-
            { report with
                Repo = repoInfo
                Verifier = { report.Verifier with DotnetSdk = Provenance.sdkVersion dotnet repo } }

        require
            (not opts.RequireClean || repoInfo.TreeClean)
            "--require-clean: the working tree is dirty (or not a git work tree); the evaluated content would not be the committed revision"

        let built = ref false

        let facts =
            try
                evaluateRepo dotnet repo policy files timings built
            finally
                report <- { report with BuildOk = built.Value }

        report <- { report with Projects = facts.Projects }

        let instances =
            policy.Rules
            @ probes
            @ (match decisions with
               | Some _ when not (policy.Rules |> List.exists (fun r -> r.Rule.Id = "ARC-TRC-01")) ->
                   [ { Rule = (Catalogue.tryFind "ARC-TRC-01").Value
                       Params = RuleParams.empty
                       Origin = "policy" } ]
               | _ -> [])

        let all = timed timings "rulesMs" (fun () -> findings instances decisions facts)
        report <- { report with Findings = all }
        finish (if pass all then 0 else 1)
    with
    | NotEvaluable errors ->
        report <- { report with Errors = errors; Findings = [] }
        finish 2
    | ex ->
        report <- { report with Errors = [ $"internal error: {ex.GetType().Name}: {ex.Message}" ]; Findings = [] }
        finish 2
