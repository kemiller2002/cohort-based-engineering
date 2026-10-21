module OracleU8

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let other = AccountId "other"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let d (m: int) (day: int) = DateOnly(2026, m, day)
let on date (l: LedgerState) = Ledger.setDate date l |> ok

/// cash: 1/10 +100 (open), 2/1 -10, 2/1 +5 (same day), other 2/1 +7, 2/15 -20, 3/1 +1
let setup () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount other |> ok
    |> on (d 1 10) |> Ledger.credit cash 100m "open" |> ok
    |> on (d 2 1) |> Ledger.debit cash 10m "a" |> ok |> Ledger.credit cash 5m "b" |> ok |> Ledger.credit other 7m "x" |> ok
    |> on (d 2 15) |> Ledger.debit cash 20m "c" |> ok
    |> on (d 3 1) |> Ledger.credit cash 1m "e" |> ok

let refs lines = lines |> List.map (fun (s: StatementLine) -> s.Reference)

[<Fact>]
let ``LEDGER-U8-R1 both ends inclusive`` () =
    Assert.Equal<string list>([ "a"; "b"; "c" ], Ledger.statement cash (d 2 1) (d 2 15) (setup ()) |> ok |> refs)

[<Fact>]
let ``LEDGER-U8-R1 single day range`` () =
    Assert.Equal<string list>([ "a"; "b" ], Ledger.statement cash (d 2 1) (d 2 1) (setup ()) |> ok |> refs)
    Assert.Equal<string list>([ "e" ], Ledger.statement cash (d 3 1) (d 3 1) (setup ()) |> ok |> refs)

[<Fact>]
let ``LEDGER-U8-R1 running balance counts postings before the range`` () =
    let lines = Ledger.statement cash (d 2 2) (d 3 31) (setup ()) |> ok
    Assert.Equal<StatementLine list>(
        [ { Date = d 2 15; Reference = "c"; Amount = -20m; Balance = 75m }
          { Date = d 3 1; Reference = "e"; Amount = 1m; Balance = 76m } ],
        lines)

[<Fact>]
let ``LEDGER-U8-R1 same-day postings in recording order with balances`` () =
    let lines = Ledger.statement cash (d 1 1) (d 2 1) (setup ()) |> ok
    Assert.Equal<StatementLine list>(
        [ { Date = d 1 10; Reference = "open"; Amount = 100m; Balance = 100m }
          { Date = d 2 1; Reference = "a"; Amount = -10m; Balance = 90m }
          { Date = d 2 1; Reference = "b"; Amount = 5m; Balance = 95m } ],
        lines)

[<Fact>]
let ``LEDGER-U8-R1 other accounts never appear`` () =
    let lines = Ledger.statement other (d 1 1) (d 12 31) (setup ()) |> ok
    Assert.Equal<StatementLine list>([ { Date = d 2 1; Reference = "x"; Amount = 7m; Balance = 7m } ], lines)

[<Fact>]
let ``LEDGER-U8-R1 empty range gives no lines`` () =
    Assert.Empty(Ledger.statement cash (d 2 2) (d 2 14) (setup ()) |> ok)
    Assert.Empty(Ledger.statement cash (d 4 1) (d 4 30) (setup ()) |> ok)

[<Fact>]
let ``LEDGER-U8-R1 inverted range refused`` () =
    Assert.Equal(Error(InvalidDateRange(d 2 2, d 2 1)), Ledger.statement cash (d 2 2) (d 2 1) (setup ()))

[<Fact>]
let ``LEDGER-U8-R1 unknown account refused, range checked first`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.statement ghost (d 1 1) (d 2 1) (setup ()))
    Assert.Equal(Error(InvalidDateRange(d 2 2, d 2 1)), Ledger.statement ghost (d 2 2) (d 2 1) (setup ()))
