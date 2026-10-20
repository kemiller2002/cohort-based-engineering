module BaseTests

open Xunit
open Ledger

let cash = AccountId "cash"

let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``opening an account twice is refused`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok
    Assert.Equal(Error(DuplicateAccount cash), Ledger.openAccount cash l)

[<Fact>]
let ``credit then debit leaves the difference`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 10m "c1" |> ok |> Ledger.debit cash 4m "d1" |> ok
    Assert.Equal(Ok 6m, Ledger.balance cash l)

[<Fact>]
let ``debit beyond balance is refused`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 3m "c1" |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 5m)), Ledger.debit cash 5m "d1" l)
