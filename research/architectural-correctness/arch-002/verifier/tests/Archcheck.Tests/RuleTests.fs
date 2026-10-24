module Archcheck.Tests.RuleTests

open Xunit
open Archcheck
open Archcheck.Domain
open Archcheck.Policy
open Archcheck.Tests.Support

let private sem = "src/Lending.Semantic/Lending.Semantic.fsproj"
let private app = "src/Lending.Application/Lending.Application.fsproj"
let private host = "src/Lending.Host/Lending.Host.fsproj"
let private tests = "tests/Lending.Tests/Lending.Tests.fsproj"

let private reference target line = { Target = target; DefinedIn = sem; Line = line }

[<Fact>]
let ``ARC-DEP-01 flags upward and test edges only`` () =
    let semantic = { project sem 1 [] with ProjectRefs = [ reference app 7; reference tests 8 ] }
    let application = { project app 3 [] with ProjectRefs = [ { Target = sem; DefinedIn = app; Line = 5 } ] }
    let testProject = { project tests 4 [] with Role = Test; Tier = None }
    let found = Rules.dependencyDirection (instance "ARC-DEP-01") (facts [ semantic; application; testProject ])
    Assert.Equal<int list>([ 7; 8 ], found |> List.map _.Line |> List.sort)
    Assert.All(found, fun f -> Assert.Equal(3, f.Severity))

[<Fact>]
let ``ARC-DEP-01 subsumes DOK-R008 forbidden pairs`` () =
    let i = instance "ARC-DEP-01"
    let i = { i with Params = { i.Params with ForbiddenReferences = [ "Lending.Application", "Lending.Semantic" ] } }
    let application = { project app 3 [] with ProjectRefs = [ { Target = sem; DefinedIn = app; Line = 5 } ] }
    let found = Rules.dependencyDirection i (facts [ project sem 1 []; application ])
    Assert.Single found |> ignore

[<Fact>]
let ``ARC-DEP-02 sees direct, transitive and raw references`` () =
    let p =
        { project sem 1 [] with
            Packages =
                [ { Id = "FSharp.Core"; Version = "10.1.402"; Direct = false; DefinedIn = sem; Line = 1 }
                  { Id = "Newtonsoft.Json"; Version = "13.0.1"; Direct = true; DefinedIn = sem; Line = 9 } ]
            AssemblyRefs =
                [ { Path = "/x/FSharp.Core.dll"; Kind = Package "FSharp.Core" }
                  { Path = "/x/Newtonsoft.Json.dll"; Kind = Package "Newtonsoft.Json" }
                  { Path = "/x/Npgsql.dll"; Kind = Package "Npgsql" }
                  { Path = "/x/Raw.dll"; Kind = Raw }
                  { Path = "/x/System.Runtime.dll"; Kind = Framework } ] }

    let found = Rules.pureReferences (instance "ARC-DEP-02") (facts [ p; project app 3 [] ])
    Assert.Equal<string list>([ "Newtonsoft.Json"; "Npgsql"; "Raw.dll" ], found |> List.map _.Symbol |> List.sort)

[<Fact>]
let ``ARC-SYM-02 exempts only the composition root`` () =
    let uses scope = [ symbolUse scope Property "System.DateTime.UtcNow" 3 ]

    let h =
        project host 4 [ file "src/Lending.Host/Composition.fs" (uses "Lending.Host.Composition")
                         file "src/Lending.Host/Cli/Render.fs" (uses "Lending.Host.Cli.Render") ]

    let found = Rules.forbiddenSymbols (instance "ARC-SYM-02") (facts [ h ])
    Assert.Equal<string list>([ "src/Lending.Host/Cli/Render.fs" ], found |> List.map _.File)

[<Fact>]
let ``ARC-SYM-01 applies to tiers 1 and 2 only`` () =
    let io = [ symbolUse "M" Method "System.IO.File.ReadAllText" 2 ]
    let found = Rules.forbiddenSymbols (instance "ARC-SYM-01") (facts [ project sem 1 [ file "a.fs" io ]; project host 4 [ file "b.fs" io ] ])
    Assert.Equal<string list>([ "a.fs" ], found |> List.map _.File)

[<Fact>]
let ``ARC-BND-02 ignores Transition types and union cases`` () =
    let uses =
        [ symbolUse "Lending.Host.Cli.Render" Type "Lending.Transition.Loans.Interpretation" 1
          symbolUse "Lending.Host.Cli.Render" UnionCase "Lending.Transition.Loans.Interpretation.Done" 2
          symbolUse "Lending.Host.Cli.Render" Function "Lending.Transition.Loans.renew" 3 ]

    let found = Rules.forbiddenSymbols (instance "ARC-BND-02") (facts [ project host 4 [ file "r.fs" uses ] ])
    Assert.Equal<int list>([ 3 ], found |> List.map _.Line)

[<Fact>]
let ``ARC-BND-03 allows identifiers and construction labels`` () =
    let read name line = symbolUse "Lending.Host.Cli.Render" Field name line

    let uses =
        [ read "Lending.Semantic.Loan.LoanId" 1
          read "Lending.Semantic.Loan.DueDate" 2
          { read "Lending.Semantic.Loan.Renewals" 3 with IsRecordConstructionLabel = true }
          read "Lending.Application.Views.LoanView.Due" 4
          { read "Lending.Semantic.Loan.DueDate" 5 with Scope = "Lending.Host.Persistence.Json" } ]

    let found = Rules.entityFieldReads (instance "ARC-BND-03") (facts [ project host 4 [ file "r.fs" uses ] ])
    Assert.Equal<int list>([ 2 ], found |> List.map _.Line)

[<Fact>]
let ``ARC-TRC-01 needs a production comment and a test name or comment`` () =
    let prod =
        project sem 1 [ { file "a.fs" [] with Comments = [ { Span = span 1 0; Text = "// DEC-A and DEC-B" } ] } ]

    let test =
        { project tests 4 [ { file "t.fs" [] with BindingNames = [ "DEC-A works" ]; StringLiterals = [ "DEC-B" ] } ] with
            Role = Test
            Tier = None }

    let found = Rules.decisionTrace (instance "ARC-DEP-01") [ "DEC-A"; "DEC-B"; "DEC-C" ] (facts [ prod; test ])
    // DEC-B only in a test string literal: not a test citation. DEC-C nowhere.
    Assert.Equal<string list>([ "DEC-B"; "DEC-C"; "DEC-C" ], found |> List.map _.Symbol |> List.sort)

[<Fact>]
let ``ARC-HEU-02 reports occurrences above the lowest tier`` () =
    let lit v line = { Span = span line 0; Scope = "M"; Value = v }
    let a = project sem 1 [ { file "a.fs" [] with Literals = [ lit "21" 1; lit "7" 2 ] } ]
    let b = project app 3 [ { file "b.fs" [] with Literals = [ lit "21" 5; lit "1" 6 ] } ]
    let found = Heuristics.duplicatedFacts (instance "ARC-HEU-02") (facts [ a; b ])
    Assert.Equal<(string * int) list>([ "b.fs", 5 ], found |> List.map (fun f -> f.File, f.Line))
    Assert.All(found, fun f -> Assert.Equal(Heu, f.Class))

[<Fact>]
let ``HEU findings never fail the gate; DET severity 1 does not either`` () =
    let f cls sev = { Rules.finding (instance "ARC-HEU-01") "" "" 0 0 "" "" with Class = cls; Severity = sev }
    Assert.True(Report.pass [ f Heu 1; f Det 1 ])
    Assert.False(Report.pass [ f Det 2 ])

[<Fact>]
let ``consolidate merges a probe repeating the policy and sorts`` () =
    let base' = Rules.finding (instance "ARC-BND-03") "p" "b.fs" 3 1 "X" "m"
    let probe = { base' with Origins = [ "probe:0" ] }
    let other = { base' with File = "a.fs" }
    let merged = Report.consolidate [ probe; base'; other ]
    Assert.Equal<string list>([ "a.fs"; "b.fs" ], merged |> List.map _.File)
    Assert.Equal<string list>([ "policy"; "probe:0" ], merged[1].Origins)

[<Fact>]
let ``unmapped production projects are refused`` () =
    let p = lendingPolicy.Value
    Assert.True(Verify.classify p "src/Lending.Utilities/Lending.Utilities.fsproj" |> Result.isError)
    Assert.Equal(Ok(Test, None), Verify.classify p "tests/Lending.Tests/Lending.Tests.fsproj")
    Assert.Equal(Ok(Production, Some 2), Verify.classify p "src/Lending.Transition/Lending.Transition.fsproj")
