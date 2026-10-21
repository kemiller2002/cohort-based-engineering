module T8FollowupAcceptanceTests

open Xunit
open Lending.Semantic
open Support

[<Fact>]
let ``LEND-T8-F1 an ISBN-10 is stored as its ISBN-13`` () =
    let w = world "2026-03-02"
    Assert.Equal("book b1 added: Dune by Herbert", run w "add-book b1 0-441-01359-7 Dune Herbert")
    Assert.Equal("9780441013593", w.Ports.Store.Load().Books[BookId "b1"].Isbn)
    Assert.Equal("error: invalid ISBN '0-441-01359-8'", run w "add-book b2 0-441-01359-8 Dune Herbert")
