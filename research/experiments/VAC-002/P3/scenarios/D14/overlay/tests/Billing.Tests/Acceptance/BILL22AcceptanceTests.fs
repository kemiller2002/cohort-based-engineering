module BILL22AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-22-R1 terms for a standard customer`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("c1 pays within 30 days", run w "terms c1")
    Assert.Equal("error: unknown customer c9", run w "terms c9")

[<Fact>]
let ``BILL-22-R1 help lists terms after balance`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "balance <customer>") lines + 1, List.findIndex ((=) "terms <customer>") lines)
