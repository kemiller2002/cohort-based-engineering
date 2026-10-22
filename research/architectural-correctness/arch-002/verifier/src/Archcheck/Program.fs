module Archcheck.Program

open System
open System.IO

let private usage =
    """usage:
  archcheck verify --repo DIR --policy POLICY.json [--contract CONTRACT.json] [--probes PROBES.json]
                   [--baseline REPORT.json] [--require-clean] [--json] [--out REPORT.json] [--facts USES.json]
  archcheck selftest [--samples DIR] [--filter NAME] [--parallel N]

exit codes: 0 no DET violation of severity >= 2; 1 at least one; 2 could not evaluate.
with --baseline, violations whose (rule, file, symbol, module) the baseline report holds are
marked preexisting and do not count toward the exit code."""

type private Args =
    { Values: Map<string, string>
      Flags: Set<string> }

let private flagNames = set [ "--json"; "--require-clean" ]

let private parseArgs (argv: string list) : Result<Args, string> =
    let rec go acc =
        function
        | [] -> Ok acc
        | f :: rest when flagNames.Contains f -> go { acc with Flags = acc.Flags.Add f } rest
        | k :: v :: rest when k.StartsWith "--" && not (v.StartsWith "--") -> go { acc with Values = acc.Values.Add(k, v) } rest
        | k :: _ -> Error $"unexpected argument '{k}'"

    go { Values = Map.empty; Flags = Set.empty } argv

let private verify (args: Args) =
    let known = set [ "--repo"; "--policy"; "--contract"; "--probes"; "--baseline"; "--out"; "--facts" ]

    match args.Values |> Map.toList |> List.map fst |> List.filter (known.Contains >> not) with
    | k :: _ ->
        eprintfn "unknown option %s\n%s" k usage
        2
    | [] ->
        match args.Values.TryFind "--repo", args.Values.TryFind "--policy" with
        | Some repo, Some policy ->
            let outcome =
                Verify.run
                    { Repo = repo
                      Policy = policy
                      Contract = args.Values.TryFind "--contract"
                      Probes = args.Values.TryFind "--probes"
                      Baseline = args.Values.TryFind "--baseline"
                      RequireClean = args.Flags.Contains "--require-clean" }

            let json = Report.render outcome.Report

            match args.Values.TryFind "--out" with
            | Some out ->
                let dir = Path.GetDirectoryName(Path.GetFullPath out)
                Directory.CreateDirectory dir |> ignore
                File.WriteAllText(out, json)
            | None -> ()

            match args.Values.TryFind "--facts" with
            | Some path -> File.WriteAllText(path, Json.render (Report.factsJson outcome.Report.Projects))
            | None -> ()

            let stdout = Console.OpenStandardOutput()
            let text = if args.Flags.Contains "--json" then json else Report.text outcome.Report
            let bytes = Text.UTF8Encoding(false).GetBytes text
            stdout.Write(bytes, 0, bytes.Length)
            stdout.Flush()
            outcome.ExitCode
        | _ ->
            eprintfn "verify needs --repo and --policy\n%s" usage
            2

let private selftest (args: Args) =
    match args.Values.TryFind "--samples" |> Option.orElse (Selftest.defaultSamplesDir ()) with
    | None ->
        eprintfn "no samples directory found; pass --samples DIR"
        2
    | Some dir ->
        let parallelism =
            args.Values.TryFind "--parallel" |> Option.map int |> Option.defaultValue 4

        let results = Selftest.run (Path.GetFullPath dir) (args.Values.TryFind "--filter") parallelism

        for r in results do
            printfn "%s %-28s %6dms  %s" (if r.Ok then "ok  " else "FAIL") r.Name r.ElapsedMs r.Detail

        let failed = results |> List.filter (fun r -> not r.Ok) |> List.length
        printfn "selftest: %d sample(s), %d failed" results.Length failed
        if failed = 0 && not results.IsEmpty then 0 else 1

[<EntryPoint>]
let main argv =
    match List.ofArray argv with
    | "verify" :: rest ->
        match parseArgs rest with
        | Ok a -> verify a
        | Error e ->
            eprintfn "%s\n%s" e usage
            2
    | "selftest" :: rest ->
        match parseArgs rest with
        | Ok a -> selftest a
        | Error e ->
            eprintfn "%s\n%s" e usage
            2
    | [ "--version" ] ->
        let v = Reflection.Assembly.GetExecutingAssembly().GetName().Version
        printfn "archcheck %O" v
        0
    | _ ->
        eprintfn "%s" usage
        2
