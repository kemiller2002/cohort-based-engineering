module BILL11AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-11-R1 partial and settling payments`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    Assert.Equal("i1 paid 40.00, outstanding 60.00", run w "pay i1 40.00")
    Assert.Equal("i1 paid 60.00, outstanding 0.00, settled", run w "pay i1 60.00")

[<Fact>]
let ``BILL-11-R1 overpayment and unknown invoice are refused`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    Assert.Equal("error: payment 120.00 exceeds outstanding 100.00", run w "pay i1 120.00")
    Assert.Equal("error: unknown invoice i9", run w "pay i9 10.00")

[<Fact>]
let ``BILL-11-R2 show and balance reflect payments`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    run w "pay i1 25.50" |> ignore
    Assert.Equal("i1 c1 amount 100.00, late fee 0.00, paid 25.50, outstanding 74.50, due 2026-04-01", run w "show i1")
    Assert.Equal("c1 balance 74.50", run w "balance c1")
