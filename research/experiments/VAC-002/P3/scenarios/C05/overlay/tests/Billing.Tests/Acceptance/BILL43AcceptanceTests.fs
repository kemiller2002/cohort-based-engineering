module BILL43AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-43-R1 interest is charged once, more than 60 days after the due date`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 300.00" |> ignore
    w.SetToday "2026-05-31"
    Assert.Equal("interest charged: 0", run w "run-interest")
    w.SetToday "2026-06-01"
    Assert.Equal("interest charged: 1", run w "run-interest")
    Assert.Equal("interest charged: 0", run w "run-interest")
    Assert.Equal("c1 balance 303.00", run w "balance c1")

[<Fact>]
let ``BILL-43-R2 help lists run-interest after run-late-fees`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "run-late-fees") lines + 1, List.findIndex ((=) "run-interest") lines)
