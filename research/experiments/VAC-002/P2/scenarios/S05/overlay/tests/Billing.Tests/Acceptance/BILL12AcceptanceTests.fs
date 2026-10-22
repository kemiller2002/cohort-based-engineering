module BILL12AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-12-R1 invoices add the region's tax`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c1: 100.00 + tax 13.00 = 113.00 due 2026-04-01", run w "invoice i1 c1 100.00")
    Assert.Equal("i2 issued to c3: 200.00 + tax 24.00 = 224.00 due 2026-04-01", run w "invoice i2 c3 200.00")

[<Fact>]
let ``BILL-12-R2 show and balance include the tax`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    Assert.Equal("i1 c1 amount 100.00, tax 13.00, late fee 0.00, paid 0.00, outstanding 113.00, due 2026-04-01", run w "show i1")
    Assert.Equal("c1 balance 113.00", run w "balance c1")
