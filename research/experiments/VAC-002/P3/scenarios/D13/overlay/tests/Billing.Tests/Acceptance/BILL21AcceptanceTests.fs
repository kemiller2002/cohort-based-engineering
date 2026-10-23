module BILL21AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-21-R1 premium customers get their discount`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c3: 100.00 - discount 5.00 = 95.00 due 2026-04-01", run w "invoice i1 c3 100.00")

[<Fact>]
let ``BILL-21-R1 nonprofit customers get their discount`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c2: 100.00 - discount 10.00 = 90.00 due 2026-04-01", run w "invoice i1 c2 100.00")

[<Fact>]
let ``BILL-21-R1 customers without a discount are invoiced as before`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c1: 100.00 due 2026-04-01", run w "invoice i1 c1 100.00")

[<Fact>]
let ``BILL-21-R2 show uses the amount invoiced`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c3 100.00" |> ignore
    Assert.Equal("i1 c3 amount 95.00, late fee 0.00, paid 0.00, outstanding 95.00, due 2026-04-01", run w "show i1")
