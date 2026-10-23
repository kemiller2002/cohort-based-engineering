module BILL13AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-13-R1 a nonprofit on the standard plan gets the approved discount`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c2: 90.00 (discount 10.00) due 2026-04-01", run w "invoice i1 c2 100.00")
    Assert.Equal("i2 issued to c1: 100.00 due 2026-04-01", run w "invoice i2 c1 100.00")

[<Fact>]
let ``BILL-13-R2 the discounted amount is the invoice amount`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c2 100.00" |> ignore
    Assert.Equal("i1 c2 amount 90.00, late fee 0.00, paid 0.00, outstanding 90.00, due 2026-04-01", run w "show i1")
    Assert.Equal("c2 balance 90.00", run w "balance c2")
