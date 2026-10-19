module OracleT3

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok |> Ledger.openAccount c |> ok
    |> Ledger.credit a 5m "seed" |> ok |> Ledger.credit b 0.5m "seed" |> ok |> Ledger.credit c 1m "seed" |> ok

[<Fact>]
let ``LEDGER-T3-R1 fee charged at or above 1`` () =
    let s, l = Ledger.closePeriod "P1" (setup ()) |> ok
    Assert.Equal(Ok 4m, Ledger.balance a l)
    Assert.Equal(Ok 0.5m, Ledger.balance b l)
    Assert.Equal(Ok 0m, Ledger.balance c l)
    Assert.Equal("P1", s.PeriodId)
    Assert.Equal<Map<AccountId, decimal>>(Map [ a, 1m; b, 0m; c, 1m ], s.Fees)
    Assert.Equal<Map<AccountId, decimal>>(Map [ a, 4m; b, 0.5m; c, 0m ], s.Balances)

[<Fact>]
let ``LEDGER-T3-R1 fee posting shape`` () =
    let l0 = setup ()
    let _, l = Ledger.closePeriod "P1" l0 |> ok
    let added = Ledger.postings l |> List.skip (List.length (Ledger.postings l0))
    Assert.Equal(2, added.Length)
    Assert.All(added, fun p -> Assert.Equal(-1m, p.Amount); Assert.Equal("fee:P1", p.Reference))

[<Fact>]
let ``LEDGER-T3-R2 reclose is a no-op returning first summary`` () =
    let s1, l1 = Ledger.closePeriod "P1" (setup ()) |> ok
    let s2, l2 = Ledger.closePeriod "P1" l1 |> ok
    Assert.Equal(s1, s2)
    Assert.Equal<Posting list>(Ledger.postings l1, Ledger.postings l2)

[<Fact>]
let ``LEDGER-T3-R2 reclose after balance change keeps first summary`` () =
    // DEC-T3-IDEMPOTENCY-KEY: a close that charged nobody leaves no fee posting.
    let empty = Ledger.empty |> Ledger.openAccount a |> ok
    let s1, l1 = Ledger.closePeriod "P0" empty |> ok
    let l1b = l1 |> Ledger.credit a 7m "late" |> ok
    let s2, l2 = Ledger.closePeriod "P0" l1b |> ok
    Assert.Equal(s1, s2)
    Assert.Equal(Ok 7m, Ledger.balance a l2)

[<Fact>]
let ``LEDGER-T3-R2 a different period charges again`` () =
    let _, l1 = Ledger.closePeriod "P1" (setup ()) |> ok
    let s2, l2 = Ledger.closePeriod "P2" l1 |> ok
    Assert.Equal(Ok 3m, Ledger.balance a l2)
    Assert.Equal(1m, s2.Fees[a])
    Assert.Equal(0m, s2.Fees[c])
