module Archcheck.Tests.UnitTests

open System.IO
open Xunit
open Archcheck
open Archcheck.Domain
open Archcheck.Json

[<Fact>]
let ``dotted prefixes respect segment boundaries`` () =
    Assert.True(Paths.isWithin "System.IO" "System.IO.File.ReadAllText")
    Assert.True(Paths.isWithin "System.IO" "System.IO")
    Assert.False(Paths.isWithin "System.IO" "System.IOX.File")
    Assert.False(Paths.isWithin "Lending.Host.Cli" "Lending.Host.CliTools")

[<Fact>]
let ``identifier wildcards`` () =
    Assert.True(Paths.wildcard "*Id" "LoanId")
    Assert.True(Paths.wildcard "Id" "Id")
    Assert.False(Paths.wildcard "*Id" "DueDate")
    Assert.True(Paths.wildcard "a*b*c" "axxbyyc")
    Assert.False(Paths.wildcard "a*b*c" "axxc")

[<Fact>]
let ``json rendering is stable and escaped`` () =
    let v = obj [ "b", str "x\"y\n"; "a", arr [ num 1; JBool false; JNull ]; "e", obj [] ]
    let expected = "{\n  \"b\": \"x\\\"y\\n\",\n  \"a\": [\n    1,\n    false,\n    null\n  ],\n  \"e\": {}\n}\n"
    Assert.Equal(expected, render v)
    Assert.Equal(render v, render v)

[<Fact>]
let ``shipped lending policy decodes with every rule`` () =
    let p = Support.lendingPolicy.Value
    Assert.Equal("lending/0.1", p.Id)
    Assert.Equal(4, p.Projects.Length)
    Assert.Equal<string list>(Catalogue.required |> List.sort, p.Rules |> List.map _.Rule.Id |> List.sort)

let private minimalPolicy (rules: string) =
    $"""{{ "schema": "arch001.policy/1", "id": "t", "projects": [{{"path":"a/A.fsproj","tier":1}}], "rules": {{ {rules} }} }}"""

let private allRules (overrides: (string * string) list) =
    Catalogue.required
    |> List.map (fun id ->
        let body = overrides |> List.tryFind (fst >> (=) id) |> Option.map snd |> Option.defaultValue "{}"
        $"\"{id}\": {body}")
    |> String.concat ", "

[<Fact>]
let ``policy refusals`` () =
    let isError =
        function
        | Error(_: string) -> true
        | Ok _ -> false

    Assert.True(isError (Policy.decode """{ "schema": "other/1" }"""))
    Assert.True(isError (Policy.decode (minimalPolicy "\"ARC-DEP-01\": {}")))
    Assert.True(isError (Policy.decode (minimalPolicy (allRules [ "ARC-SYM-01", """{ "namespacez": [] }""" ]))))
    Assert.True(isError (Policy.decode (minimalPolicy (allRules [ "ARC-BND-02", """{ "kinds": ["verb"] }""" ]))))
    Assert.True(isError (Policy.decode (minimalPolicy (allRules [ "ARC-SYM-01", """{ "tiers": [5] }""" ]))))
    Assert.True(isError (Policy.decode (minimalPolicy (allRules [] + ", \"ARC-XYZ-01\": {}"))))
    Assert.False(isError (Policy.decode (minimalPolicy (allRules []))))

[<Fact>]
let ``probes are complete rule instances`` () =
    let text =
        """[ { "rule": "ARC-BND-03", "module": "Lending.Host.Cli", "forbiddenSymbols": ["Lending.Semantic.Loan.DueDate"] },
             { "rule": "ARC-SYM-01", "tiers": [2], "symbols": ["System.DateTime.Now"] } ]"""

    match Policy.decodeProbes text with
    | Ok [ a; b ] ->
        Assert.Equal("probe:0", a.Origin)
        Assert.Equal<string list>([ "Lending.Host.Cli" ], a.Params.Modules)
        Assert.Equal<string list>([ "Lending.Semantic.Loan.DueDate" ], a.Params.Symbols)
        Assert.Empty(a.Params.EntityNamespaces)
        Assert.Equal(3, b.Rule.Severity)
    | other -> failwithf "%A" other

    Assert.True(Policy.decodeProbes """[ { "rule": "ARC-TRC-01" } ]""" |> Result.isError)
    Assert.True(Policy.decodeProbes """[ { "rule": "ARC-NOPE" } ]""" |> Result.isError)

[<Fact>]
let ``contract decisions are the decision nodes`` () =
    let text =
        """{ "schemaVersion": "ecir/1", "nodes": [ {"id":"DEC-B","kind":"decision"}, {"id":"V-1","kind":"verificationObligation"}, {"id":"DEC-A","kind":"decision"} ] }"""

    Assert.Equal<string list>([ "DEC-A"; "DEC-B" ], Policy.decodeContract text |> Result.defaultValue [])
    Assert.True(Policy.decodeContract """{ "schemaVersion": "ecir/2", "nodes": [] }""" |> Result.isError)

let private parse (source: string) =
    let path = Path.Combine(Path.GetTempPath(), $"archcheck-{System.Guid.NewGuid():N}.fs")
    File.WriteAllText(path, source)

    try
        (Symbols.parseOnly path).Syntax
    finally
        File.Delete path

[<Fact>]
let ``comments include doc lines but not strings`` () =
    let s =
        parse
            "module A.B\n/// doc DEC-1\n// line DEC-2\n(* block DEC-3 *)\nlet s = \"/// not DEC-4\"\nlet f x = x // tail DEC-5\n"

    let text = s.Comments |> List.map _.Text |> String.concat "|"

    for id in [ "DEC-1"; "DEC-2"; "DEC-3"; "DEC-5" ] do
        Assert.Contains(id, text)

    Assert.DoesNotContain("DEC-4", text)
    Assert.Contains("/// not DEC-4", s.StringLiterals)

[<Fact>]
let ``scopes resolve nested modules`` () =
    let s = parse "namespace Lending.Host\n\nmodule Cli =\n    module Render =\n        let x = 1\n\nmodule Other =\n    let y = 2\n"
    let at line = Syntax.scopeAt s.Scopes { StartLine = line; StartCol = 8; EndLine = line; EndCol = 9 }
    Assert.Equal("Lending.Host.Cli.Render", at 5)
    Assert.Equal("Lending.Host.Other", at 8)

[<Fact>]
let ``handlers, arms, literals and predicates`` () =
    let s =
        parse
            "module M\nlet a () = try 1 with _ -> 0\nlet b () = try 1 with ex -> reraise ()\nlet c () = try 1 with :? System.FormatException -> 0\nlet d o = match o with | Some x -> Ok x | None -> Error 14.0\nlet e r = r.Renewals >= 3\n"

    Assert.Equal<bool list>([ true; true; false ], s.Handlers |> List.map _.CatchAll)
    Assert.Equal<bool list>([ false; true; false ], s.Handlers |> List.map _.Reraises)
    Assert.Contains(s.Arms, fun a -> a.Case = "None" && a.Into = "Error")
    Assert.Contains(s.Literals, fun l -> l.Value = "14")
    Assert.Contains(s.BinaryOps, fun o -> o.Predicate = Some "Renewals >= 3")
