module BILL41AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-41-R1 quote format and refusals`` () =
    let w = seeded "2026-03-02"
    Assert.StartsWith("quote c1 100.00 payable by 2026-", run w "quote c1 100.00")
    Assert.Equal("error: unknown customer c9", run w "quote c9 100.00")
    Assert.Equal("error: invalid amount -3", run w "quote c1 -3")
    Assert.Equal("c1 balance 0.00", run w "balance c1")

[<Fact>]
let ``BILL-41-R2 help lists quote after invoice`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "invoice <invoice> <customer> <amount>") lines + 1, List.findIndex ((=) "quote <customer> <amount>") lines)
