module T0AcceptanceTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``T0 three days late costs 75 cents`` () = Assert.Equal(75, Fees.lateFee 3)
