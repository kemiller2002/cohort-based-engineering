module BaseTests

open Xunit
open Lending.Semantic

[<Fact>]
let ``daily late fee is 25 cents`` () = Assert.Equal(25, Fees.dailyLateFeeCents)
