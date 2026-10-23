module L03AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L03-R1 LEND-L03-R2 a loan is renewed and shown as renewed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-20"
    Assert.Equal("c1 renewed, due 2026-04-13 (renewal 1 of 2)", run w "renew c1")
    Assert.Equal("loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-04-13 (renewed 1)", run w "loans m1")

[<Fact>]
let ``LEND-L03-R1 an overdue loan cannot be renewed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-24"
    Assert.Equal("error: copy c1 is overdue", run w "renew c1")
