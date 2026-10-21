module OracleU4

open Xunit
open Ledger

let cash = AccountId "cash"
let card = AccountId "card"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let refs (ps: Posting list) = ps |> List.map (fun p -> p.Reference)

/// cash: c1 +10, t1 -4 (transfer to card), c2 +5, d1 -3, c3 +1 ; card: t1 +4, k1 +2
let setup () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount card |> ok
    |> Ledger.credit cash 10m "c1" |> ok |> Ledger.transfer cash card 4m "t1" |> ok
    |> Ledger.credit cash 5m "c2" |> ok |> Ledger.credit card 2m "k1" |> ok
    |> Ledger.debit cash 3m "d1" |> ok |> Ledger.credit cash 1m "c3" |> ok

[<Fact>]
let ``LEDGER-U4-R1 count larger than history gives all postings`` () =
    Assert.Equal<string list>([ "c3"; "d1"; "c2"; "t1"; "c1" ], Ledger.recent cash 50 (setup ()) |> ok |> refs)

[<Fact>]
let ``LEDGER-U4-R1 zero and negative counts give nothing`` () =
    Assert.Empty(Ledger.recent cash 0 (setup ()) |> ok)
    Assert.Empty(Ledger.recent cash -2 (setup ()) |> ok)

[<Fact>]
let ``LEDGER-U4-R1 unknown account refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.recent ghost 3 (setup ()))

[<Fact>]
let ``LEDGER-U4-R1 recent agrees with postingsOf after reversals`` () =
    let l = setup () |> Ledger.reverse "c2" |> ok |> Ledger.reverse "d1" |> ok
    Assert.Equal<string list>([ "c3"; "t1" ], Ledger.recent cash 2 l |> ok |> refs)
    Assert.Equal<Posting list>(Ledger.postingsOf cash l, Ledger.recent cash 100 l |> ok)

[<Fact>]
let ``LEDGER-U4-R1 recent hides a reversed transfer on both accounts`` () =
    let l = setup () |> Ledger.reverse "t1" |> ok
    Assert.Equal<string list>([ "k1" ], Ledger.recent card 5 l |> ok |> refs)
    Assert.Equal<string list>([ "c3"; "d1"; "c2"; "c1" ], Ledger.recent cash 5 l |> ok |> refs)

[<Fact>]
let ``LEDGER-U4-R2 compensating postings in recording order`` () =
    let l0 = setup () |> Ledger.setDate (System.DateOnly(2026, 4, 1)) |> ok
    let l = Ledger.reverse "t1" l0 |> ok
    let added = Ledger.postings l |> List.skip (List.length (Ledger.postings l0))
    Assert.Equal<Posting list>(
        [ { Account = cash; Amount = 4m; Reference = "reversal:t1"; Date = System.DateOnly(2026, 4, 1) }
          { Account = card; Amount = -4m; Reference = "reversal:t1"; Date = System.DateOnly(2026, 4, 1) } ],
        added)

[<Fact>]
let ``LEDGER-U4-R2 balances after reversal`` () =
    let l = setup () |> Ledger.reverse "t1" |> ok
    Assert.Equal(Ok 13m, Ledger.balance cash l)
    Assert.Equal(Ok 2m, Ledger.balance card l)

[<Fact>]
let ``LEDGER-U4-R2 full journal keeps both`` () =
    let l0 = setup ()
    let l = Ledger.reverse "c2" l0 |> ok
    Assert.Equal(List.length (Ledger.postings l0) + 1, List.length (Ledger.postings l))
    Assert.Contains("c2", Ledger.postings l |> refs)
    Assert.Contains("reversal:c2", Ledger.postings l |> refs)
    Assert.DoesNotContain("c2", Ledger.postingsOf cash l |> refs)
    Assert.DoesNotContain("reversal:c2", Ledger.postingsOf cash l |> refs)

[<Fact>]
let ``LEDGER-U4-R2 refusals`` () =
    let l = setup () |> Ledger.reverse "c2" |> ok
    Assert.Equal(Error(UnknownReference "nope"), Ledger.reverse "nope" l)
    Assert.Equal(Error(UnknownReference "reversal:c2"), Ledger.reverse "reversal:c2" l)
    Assert.Equal(Error(AlreadyReversed "c2"), Ledger.reverse "c2" l)

[<Fact>]
let ``LEDGER-U4-R2 a closed period fee can be reversed`` () =
    let _, l0 = Ledger.closePeriod "P1" (setup ()) |> ok
    let l = Ledger.reverse "fee:P1" l0 |> ok
    Assert.Equal(Ok 9m, Ledger.balance cash l)
    Assert.Equal(Ok 6m, Ledger.balance card l)
