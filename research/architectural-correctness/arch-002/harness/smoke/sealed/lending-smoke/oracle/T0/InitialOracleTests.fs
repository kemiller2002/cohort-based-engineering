module InitialOracleTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``R1 zero days late costs nothing`` () = Assert.Equal(0, Fees.lateFee 0)

[<Fact>]
let ``R1 negative days late cost nothing`` () = Assert.Equal(0, Fees.lateFee -2)

[<Fact>]
let ``R1 Regression one day late costs the daily fee`` () = Assert.Equal(25, Fees.lateFee 1)

[<Fact>]
let ``R1 DEC-T0-FEE-RULE ten days late is ten daily fees`` () = Assert.Equal(10 * Fees.dailyLateFeeCents, Fees.lateFee 10)
