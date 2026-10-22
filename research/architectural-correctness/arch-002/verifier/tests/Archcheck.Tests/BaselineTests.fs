/// ARCH-002 `--baseline`: key matching (line ignored, multiset, scope part of the key),
/// decoding and the gate. Pure; no build.
module Archcheck.Tests.BaselineTests

open Xunit
open Archcheck
open Archcheck.Domain
open Archcheck.Tests.Support

let private clock file line scope =
    Rules.finding (instance "ARC-SYM-02") "src/Lending.Transition/Lending.Transition.fsproj" file line 5 "System.DateTime.Now" "m"
    |> Rules.at scope

let private key file scope : Baseline.Key =
    { RuleId = "ARC-SYM-02"; File = file; Symbol = "System.DateTime.Now"; Scope = Some scope; Context = None }

let private loans = "src/Lending.Transition/Loans.fs"

[<Fact>]
let ``a finding that only moved lines is preexisting`` () =
    let out = Baseline.mark [ key loans "Lending.Transition.Loans" ] [ clock loans 40 "Lending.Transition.Loans" ]
    Assert.True(out.Findings.Head.Preexisting)
    Assert.Equal(1, out.Matched)
    Assert.Empty(out.Fixed)
    Assert.True(Report.pass out.Findings)

[<Fact>]
let ``keys are a multiset: two findings against one baseline key leave one new`` () =
    let found = [ clock loans 3 "Lending.Transition.Loans"; clock loans 9 "Lending.Transition.Loans" ]
    let out = Baseline.mark [ key loans "Lending.Transition.Loans" ] found
    Assert.Equal<bool list>([ true; false ], out.Findings |> List.map _.Preexisting)
    Assert.False(Report.pass out.Findings)
    Assert.Single(Report.gateFailures out.Findings) |> ignore

[<Fact>]
let ``a different module or file is a new key and the old key is fixed`` () =
    let out =
        Baseline.mark
            [ key loans "Lending.Transition.Loans" ]
            [ clock "src/Lending.Transition/Clock.fs" 4 "Lending.Transition.Clock"; clock loans 4 "Lending.Transition.Other" ]
    Assert.All(out.Findings, fun f -> Assert.False f.Preexisting)
    Assert.Equal<Baseline.Key list>([ key loans "Lending.Transition.Loans" ], out.Fixed)

[<Fact>]
let ``a different rule with the same place is new`` () =
    let other = { clock loans 4 "Lending.Transition.Loans" with RuleId = "ARC-SYM-01"; Severity = 3 }
    let out = Baseline.mark [ key loans "Lending.Transition.Loans" ] [ other ]
    Assert.False(out.Findings.Head.Preexisting)
    Assert.Single(out.Fixed) |> ignore

[<Fact>]
let ``a scope-less legacy key matches on rule, file and symbol`` () =
    let legacy = { key loans "x" with Scope = None }
    let out = Baseline.mark [ legacy ] [ clock loans 4 "Lending.Transition.Loans" ]
    Assert.True(out.Findings.Head.Preexisting)
    Assert.Empty(out.Fixed)

[<Fact>]
let ``preexisting HEU findings are marked too and never gate`` () =
    let heu =
        Rules.finding (instance "ARC-HEU-04") "p" loans 1 1 "" "long" |> Rules.at ""
    let k : Baseline.Key = { RuleId = "ARC-HEU-04"; File = loans; Symbol = ""; Scope = Some ""; Context = None }
    let out = Baseline.mark [ k ] [ heu ]
    Assert.True(out.Findings.Head.Preexisting)

[<Fact>]
let ``decode reads a rendered report and refuses an unevaluated one`` () =
    let report =
        """{ "schema": "arch002.verifier-report/1", "errors": [], "findings": [
             { "ruleId": "ARC-SYM-02", "file": "src/Lending.Transition/Loans.fs", "line": 4, "symbol": "System.DateTime.Now", "scope": "Lending.Transition.Loans" },
             { "ruleId": "ARC-TRC-01", "file": "", "line": 0, "symbol": "DEC-1" } ] }"""
    match Baseline.decode report with
    | Ok [ a; b ] ->
        Assert.Equal(key loans "Lending.Transition.Loans", a)
        Assert.Equal(None, b.Scope)
    | other -> failwithf "%A" other
    Assert.True(Baseline.decode """{ "schema": "arch002.verifier-report/1", "errors": ["build failed"], "findings": [] }""" |> Result.isError)
    Assert.True(Baseline.decode """{ "schema": "something/1", "findings": [] }""" |> Result.isError)
    Assert.True(Baseline.decode "not json" |> Result.isError)

[<Fact>]
let ``the report carries scope, preexisting and the new/preexisting split`` () =
    let out = Baseline.mark [ key loans "Lending.Transition.Loans" ] [ clock loans 3 "Lending.Transition.Loans"; clock loans 9 "Lending.Transition.Loans" ]
    match Report.summaryJson out.Findings with
    | Json.JObject members ->
        let det part =
            match List.find (fst >> (=) part) members |> snd with
            | Json.JObject m -> m |> List.find (fst >> (=) "det") |> snd
            | v -> failwithf "%A" v
        let total = function Json.JObject m -> m |> List.find (fst >> (=) "total") |> snd | v -> failwithf "%A" v
        Assert.Equal(Json.JInt 1L, total (det "new"))
        Assert.Equal(Json.JInt 1L, total (det "preexisting"))
        Assert.Equal(Json.JBool false, members |> List.find (fst >> (=) "pass") |> snd)
    | v -> failwithf "%A" v

[<Fact>]
let ``within a key the finding on the baseline's line text is the preexisting one`` () =
    let old = { key loans "Lending.Transition.Loans" with Context = Some "let stamp () = System.DateTime.Now" }
    let added = { clock loans 6 "Lending.Transition.Loans" with Context = "let due d = System.DateTime.Now.AddDays d" }
    let moved = { clock loans 9 "Lending.Transition.Loans" with Context = "let stamp () = System.DateTime.Now" }
    let out = Baseline.mark [ old ] [ added; moved ]
    Assert.Equal<bool list>([ false; true ], out.Findings |> List.map _.Preexisting)
    Assert.Equal(1, Report.gateFailures out.Findings |> List.length)

[<Fact>]
let ``withContext reads the trimmed source line`` () =
    let f = clock loans 2 "Lending.Transition.Loans"
    let out = Baseline.withContext (Map.ofList [ loans, [| "module M"; "    let stamp () = System.DateTime.Now  " |] ]) [ f; { f with Line = 99 } ]
    Assert.Equal<string list>([ "let stamp () = System.DateTime.Now"; "" ], out |> List.map _.Context)
