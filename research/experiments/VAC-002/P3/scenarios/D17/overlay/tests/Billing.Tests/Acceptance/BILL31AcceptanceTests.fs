module BILL31AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-31-R1 preview states whether the invoice is overdue and charges nothing`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    Assert.EndsWith("(not yet due)", run w "fee-preview i1")
    w.SetToday "2026-04-02"
    Assert.EndsWith("(overdue)", run w "fee-preview i1")
    Assert.Equal("i1 c1 amount 100.00, late fee 0.00, paid 0.00, outstanding 100.00, due 2026-04-01", run w "show i1")
    Assert.Equal("error: unknown invoice i9", run w "fee-preview i9")

[<Fact>]
let ``BILL-31-R2 help lists fee-preview after run-late-fees`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "run-late-fees") lines + 1, List.findIndex ((=) "fee-preview <invoice>") lines)
