module FollowupOracleTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``R2 the cap is 500 cents`` () = Assert.Equal(500, Fees.maxLateFeeCents)

[<Fact>]
let ``R2 DEC-T0-FEE-CAP the cap applies from day 21`` () = Assert.Equal(500, Fees.lateFee 21)

[<Fact>]
let ``R2 below the cap the fee is unchanged`` () = Assert.Equal(475, Fees.lateFee 19)
