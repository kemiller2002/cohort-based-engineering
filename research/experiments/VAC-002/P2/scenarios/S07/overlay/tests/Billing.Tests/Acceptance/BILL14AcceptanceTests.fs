module BILL14AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-14-R1 a credit reduces the balance`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    Assert.Equal("c1 credited 20.00, balance 80.00", run w "credit c1 20.00")
    Assert.Equal("c1 balance 80.00", run w "balance c1")

[<Fact>]
let ``BILL-14-R1 refusals`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("error: unknown customer c9", run w "credit c9 5.00")
    Assert.Equal("error: invalid amount x", run w "credit c1 x")
