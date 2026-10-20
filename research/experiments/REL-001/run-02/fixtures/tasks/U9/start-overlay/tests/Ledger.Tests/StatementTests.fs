module StatementTests

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let d (m: int) (day: int) = DateOnly(2026, m, day)

[<Fact>]
let ``statement lists postings in the range with running balance`` () =
    let l =
        Ledger.empty |> Ledger.openAccount cash |> ok
        |> Ledger.setDate (d 2 1) |> ok |> Ledger.credit cash 10m "c1" |> ok
        |> Ledger.setDate (d 2 10) |> ok |> Ledger.debit cash 3m "d1" |> ok
    let lines = Ledger.statement cash (d 2 1) (d 2 28) l |> ok
    Assert.Equal<StatementLine list>(
        [ { Date = d 2 1; Reference = "c1"; Amount = 10m; Balance = 10m }
          { Date = d 2 10; Reference = "d1"; Amount = -3m; Balance = 7m } ],
        lines)
