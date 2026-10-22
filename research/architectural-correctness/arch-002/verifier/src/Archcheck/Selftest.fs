/// `archcheck selftest`: runs the verifier over the synthetic sample repositories and
/// checks each one's exit code and exact set of rule ids against its `expected.json`.
///
/// Every sample is copied to a fresh temporary directory and committed to a new git
/// repository there, so the run also checks `treeClean`, `--require-clean` and that the
/// reported tree hash equals git's own `HEAD^{tree}`.
module Archcheck.Selftest

open System
open System.IO
open Archcheck.Json

type Expectation =
    { Name: string
      Dir: string
      Exit: int
      Rules: string list
      Policy: string
      Contract: string option
      Probes: string option
      RequireClean: bool
      /// Exact number of findings, when given.
      Findings: int option
      /// Policy path inside the copied repository (to test the integrity refusal).
      RepoPolicy: string option
      /// Leave an untracked file after committing.
      Dirty: bool
      /// ARCH-002: a sample directory (e.g. `base`) evaluated first; its report is the
      /// `--baseline` of the `repo` run.
      BaselineRepo: string option
      /// ARCH-002: exact counts of new and pre-existing findings and of fixed baseline keys.
      New: int option
      Preexisting: int option
      Fixed: int option
      /// ARCH-002: the lines of the non-preexisting findings, when given.
      NewLines: int list option }

type SampleResult =
    { Name: string
      Ok: bool
      Detail: string
      ElapsedMs: int64 }

/// Locate `tests/samples` from the binary upward (works from bin/ and from dist/).
let defaultSamplesDir () =
    let rec up (dir: DirectoryInfo) =
        if isNull dir then
            None
        else
            let candidate = Path.Combine(dir.FullName, "tests", "samples")
            if Directory.Exists candidate then Some candidate else up dir.Parent

    up (DirectoryInfo AppContext.BaseDirectory)

let private decode (samplesDir: string) (dir: string) : Result<Expectation, string> =
    let name = Path.GetFileName dir
    let path = Path.Combine(dir, "expected.json")

    match File.ReadAllText path |> parse with
    | Error e -> Error $"{name}: {e}"
    | Ok v ->
        let rel (key: string) =
            member' key v
            |> Option.bind asString
            |> Option.map (fun p -> Path.GetFullPath(Path.Combine(dir, p)))

        match member' "exit" v |> Option.bind asInt, stringList "rules" v with
        | Some exit, Ok rules ->
            Ok
                { Name = name
                  Dir = dir
                  Exit = exit
                  Rules = rules |> List.distinct |> List.sort
                  Policy =
                    rel "policy"
                    |> Option.defaultValue (Path.GetFullPath(Path.Combine(samplesDir, "..", "..", "policy", "lending.policy.json")))
                  Contract = rel "contract"
                  Probes = rel "probes"
                  RequireClean = member' "requireClean" v = Some(JBool true)
                  Findings = member' "findings" v |> Option.bind asInt
                  RepoPolicy = member' "repoPolicy" v |> Option.bind asString
                  Dirty = member' "dirty" v = Some(JBool true)
                  BaselineRepo = member' "baselineRepo" v |> Option.bind asString
                  New = member' "new" v |> Option.bind asInt
                  Preexisting = member' "preexisting" v |> Option.bind asInt
                  Fixed = member' "fixed" v |> Option.bind asInt
                  NewLines =
                    match member' "newLines" v with
                    | Some(JArray xs) -> Some(xs |> List.choose asInt)
                    | _ -> None }
        | _ -> Error $"{name}: expected.json needs 'exit' and 'rules'"

let rec private copyTree (source: string) (target: string) =
    Directory.CreateDirectory target |> ignore

    for f in Directory.GetFiles source do
        File.Copy(f, Path.Combine(target, Path.GetFileName f))

    for d in Directory.GetDirectories source do
        let name = Path.GetFileName d

        if name <> "bin" && name <> "obj" then
            copyTree d (Path.Combine(target, name))

let private git (dir: string) (args: string list) =
    let r =
        Exec.run
            dir
            "git"
            ([ "-c"; "user.name=archcheck"; "-c"; "user.email=archcheck@invalid"; "-c"; "commit.gpgsign=false"; "-c"; "init.defaultBranch=main" ]
             @ args)
            (TimeSpan.FromMinutes 1.0)

    if r.ExitCode <> 0 then
        failwith $"""git {String.concat " " args} failed: {r.Stderr}"""

    r.Stdout.Trim()

let private committed (source: string) (repo: string) =
    copyTree source repo
    git repo [ "init"; "-q" ] |> ignore
    git repo [ "add"; "-A" ] |> ignore
    git repo [ "commit"; "-q"; "-m"; "sample"; "--date=2026-01-01T00:00:00Z" ] |> ignore
    git repo [ "rev-parse"; "HEAD^{tree}" ]

/// ARCH-002: evaluate the sample's baseline tree and write its report outside both trees.
let private baselineReport (workRoot: string) (e: Expectation) (dir: string) =
    let repo = Path.Combine(workRoot, e.Name + ".baseline")
    committed (Path.Combine(e.Dir, dir)) repo |> ignore

    let outcome =
        Verify.run
            { Repo = repo
              Policy = e.Policy
              Contract = e.Contract
              Probes = e.Probes
              Baseline = None
              RequireClean = false }

    if outcome.ExitCode = 2 then
        failwith ("baseline tree not evaluable: " + String.concat " / " outcome.Report.Errors)

    let path = Path.Combine(workRoot, e.Name + ".baseline.json")
    File.WriteAllText(path, Report.render outcome.Report)
    path

let runSample (workRoot: string) (e: Expectation) : SampleResult =
    let sw = Diagnostics.Stopwatch.StartNew()

    try
        let baseline = e.BaselineRepo |> Option.map (baselineReport workRoot e)
        let repo = Path.Combine(workRoot, e.Name)
        let headTree = committed (Path.Combine(e.Dir, "repo")) repo

        if e.Dirty then
            File.WriteAllText(Path.Combine(repo, "untracked.txt"), "dirty\n")

        let outcome =
            Verify.run
                { Repo = repo
                  Policy = (e.RepoPolicy |> Option.map (fun p -> Path.Combine(repo, p)) |> Option.defaultValue e.Policy)
                  Contract = e.Contract
                  Probes = e.Probes
                  Baseline = baseline
                  RequireClean = e.RequireClean }

        let found =
            outcome.Report.Findings |> List.map _.RuleId |> List.distinct |> List.sort

        let problems =
            [ if outcome.ExitCode <> e.Exit then
                  yield $"exit {outcome.ExitCode}, expected {e.Exit}"
              if found <> e.Rules then
                  yield $"""rules [{String.concat " " found}], expected [{String.concat " " e.Rules}]"""
              match e.Findings with
              | Some n when n <> outcome.Report.Findings.Length -> yield $"{outcome.Report.Findings.Length} findings, expected {n}"
              | _ -> ()
              let fresh = outcome.Report.Findings |> List.filter (fun f -> not f.Preexisting) |> List.length
              let pre = outcome.Report.Findings |> List.filter _.Preexisting |> List.length
              let fixedCount = outcome.Report.Baseline |> Option.map _.Fixed.Length |> Option.defaultValue 0
              match e.New with
              | Some n when n <> fresh -> yield $"{fresh} new findings, expected {n}"
              | _ -> ()
              match e.Preexisting with
              | Some n when n <> pre -> yield $"{pre} preexisting findings, expected {n}"
              | _ -> ()
              match e.Fixed with
              | Some n when n <> fixedCount -> yield $"{fixedCount} fixed baseline keys, expected {n}"
              | _ -> ()
              let newLines = outcome.Report.Findings |> List.filter (fun f -> not f.Preexisting) |> List.map _.Line |> List.sort
              match e.NewLines with
              | Some ls when List.sort ls <> newLines -> yield $"new findings at lines {newLines}, expected {ls}"
              | _ -> ()
              if e.BaselineRepo.IsSome && outcome.ExitCode <> 2 && outcome.Report.Baseline.IsNone then
                  yield "no baseline section in the report"
              if outcome.ExitCode <> 2 && outcome.Report.Repo.TreeHash <> headTree then
                  yield $"treeHash {outcome.Report.Repo.TreeHash} <> git HEAD^{{tree}} {headTree}"
              if outcome.ExitCode <> 2 && not outcome.Report.Repo.TreeClean then
                  yield "fresh commit reported as dirty"
              if e.Exit = 2 && outcome.Report.Errors.IsEmpty then
                  yield "exit 2 without an error" ]

        let detail =
            if problems.IsEmpty then
                let pre = outcome.Report.Findings |> List.filter _.Preexisting |> List.length
                let suffix = if e.BaselineRepo.IsSome then $" ({pre} preexisting)" else ""
                $"""exit {outcome.ExitCode} [{String.concat " " found}]{suffix}"""
            else
                String.concat "; " problems
                + (if outcome.Report.Errors.IsEmpty then "" else " | errors: " + String.concat " / " outcome.Report.Errors)

        { Name = e.Name; Ok = problems.IsEmpty; Detail = detail; ElapsedMs = sw.ElapsedMilliseconds }
    with ex ->
        { Name = e.Name; Ok = false; Detail = $"exception: {ex.Message}"; ElapsedMs = sw.ElapsedMilliseconds }

let loadSamples (samplesDir: string) : Result<Expectation list, string> =
    Directory.GetDirectories samplesDir
    |> Array.filter (fun d -> File.Exists(Path.Combine(d, "expected.json")))
    |> Array.sort
    |> Array.map (decode samplesDir)
    |> Array.fold
        (fun acc r ->
            match acc, r with
            | Ok xs, Ok x -> Ok(x :: xs)
            | Error e, _ -> Error e
            | _, Error e -> Error e)
        (Ok [])
    |> Result.map List.rev

/// Run every sample (optionally only those whose name contains `filter`).
let run (samplesDir: string) (filter: string option) (parallelism: int) : SampleResult list =
    match loadSamples samplesDir with
    | Error e -> [ { Name = "samples"; Ok = false; Detail = e; ElapsedMs = 0L } ]
    | Ok samples ->
        let selected =
            samples
            |> List.filter (fun s ->
                match filter with
                | Some f -> s.Name.Contains f
                | None -> true)

        let workRoot =
            Path.Combine(Path.GetTempPath(), "archcheck-selftest-" + Guid.NewGuid().ToString("N"))

        Directory.CreateDirectory workRoot |> ignore

        try
            selected
            |> List.map (fun s -> async { return runSample workRoot s })
            |> fun jobs -> Async.Parallel(jobs, maxDegreeOfParallelism = max 1 parallelism)
            |> Async.RunSynchronously
            |> List.ofArray
        finally
            try
                Directory.Delete(workRoot, true)
            with _ ->
                ()
