module T3FollowupAcceptanceTests

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
let ``LEND-T3-F2 a row that would overfill its branch is skipped`` () =
    let w = world "2026-03-02"

    withCsv
        [ "book,isbn,title,author,copies,branch"
          "b1,9780441013593,Dune,Frank Herbert,3,east"
          "b2,9780141439587,Emma,Jane Austen,2,east"
          "b3,9780000000003,Three,Someone,2,main" ]
        (fun path ->
            Assert.Equal("imported 2 books, 5 copies\n  line 3: skipped: branch east has room for 1 more copies", run w $"import {path}"))
