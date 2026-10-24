/// Loading the repository through MSBuild.
///
/// 1. Projects are discovered from the evaluated content (tracked + untracked non-ignored
///    files), and their declared ProjectReference/PackageReference elements are read with
///    an XML parser for locations.
/// 2. `dotnet build -c Release` builds every production root project.
/// 3. A design-time pass per project (`dotnet msbuild -t:Compile` with
///    `DesignTimeBuild=true; SkipCompilerExecution=true; ProvideCommandLineArgs=true`)
///    returns the exact `fsc` command line MSBuild would run (`FscCommandLineArgs`) and the
///    evaluated `ReferencePath`, `ProjectReference` and `PackageReference` items. The F#
///    compiler is not executed in this pass; `NonExistentFile` is set so the target is never
///    skipped as up to date (otherwise no arguments would be returned).
module Archcheck.MsBuild

open System
open System.IO
open System.Xml.Linq
open Archcheck.Json

/// A `ProjectReference`/`PackageReference` element as written in a project or import file.
type DeclaredItem =
    { Kind: string
      Include: string
      Version: string
      File: string
      Line: int }

let private localName (e: XElement) = e.Name.LocalName

/// Declared reference items in one MSBuild XML file (no evaluation, no imports followed).
let declaredItems (path: string) : DeclaredItem list =
    let doc = XDocument.Load(path, LoadOptions.SetLineInfo)

    doc.Descendants()
    |> Seq.filter (fun e -> localName e = "ProjectReference" || localName e = "PackageReference")
    |> Seq.choose (fun e ->
        let attr (n: string) =
            match e.Attribute(XName.Get n) with
            | null -> None
            | a -> Some a.Value

        let child (n: string) =
            e.Elements() |> Seq.tryFind (fun c -> localName c = n) |> Option.map _.Value

        match attr "Include" |> Option.orElse (attr "Update") with
        | None -> None
        | Some inc ->
            Some
                { Kind = localName e
                  Include = inc
                  Version = attr "Version" |> Option.orElse (child "Version") |> Option.defaultValue ""
                  File = Paths.normalize path
                  Line = (e :> Xml.IXmlLineInfo).LineNumber })
    |> List.ofSeq

/// An evaluated MSBuild item: identity plus metadata.
type Item =
    { Identity: string
      Metadata: Map<string, string> }

    member this.Meta(name: string) =
        this.Metadata |> Map.tryFind name |> Option.defaultValue ""

type Evaluation =
    { ProjectPath: string
      Properties: Map<string, string>
      Items: Map<string, Item list> }

    member this.ItemsOf(name: string) =
        this.Items |> Map.tryFind name |> Option.defaultValue []

    member this.Property(name: string) =
        this.Properties |> Map.tryFind name |> Option.defaultValue ""

let private decodeEvaluation (projectPath: string) (stdout: string) : Result<Evaluation, string> =
    let start = stdout.IndexOf '{'

    if start < 0 then
        Error "MSBuild returned no JSON"
    else
        match parse (stdout.Substring start) with
        | Error e -> Error $"MSBuild JSON: {e}"
        | Ok root ->
            let props =
                match member' "Properties" root with
                | Some(JObject ms) -> ms |> List.choose (fun (k, v) -> asString v |> Option.map (fun s -> k, s)) |> Map.ofList
                | _ -> Map.empty

            let items =
                match member' "Items" root with
                | Some(JObject groups) ->
                    groups
                    |> List.map (fun (name, v) ->
                        let entries =
                            asList v
                            |> Option.defaultValue []
                            |> List.map (fun item ->
                                match item with
                                | JObject ms ->
                                    let meta =
                                        ms |> List.choose (fun (k, v) -> asString v |> Option.map (fun s -> k, s)) |> Map.ofList

                                    { Identity = meta |> Map.tryFind "Identity" |> Option.defaultValue ""
                                      Metadata = meta }
                                | _ -> { Identity = ""; Metadata = Map.empty })

                        name, entries)
                    |> Map.ofList
                | _ -> Map.empty

            Ok { ProjectPath = projectPath; Properties = props; Items = items }

let private tail (n: int) (s: string) =
    let lines = s.Split('\n')
    lines[max 0 (lines.Length - n) ..] |> String.concat "\n"

/// `dotnet build -c Release` of one project. Restores from the configured NuGet feeds.
let build (dotnet: string) (repo: string) (project: string) : Result<unit, string> =
    let r =
        Exec.run
            repo
            dotnet
            [ "build"; project; "-c"; "Release"; "-nologo"; "-nodeReuse:false"; "-v:q"; "-clp:NoSummary;ErrorsOnly" ]
            (TimeSpan.FromMinutes 10.0)

    if r.ExitCode = 0 then
        Ok()
    else
        Error $"dotnet build {Paths.relative repo project} failed (exit {r.ExitCode}):\n{tail 40 (r.Stdout + r.Stderr)}"

let private designTimeArgs (project: string) =
    [ "msbuild"
      project
      "-nologo"
      "-nodeReuse:false"
      "-p:Configuration=Release"
      "-p:DesignTimeBuild=true"
      "-p:SkipCompilerExecution=true"
      "-p:ProvideCommandLineArgs=true"
      "-p:NonExistentFile=__archcheck_nonexistent__/__none__"
      "-t:Compile"
      "-getItem:FscCommandLineArgs"
      "-getItem:ReferencePath"
      "-getItem:ProjectReference"
      "-getItem:PackageReference"
      "-getItem:Reference"
      "-getItem:Compile"
      "-getProperty:AssemblyName"
      "-getProperty:TargetPath"
      "-getProperty:MSBuildProjectDirectory" ]

/// Design-time compile pass of a built project: the real compiler arguments and references.
let designTime (dotnet: string) (repo: string) (project: string) : Result<Evaluation, string> =
    let r = Exec.run repo dotnet (designTimeArgs project) (TimeSpan.FromMinutes 5.0)

    if r.ExitCode <> 0 then
        Error $"design-time evaluation of {Paths.relative repo project} failed (exit {r.ExitCode}):\n{tail 40 (r.Stdout + r.Stderr)}"
    else
        decodeEvaluation project r.Stdout

/// Plain evaluation (no targets) — used for test projects, which are not built.
let evaluate (dotnet: string) (repo: string) (project: string) : Result<Evaluation, string> =
    let r =
        Exec.run
            repo
            dotnet
            [ "msbuild"
              project
              "-nologo"
              "-nodeReuse:false"
              "-p:Configuration=Release"
              "-getItem:Compile"
              "-getProperty:AssemblyName"
              "-getProperty:MSBuildProjectDirectory" ]
            (TimeSpan.FromMinutes 5.0)

    if r.ExitCode <> 0 then
        Error $"evaluation of {Paths.relative repo project} failed (exit {r.ExitCode}):\n{tail 40 (r.Stdout + r.Stderr)}"
    else
        decodeEvaluation project r.Stdout

/// Split an fsc command line into (options, source files). Sources are resolved against
/// the project directory.
let splitCompilerArgs (projectDir: string) (args: string list) : string list * string list =
    let isSource (a: string) =
        not (a.StartsWith "-")
        && (a.EndsWith(".fs", StringComparison.OrdinalIgnoreCase)
            || a.EndsWith(".fsi", StringComparison.OrdinalIgnoreCase)
            || a.EndsWith(".fsx", StringComparison.OrdinalIgnoreCase))

    let sources, options = args |> List.partition isSource
    options, sources |> List.map (fun s -> Path.GetFullPath(Path.Combine(projectDir, s)))
