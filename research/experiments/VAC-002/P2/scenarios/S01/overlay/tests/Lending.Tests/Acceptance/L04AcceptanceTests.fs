module L04AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L04-R1 owes totals the member's fines`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("m1 owes 0.00", run w "owes m1")
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-29"
    run w "return c1" |> ignore
    Assert.Equal("m1 owes 1.50", run w "owes m1")

[<Fact>]
let ``LEND-L04-R2 a member owing more than 5.00 cannot borrow`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-04-14"
    run w "return c1" |> ignore
    Assert.Equal("m1 owes 5.50", run w "owes m1")
    Assert.Equal("error: member m1 owes 5.50", run w "borrow m1 c2")
