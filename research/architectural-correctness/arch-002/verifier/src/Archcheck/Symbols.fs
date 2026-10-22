/// Type-checking a project with FSharpChecker using the real compiler arguments, and
/// turning every typed symbol use into a `SymbolUse` fact.
module Archcheck.Symbols

open System
open System.IO
open FSharp.Compiler.CodeAnalysis
open FSharp.Compiler.Diagnostics
open FSharp.Compiler.Symbols
open FSharp.Compiler.Text
open Archcheck.Domain

let private checker =
    lazy
        (FSharpChecker.Create(
            projectCacheSize = 20,
            keepAssemblyContents = false,
            keepAllBackgroundResolutions = false,
            keepAllBackgroundSymbolUses = true,
            parallelReferenceResolution = true
        ))

/// Follow type abbreviations to the abbreviated definition (`type Clock = System.DateTime`).
let rec private resolve (e: FSharpEntity) : FSharpEntity =
    if e.IsFSharpAbbreviation && e.AbbreviatedType.HasTypeDefinition then
        let target = e.AbbreviatedType.TypeDefinition
        if obj.ReferenceEquals(target, e) then e else resolve target
    else
        e

/// Drop generic arity suffixes: ``Option`1`` → `Option`, ``Dictionary`2.TryGetValue`` →
/// `Dictionary.TryGetValue`, so policies name symbols as source code does.
let private stripArity (name: string) =
    name.Split('.')
    |> Array.map (fun segment ->
        match segment.IndexOf '`' with
        | -1 -> segment
        | i when i > 0 && segment.Substring(i + 1) |> Seq.forall Char.IsDigit -> segment.Substring(0, i)
        | _ -> segment)
    |> String.concat "."

/// The dotted source-level name of an entity, after following abbreviations:
/// `AccessPath.DisplayName` for F# entities (so `module Loan` beside `type Loan` is
/// `…Loan`, not the compiled `…LoanModule`), the CLR full name otherwise; generic arity
/// suffixes removed.
let entityName (e: FSharpEntity) : string =
    let e = resolve e

    let raw =
        if e.IsFSharp || e.IsFSharpModule then
            let path =
                try
                    e.AccessPath
                with _ ->
                    ""

            let display = e.DisplayNameCore
            if String.IsNullOrEmpty path || path = "global" then display else path + "." + display
        else
            match e.TryFullName with
            | Some n -> n
            | None -> e.LogicalName

    stripArity raw

let private assemblyOf (s: FSharpSymbol) =
    try
        s.Assembly.SimpleName
    with _ ->
        ""

let private memberName (m: FSharpMemberOrFunctionOrValue) =
    let logical = m.LogicalName

    if (m.IsPropertyGetterMethod || m.IsPropertySetterMethod) && logical.Length > 4 && logical[3] = '_' then
        logical.Substring 4
    else
        logical

/// (qualified name, owner, kind) of a symbol, or None for locals, parameters, generic
/// parameters and namespaces, which no rule is defined over.
let describe (symbol: FSharpSymbol) : (string * string * SymbolKind) option =
    try
        match symbol with
        | :? FSharpMemberOrFunctionOrValue as m when m.IsModuleValueOrMember ->
            match m.DeclaringEntity with
            | None -> None
            | Some decl ->
                let owner = entityName decl

                let kind =
                    if m.IsConstructor then Constructor
                    elif m.IsProperty || m.IsPropertyGetterMethod || m.IsPropertySetterMethod then Property
                    elif m.IsEvent then Event
                    elif m.IsActivePattern then ActivePattern
                    elif decl.IsFSharpModule then
                        if m.FullType.IsFunctionType || m.CurriedParameterGroups.Count > 0 then Function else ModuleValue
                    else Method

                Some(owner + "." + memberName m, owner, kind)
        | :? FSharpEntity as e when not e.IsNamespace ->
            let r = resolve e

            let owner =
                match r.DeclaringEntity with
                | Some d -> entityName d
                | None -> r.Namespace |> Option.defaultValue ""

            Some(entityName r, owner, Type)
        | :? FSharpField as f ->
            match f.DeclaringEntity with
            | Some d when not f.IsAnonRecordField ->
                let owner = entityName d
                Some(owner + "." + f.Name, owner, Field)
            | _ -> None
        | :? FSharpUnionCase as u ->
            let owner = entityName u.DeclaringEntity
            Some(owner + "." + u.Name, owner, UnionCase)
        | :? FSharpActivePatternCase as a ->
            match a.Group.DeclaringEntity with
            | Some d ->
                let owner = entityName d
                Some(owner + "." + a.Name, owner, ActivePattern)
            | None -> None
        | _ -> None
    with _ ->
        None

type CheckedFile =
    { FullPath: string
      Source: string
      Syntax: Syntax.FileSyntax
      Uses: SymbolUse list }

type CheckResult =
    { Errors: string list
      Files: CheckedFile list }

/// Type-check one project from its fsc command line (sources already absolute) and collect
/// facts for the sources `includeFile` selects.
let private checkUnlocked (projectFile: string) (compilerArgs: string list) (includeFile: string -> bool) : CheckResult =
    let fcs = checker.Value

    let isSource (a: string) =
        not (a.StartsWith "-")
        && (a.EndsWith(".fs", StringComparison.OrdinalIgnoreCase)
            || a.EndsWith(".fsi", StringComparison.OrdinalIgnoreCase))

    let sources, flags = compilerArgs |> List.partition isSource

    let options =
        { fcs.GetProjectOptionsFromCommandLineArgs(projectFile, Array.ofList flags) with
            SourceFiles = Array.ofList sources }

    let results = fcs.ParseAndCheckProject options |> Async.RunSynchronously

    let errors =
        results.Diagnostics
        |> Array.filter (fun d -> d.Severity = FSharpDiagnosticSeverity.Error)
        |> Array.map (fun d -> $"{d.FileName}({d.StartLine},{d.StartColumn + 1}): FS{d.ErrorNumber:D4} {d.Message}")
        |> List.ofArray

    if not errors.IsEmpty || results.HasCriticalErrors then
        { Errors = (if errors.IsEmpty then [ "type-check reported critical errors" ] else errors)
          Files = [] }
    else
        let parsingOptions, _ = fcs.GetParsingOptionsFromProjectOptions options

        let usesByFile =
            results.GetAllUsesOfAllSymbols()
            |> Array.filter (fun u -> not u.IsFromDefinition && not u.IsFromOpenStatement)
            |> Array.groupBy (fun u -> Path.GetFullPath u.FileName)
            |> Map.ofArray

        let files =
            options.SourceFiles
            |> Array.filter includeFile
            |> Array.map (fun path ->
                let source = File.ReadAllText path

                let parsed =
                    fcs.ParseFile(path, SourceText.ofString source, parsingOptions)
                    |> Async.RunSynchronously

                let syntax = Syntax.analyse parsed.ParseTree source

                let uses =
                    usesByFile
                    |> Map.tryFind (Path.GetFullPath path)
                    |> Option.defaultValue [||]
                    |> Array.choose (fun u ->
                        describe u.Symbol
                        |> Option.map (fun (name, owner, kind) ->
                            let span = Syntax.spanOf u.Range

                            { Name = name
                              Owner = owner
                              Assembly = assemblyOf u.Symbol
                              Kind = kind
                              Span = span
                              Scope = Syntax.scopeAt syntax.Scopes span
                              IsFromPattern = u.IsFromPattern
                              IsFromType = u.IsFromType
                              IsRecordConstructionLabel = kind = Field && syntax.RecordLabels.Contains span }))
                    |> Array.distinct
                    |> Array.sortBy (fun u -> u.Span.StartLine, u.Span.StartCol, u.Name)
                    |> List.ofArray

                { FullPath = path
                  Source = source
                  Syntax = syntax
                  Uses = uses })
            |> List.ofArray

        { Errors = []; Files = files }

let private gate = obj ()

let check (projectFile: string) (compilerArgs: string list) (includeFile: string -> bool) : CheckResult =
    // One checker serves every project; concurrent selftest samples take turns.
    lock gate (fun () -> checkUnlocked projectFile compilerArgs includeFile)

/// Parse only (no type-check): used for test projects and for ARC-TRC-01.
let parseOnly (path: string) : CheckedFile =
    let fcs = checker.Value
    let source = File.ReadAllText path

    let options =
        { FSharpParsingOptions.Default with
            SourceFiles = [| path |] }

    let parsed =
        fcs.ParseFile(path, SourceText.ofString source, options) |> Async.RunSynchronously

    { FullPath = path
      Source = source
      Syntax = Syntax.analyse parsed.ParseTree source
      Uses = [] }
