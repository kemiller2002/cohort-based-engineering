/// End-to-end: real `dotnet build`, MSBuild design-time pass and FCS type-check over
/// sample repositories. The full sample set runs with `archcheck selftest`.
module Archcheck.Tests.IntegrationTests

open System
open System.IO
open Xunit
open Archcheck
open Archcheck.Tests.Support


[<Fact>]
[<Trait("Category", "Integration")>]
let ``representative samples meet their expectations`` () =
    let wanted = set [ "clean"; "neg-regex-trap"; "sym01-alias"; "bnd03-entity-field"; "err-policy-in-repo" ]

    let samples =
        match Selftest.loadSamples samplesDir with
        | Ok s -> s |> List.filter (fun s -> wanted.Contains s.Name)
        | Error e -> failwith e

    Assert.Equal(wanted.Count, samples.Length)
    let work = Path.Combine(Path.GetTempPath(), "archcheck-it-" + Guid.NewGuid().ToString("N"))
    Directory.CreateDirectory work |> ignore

    try
        let results =
            samples
            |> List.map (fun s -> async { return Selftest.runSample work s })
            |> fun jobs -> Async.Parallel(jobs, maxDegreeOfParallelism = 3)
            |> Async.RunSynchronously

        for r in results do
            Assert.True(r.Ok, $"{r.Name}: {r.Detail}")
    finally
        try
            Directory.Delete(work, true)
        with _ ->
            ()

let private withoutRun (json: string) =
    match Json.parse json with
    | Ok(Json.JObject members) -> Json.render (Json.JObject(members |> List.filter (fun (k, _) -> k <> "run")))
    | other -> failwithf "%A" other

[<Fact>]
[<Trait("Category", "Integration")>]
let ``two runs on the same tree are byte-identical apart from run`` () =
    let work = Path.Combine(Path.GetTempPath(), "archcheck-det-" + Guid.NewGuid().ToString("N"))
    let repo = Path.Combine(work, "repo")

    let rec copy (src: string) (dst: string) =
        Directory.CreateDirectory dst |> ignore
        for f in Directory.GetFiles src do File.Copy(f, Path.Combine(dst, Path.GetFileName f))
        for d in Directory.GetDirectories src do
            if Path.GetFileName d <> "bin" && Path.GetFileName d <> "obj" then copy d (Path.Combine(dst, Path.GetFileName d))

    copy (Path.Combine(samplesDir, "heu02-duplicate", "repo")) repo

    try
        let verify () =
            Verify.run
                { Repo = repo
                  Policy = policyPath
                  Contract = None
                  Probes = None
                  RequireClean = false }

        let first = verify ()
        let second = verify ()
        Assert.Equal(0, first.ExitCode)
        Assert.NotEmpty(first.Report.Findings)
        Assert.Equal(withoutRun (Report.render first.Report), withoutRun (Report.render second.Report))
    finally
        try
            Directory.Delete(work, true)
        with _ ->
            ()
