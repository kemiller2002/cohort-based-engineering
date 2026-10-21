module T3AcceptanceTests

open System.IO
open Xunit
open Support

let withCsv (lines: string list) (test: string -> unit) =
    let path = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv")

    try
        File.WriteAllLines(path, lines)
        test path
    finally
        File.Delete path

[<Fact>]
let ``LEND-T3-R1 LEND-T3-R2 a csv file adds books and their copies`` () =
    let w = world "2026-03-02"

    withCsv [ "book,isbn,title,author,copies"; "b1,9780441013593,Dune,Frank Herbert,2"; "b2,9780141439587,\"Emma, a novel\",Jane Austen,1" ] (fun path ->
        Assert.Equal("imported 2 books, 3 copies", run w $"import \"{path}\""))

    run w "add-member m1 standard Ada" |> ignore
    Assert.Equal("b1-2 lent to m1, due 2026-03-23", run w "borrow m1 b1-2")
    Assert.Equal("loans for m1 (Ada):\n  b1-2 \"Dune\" due 2026-03-23", run w "loans m1")

[<Fact>]
let ``LEND-T3-R3 skipped rows are reported`` () =
    let w = seeded "2026-03-02"

    withCsv [ "book,isbn,title,author,copies"; "b7,9780000000001,Seven,Someone,1"; "b1,9780441013593,Dune,Frank Herbert,2"; "b8,9780000000002,Eight,Someone,25" ] (fun path ->
        Assert.Equal(
            "imported 1 books, 1 copies\n  line 3: skipped: book b1 already exists\n  line 4: skipped: copies must be a whole number from 1 to 20",
            run w $"import {path}"
        ))
