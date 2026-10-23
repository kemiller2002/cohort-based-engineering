module BILL42AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-42-R1 shipping charge by region`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("c1 shipping 15.00", run w "shipping c1")
    Assert.Equal("error: unknown customer c9", run w "shipping c9")

[<Fact>]
let ``BILL-42-R2 help lists shipping after balance`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "balance <customer>") lines + 1, List.findIndex ((=) "shipping <customer>") lines)
