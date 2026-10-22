module L05AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L05-R1 LEND-L05-R3 a payment reduces what is owed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-29"
    run w "return c1" |> ignore
    Assert.Equal("m1 paid 1.00, owes 0.50", run w "pay m1 1")
    Assert.Equal("fines for m1:\n  c1 2026-03-29 1.50, paid 1.00", run w "fines m1")
    Assert.Equal("error: m1 owes only 0.50", run w "pay m1 0.75")
    Assert.Equal("m1 owes 0.50", run w "owes m1")
