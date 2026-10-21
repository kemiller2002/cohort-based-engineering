module T8AcceptanceTests

open Xunit
open Lending.Semantic
open Support

[<Fact>]
let ``LEND-T8-R1 an ISBN with a wrong check digit is refused`` () =
    let w = world "2026-03-02"
    Assert.Equal("error: invalid ISBN-13 '978-0-441-01359-4'", run w "add-book b1 978-0-441-01359-4 Dune Herbert")
    Assert.Equal("error: unknown book b1", run w "add-copy c1 b1")

[<Fact>]
let ``LEND-T8-R2 a valid ISBN is stored as 13 digits`` () =
    let w = world "2026-03-02"
    Assert.Equal("book b1 added: Dune by Herbert", run w "add-book b1 978-0-441-01359-3 Dune Herbert")
    Assert.Equal("9780441013593", w.Ports.Store.Load().Books[BookId "b1"].Isbn)
