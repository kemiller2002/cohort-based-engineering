module V5AcceptanceTests

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let landlord = AccountId "landlord"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount landlord |> ok
    |> Ledger.credit cash 100m "salary" |> ok
let order id day value = { OrderId = id; Payer = cash; Payee = landlord; Value = value; DayOfMonth = day }

[<Fact>]
let ``LEDGER-V5-R1 an order without a value refuses the run`` () =
    Assert.Equal(Error(InvalidOrder "rent"), StandingOrders.run (DateOnly(2026, 1, 15)) [ order "rent" 15 0m ] (funded ()))

[<Fact>]
let ``LEDGER-V5-R2 a due order is paid and an order that is not due is not`` () =
    let outcomes, l = StandingOrders.run (DateOnly(2026, 1, 15)) [ order "rent" 15 40m; order "gym" 20 10m ] (funded ()) |> ok
    Assert.True((outcomes = [ Paid "rent" ]))
    Assert.Equal(Ok 60m, Ledger.balance cash l)
    Assert.Equal(Ok 40m, Ledger.balance landlord l)

[<Fact>]
let ``LEDGER-V5-R3 a second run for the same date pays nothing`` () =
    let date = DateOnly(2026, 1, 15)
    let _, once = StandingOrders.run date [ order "rent" 15 40m ] (funded ()) |> ok
    let outcomes, twice = StandingOrders.run date [ order "rent" 15 40m ] once |> ok
    Assert.True((outcomes = [ AlreadyPaid "rent" ]))
    Assert.Equal(Ok 60m, Ledger.balance cash twice)
