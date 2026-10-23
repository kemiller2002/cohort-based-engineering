/// A dependency-free, source-compatible stand-in for the subset of xUnit these repositories use
/// (`[<Fact>]`, `Assert.Equal/True/False/Contains/DoesNotContain/StartsWith/EndsWith/Throws`).
/// `dotnet test` runs it through the `VSTest` target in `Directory.Build.targets`; results are written as a .trx file.
namespace Xunit

open System

[<AttributeUsage(AttributeTargets.Method, AllowMultiple = false)>]
type FactAttribute() =
    inherit Attribute()
    member val Skip: string = null with get, set
    member val DisplayName: string = null with get, set

exception AssertFailure of string

[<AbstractClass; Sealed>]
type Assert private () =
    static let fail (message: string) = raise (AssertFailure message)
    static let show (x: obj) =
        match x with
        | null -> "null"
        | :? string as s -> "\"" + s + "\""
        | _ -> sprintf "%A" x

    static member Equal<'T when 'T: equality>(expected: 'T, actual: 'T) : unit =
        if expected <> actual then
            fail (sprintf "Assert.Equal() Failure\nExpected: %s\nActual:   %s" (show (box expected)) (show (box actual)))

    static member NotEqual<'T when 'T: equality>(expected: 'T, actual: 'T) : unit =
        if expected = actual then fail (sprintf "Assert.NotEqual() Failure\nBoth: %s" (show (box actual)))

    static member True(condition: bool) : unit = if not condition then fail "Assert.True() Failure"
    static member True(condition: bool, userMessage: string) : unit = if not condition then fail ("Assert.True() Failure: " + userMessage)
    static member False(condition: bool) : unit = if condition then fail "Assert.False() Failure"
    static member False(condition: bool, userMessage: string) : unit = if condition then fail ("Assert.False() Failure: " + userMessage)

    static member Contains(expectedSubstring: string, actualString: string) : unit =
        if isNull actualString || not (actualString.Contains expectedSubstring) then
            fail (sprintf "Assert.Contains() Failure\nNot found: %s\nIn value:  %s" (show expectedSubstring) (show actualString))

    static member DoesNotContain(expectedSubstring: string, actualString: string) : unit =
        if not (isNull actualString) && actualString.Contains expectedSubstring then
            fail (sprintf "Assert.DoesNotContain() Failure\nFound:    %s\nIn value: %s" (show expectedSubstring) (show actualString))

    static member Contains<'T when 'T: equality>(expected: 'T, collection: seq<'T>) : unit =
        if not (Seq.contains expected collection) then
            fail (sprintf "Assert.Contains() Failure\nNot found: %s" (show (box expected)))

    static member StartsWith(expectedStartString: string, actualString: string) : unit =
        if isNull actualString || not (actualString.StartsWith(expectedStartString, StringComparison.Ordinal)) then
            fail (sprintf "Assert.StartsWith() Failure\nExpected start: %s\nActual:         %s" (show expectedStartString) (show actualString))

    static member EndsWith(expectedEndString: string, actualString: string) : unit =
        if isNull actualString || not (actualString.EndsWith(expectedEndString, StringComparison.Ordinal)) then
            fail (sprintf "Assert.EndsWith() Failure\nExpected end: %s\nActual:       %s" (show expectedEndString) (show actualString))

    static member Empty(collection: seq<'T>) : unit = if not (Seq.isEmpty collection) then fail "Assert.Empty() Failure"
    static member NotEmpty(collection: seq<'T>) : unit = if Seq.isEmpty collection then fail "Assert.NotEmpty() Failure"

    static member Throws<'E when 'E :> exn>(testCode: Action) : 'E =
        try
            testCode.Invoke()
            fail (sprintf "Assert.Throws() Failure: no exception was thrown (expected %s)" typeof<'E>.Name)
        with
        | :? 'E as e -> e
        | AssertFailure _ as e -> raise e
        | e -> fail (sprintf "Assert.Throws() Failure: expected %s, got %s: %s" typeof<'E>.Name (e.GetType().Name) e.Message)

/// Discovers `[<Fact>]` methods by reflection, runs them, prints a summary and writes a .trx file.
module Runner =
    open System.IO
    open System.Reflection
    open System.Xml.Linq

    type Outcome =
        | Passed
        | Failed of message: string
        | Skipped of reason: string

    type Result = { Name: string; Outcome: Outcome; Duration: TimeSpan }

    let private facts (assembly: Assembly) =
        assembly.GetTypes()
        |> Array.collect (fun t -> t.GetMethods(BindingFlags.Public ||| BindingFlags.Static ||| BindingFlags.Instance ||| BindingFlags.DeclaredOnly))
        |> Array.choose (fun m -> m.GetCustomAttribute<FactAttribute>() |> Option.ofObj |> Option.map (fun a -> m, a))
        |> Array.sortBy (fun (m, _) -> m.DeclaringType.FullName, m.MetadataToken)
        |> Array.toList

    let rec private unwrap (e: exn) =
        match e with
        | :? TargetInvocationException as t when not (isNull t.InnerException) -> unwrap t.InnerException
        | :? AggregateException as a when a.InnerExceptions.Count = 1 -> unwrap a.InnerExceptions.[0]
        | e -> e

    let private run (m: MethodInfo, a: FactAttribute) =
        let name = m.DeclaringType.FullName.Replace('+', '.') + "." + m.Name
        let started = Diagnostics.Stopwatch.StartNew()
        let outcome =
            if not (String.IsNullOrEmpty a.Skip) then Skipped a.Skip
            else
                try
                    let target = if m.IsStatic then null else Activator.CreateInstance m.DeclaringType
                    match m.Invoke(target, [||]) with
                    | :? Threading.Tasks.Task as t -> t.GetAwaiter().GetResult()
                    | _ -> ()
                    Passed
                with e ->
                    match unwrap e with
                    | AssertFailure msg -> Failed msg
                    | inner -> Failed(sprintf "%s: %s\n%s" (inner.GetType().FullName) inner.Message inner.StackTrace)
        { Name = name; Outcome = outcome; Duration = started.Elapsed }

    let private trx (results: Result list) (path: string) =
        let ns = XNamespace.Get "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"
        let el (n: string) (content: obj list) = XElement(ns + n, content |> List.toArray)
        let at (n: string) (v: obj) = XAttribute(XName.Get n, v) :> obj
        let outcomeName = function Passed -> "Passed" | Failed _ -> "Failed" | Skipped _ -> "NotExecuted"
        let ids = results |> List.map (fun _ -> Guid.NewGuid(), Guid.NewGuid())
        let unitResults =
            List.zip results ids
            |> List.map (fun (r, (testId, execId)) ->
                let message =
                    match r.Outcome with
                    | Failed m -> [ el "Output" [ el "ErrorInfo" [ el "Message" [ box m ] ] ] |> box ]
                    | Skipped m -> [ el "Output" [ el "StdOut" [ box m ] ] |> box ]
                    | Passed -> []
                el "UnitTestResult" ([ at "testId" testId; at "executionId" execId; at "testName" r.Name
                                       at "outcome" (outcomeName r.Outcome); at "duration" (r.Duration.ToString "c") ] @ message) |> box)
        let definitions =
            List.zip results ids
            |> List.map (fun (r, (testId, execId)) -> el "UnitTest" [ at "name" r.Name; at "id" testId; el "Execution" [ at "id" execId ] ] |> box)
        let count o = results |> List.filter (fun r -> outcomeName r.Outcome = o) |> List.length
        let doc =
            el "TestRun" [ at "id" (Guid.NewGuid()); at "name" "TestKit"
                           el "Results" unitResults
                           el "TestDefinitions" definitions
                           el "ResultSummary" [ at "outcome" (if count "Failed" = 0 then "Completed" else "Failed")
                                                el "Counters" [ at "total" (List.length results); at "executed" (List.length results - count "NotExecuted")
                                                                at "passed" (count "Passed"); at "failed" (count "Failed") ] ] ]
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath path)) |> ignore
        XDocument(doc).Save path

    let private argValue (key: string) (args: string list) =
        args |> List.pairwise |> List.tryPick (fun (k, v) -> if k = key then Some v else None)

    let main (assembly: Assembly) (argv: string[]) =
        let args = Array.toList argv
        let filter = argValue "--filter" args |> Option.defaultValue ""
        let results = facts assembly |> List.filter (fun (m, _) -> m.Name.Contains filter || m.DeclaringType.Name.Contains filter) |> List.map run
        results
        |> List.iter (fun r ->
            match r.Outcome with
            | Passed -> ()
            | Skipped why -> printfn "  Skipped %s: %s" r.Name why
            | Failed msg -> printfn "  Failed %s\n    %s" r.Name (msg.Replace("\n", "\n    ")))
        let failed = results |> List.filter (fun r -> match r.Outcome with Failed _ -> true | _ -> false) |> List.length
        let passed = results |> List.filter (fun r -> r.Outcome = Passed) |> List.length
        let skipped = List.length results - failed - passed
        printfn "%s - Failed: %d, Passed: %d, Skipped: %d, Total: %d - %s"
            (if failed = 0 then "Passed!" else "Failed!") failed passed skipped (List.length results) (assembly.GetName().Name)
        argValue "--trx" args |> Option.iter (trx results)
        if failed = 0 then 0 else 1
