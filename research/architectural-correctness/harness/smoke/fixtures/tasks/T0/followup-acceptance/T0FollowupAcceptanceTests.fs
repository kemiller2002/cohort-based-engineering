module T0FollowupAcceptanceTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``T0 follow-up fee is capped at 500 cents`` () = Assert.Equal(500, Fees.lateFee 100)
