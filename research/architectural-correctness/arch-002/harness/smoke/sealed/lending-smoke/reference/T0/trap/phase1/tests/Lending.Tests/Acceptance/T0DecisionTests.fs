module T0DecisionTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``DEC-T0-FEE-RULE two days late is two daily fees`` () = Assert.Equal(50, Fees.lateFee 2)
