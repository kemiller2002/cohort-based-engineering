module T7AcceptanceTests

open Xunit
open Lending.Host.Cli
open Support

[<Fact>]
let ``LEND-T7-R2 a line parses into a command`` () =
    Assert.Equal(Ok(Command.Borrow("m1", "c1")), Parse.command "borrow m1 c1")
    Assert.Equal(Ok(Command.AddBook("b1", "9780441013593", "Dune", "Frank Herbert")), Parse.command "add-book b1 9780441013593 Dune \"Frank Herbert\"")
    Assert.Equal(Error "usage: borrow <member> <copy>", Parse.command "borrow m1")

[<Fact>]
let ``LEND-T7-R3 run behaves as before`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("c1 lent to m1, due 2026-03-23", run w "borrow m1 c1")
    Assert.Equal("error: copy c1 is already on loan", run w "borrow s1 c1")
    Assert.Equal("loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-03-23", run w "loans m1")
