module L01AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L01-R1 LEND-L01-R2 a suspended member cannot borrow until reinstated`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("m1 suspended: overdue", run w "suspend m1 overdue")
    Assert.Equal("error: member m1 is suspended", run w "borrow m1 c1")
    Assert.Equal("m1 reinstated", run w "reinstate m1")
    Assert.Equal("c1 lent to m1, due 2026-03-23", run w "borrow m1 c1")

[<Fact>]
let ``LEND-L01-R3 member shows the standing`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("m1 Ada Lovelace (standard), active", run w "member m1")
    run w "suspend m1 \"damaged books\"" |> ignore
    Assert.Equal("m1 Ada Lovelace (standard), suspended: damaged books", run w "member m1")
