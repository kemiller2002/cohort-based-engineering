module OracleV8

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let savings = AccountId "savings"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let holding amount =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount savings |> ok
    |> Ledger.credit cash amount "salary" |> ok
let withdrawals amounts l = amounts |> List.fold (fun s a -> Ledger.withdraw cash a s |> ok) l

[<Fact>]
let ``LEDGER-V8-R1 refusals come in the stated order`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.withdraw ghost 0m (holding 1000m))
    Assert.Equal(Error(InvalidAmount -5m), Ledger.withdraw cash -5m (holding 1000m))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.withdraw ghost 5m (holding 1000m))
    Assert.Equal(Error(InsufficientFunds(cash, 600m)), Ledger.withdraw cash 600m (holding 300m))

[<Fact>]
let ``LEDGER-V8-R1 the limit counts the day's earlier withdrawals`` () =
    let l = holding 1000m |> withdrawals [ 450m ]
    Assert.Equal(Error(DailyLimitExceeded(cash, 50m)), Ledger.withdraw cash 60m l)

[<Fact>]
let ``LEDGER-V8-R1 the limit is inclusive`` () =
    let l = holding 1000m |> withdrawals [ 450m; 50m ]
    Assert.Equal(Ok 500m, Ledger.balance cash l)
    Assert.Equal(Error(DailyLimitExceeded(cash, 0m)), Ledger.withdraw cash 0.01m l)

[<Fact>]
let ``LEDGER-V8-R1 a single withdrawal of exactly the limit is allowed`` () =
    let l = holding 1000m |> withdrawals [ 500m ]
    Assert.Equal(Ok 500m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V8-R1 refused withdrawals do not count`` () =
    let l = holding 1000m |> withdrawals [ 450m ]
    Assert.True(match Ledger.withdraw cash 60m l with Error _ -> true | Ok _ -> false)
    let after = l |> withdrawals [ 50m ]
    Assert.Equal(Ok 500m, Ledger.balance cash after)

[<Fact>]
let ``LEDGER-V8-R1 debits and transfers do not count`` () =
    let l = holding 2000m |> Ledger.debit cash 400m "card" |> ok |> Ledger.transfer cash savings 300m "save" |> ok
    let after = l |> withdrawals [ 500m ]
    Assert.Equal(Ok 800m, Ledger.balance cash after)

[<Fact>]
let ``LEDGER-V8-R1 the limit starts again on a new business date`` () =
    let l = holding 1000m |> withdrawals [ 500m ] |> Ledger.setDate (DateOnly(2026, 1, 2)) |> ok |> withdrawals [ 500m ]
    Assert.Equal(Ok 0m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V8-R1 a withdrawal is one dated posting`` () =
    let start = holding 1000m |> Ledger.setDate (DateOnly(2026, 2, 3)) |> ok
    let l = Ledger.withdraw cash 120.5m start |> ok
    let added = Ledger.postings l |> List.skip (List.length (Ledger.postings start))
    Assert.True((added = [ { Account = cash; Amount = -120.5m; Reference = "withdraw"; Date = DateOnly(2026, 2, 3) } ]))

[<Fact>]
let ``LEDGER-V8-R2 the day's withdrawals are summed`` () =
    let l = holding 1000m |> withdrawals [ 120.5m; 30m ]
    Assert.Equal(Ok 150.5m, Ledger.withdrawnToday cash l)

[<Fact>]
let ``LEDGER-V8-R2 a new business date starts from zero`` () =
    let l = holding 1000m |> withdrawals [ 100m ] |> Ledger.setDate (DateOnly(2026, 1, 2)) |> ok
    Assert.Equal(Ok 0m, Ledger.withdrawnToday cash l)

[<Fact>]
let ``LEDGER-V8-R2 debits are not withdrawals`` () =
    let l = holding 1000m |> Ledger.debit cash 50m "card" |> ok
    Assert.Equal(Ok 0m, Ledger.withdrawnToday cash l)

[<Fact>]
let ``LEDGER-V8-R2 an unknown account is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.withdrawnToday ghost (holding 10m))
