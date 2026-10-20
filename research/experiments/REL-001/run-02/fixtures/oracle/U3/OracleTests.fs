module OracleU3

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let d = AccountId "d"
let e = AccountId "e"
let f = AccountId "f"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded (amount: decimal) ids =
    ids |> List.fold (fun l id -> l |> Ledger.openAccount id |> ok |> Ledger.credit id amount "seed" |> ok) Ledger.empty
let added (before: LedgerState) (after: LedgerState) =
    Ledger.postings after |> List.skip (List.length (Ledger.postings before))
let charged ids (before: LedgerState) after =
    let m = added before after |> List.map (fun p -> p.Account, -p.Amount)
    ids |> List.map (fun id -> m |> List.filter (fun (x, _) -> x = id) |> List.sumBy snd)

[<Fact>]
let ``LEDGER-U3-R2 uneven split remainder to the first account`` () =
    let l0 = funded 50m [ a; b; c ]
    let l = Ledger.chargeSharedFee 10m [ a; b; c ] "fee" l0 |> ok
    Assert.Equal<decimal list>([ 3.34m; 3.33m; 3.33m ], charged [ a; b; c ] l0 l)

[<Fact>]
let ``LEDGER-U3-R2 first in list order takes the remainder`` () =
    let l0 = funded 50m [ a; b; c ]
    let l = Ledger.chargeSharedFee 10m [ c; a; b ] "fee" l0 |> ok
    Assert.Equal<decimal list>([ 3.33m; 3.33m; 3.34m ], charged [ a; b; c ] l0 l)

[<Fact>]
let ``LEDGER-U3-R2 negative remainder`` () =
    let ids = [ a; b; c; d; e; f ]
    let l0 = funded 50m ids
    let l = Ledger.chargeSharedFee 100m ids "fee" l0 |> ok
    Assert.Equal<decimal list>([ 16.65m; 16.67m; 16.67m; 16.67m; 16.67m; 16.67m ], charged ids l0 l)

[<Fact>]
let ``LEDGER-U3-R2 banker's rounding at the half cent`` () =
    let l0 = funded 5m [ a; b ]
    // 0.05 / 2 = 0.025 -> 0.02 (half to even); remainder 0.01 to the first
    let l = Ledger.chargeSharedFee 0.05m [ a; b ] "fee" l0 |> ok
    Assert.Equal<decimal list>([ 0.03m; 0.02m ], charged [ a; b ] l0 l)
    // 0.25 / 2 = 0.125 -> 0.12; remainder 0.01 to the first
    let l2 = Ledger.chargeSharedFee 0.25m [ a; b ] "fee" l0 |> ok
    Assert.Equal<decimal list>([ 0.13m; 0.12m ], charged [ a; b ] l0 l2)
    // 0.27 / 2 = 0.135 -> 0.14; remainder -0.01 to the first
    let l3 = Ledger.chargeSharedFee 0.27m [ a; b ] "fee" l0 |> ok
    Assert.Equal<decimal list>([ 0.13m; 0.14m ], charged [ a; b ] l0 l3)

[<Fact>]
let ``LEDGER-U3-R2 shares sum exactly to the total`` () =
    for total in [ 0.01m; 0.07m; 1m; 10m; 33.33m; 100m; 123.45m; 999.99m ] do
        let l0 = funded 1000m [ a; b; c ]
        let l = Ledger.chargeSharedFee total [ a; b; c ] "fee" l0 |> ok
        Assert.Equal(total, charged [ a; b; c ] l0 l |> List.sum)
        Assert.All(added l0 l, fun p -> Assert.Equal(p.Amount, System.Math.Round(p.Amount, 2)))

[<Fact>]
let ``LEDGER-U3-R2 zero shares are not posted`` () =
    let l0 = funded 5m [ a; b; c ]
    // 0.02 / 3 = 0.00667 -> 0.01; first takes 0.02 - 0.03 -> 0.00 share
    let l = Ledger.chargeSharedFee 0.02m [ a; b; c ] "fee" l0 |> ok
    Assert.Equal<(AccountId * decimal) list>([ b, -0.01m; c, -0.01m ], added l0 l |> List.map (fun p -> p.Account, p.Amount))

[<Fact>]
let ``LEDGER-U3-R1 postings in list order with reference and date`` () =
    let l0 = funded 10m [ a; b ] |> Ledger.setDate (System.DateOnly(2026, 6, 30)) |> ok
    let l = Ledger.chargeSharedFee 1m [ b; a ] "fee:custody" l0 |> ok
    Assert.Equal<Posting list>(
        [ { Account = b; Amount = -0.5m; Reference = "fee:custody"; Date = System.DateOnly(2026, 6, 30) }
          { Account = a; Amount = -0.5m; Reference = "fee:custody"; Date = System.DateOnly(2026, 6, 30) } ],
        added l0 l)

[<Fact>]
let ``LEDGER-U3-R1 refusal order`` () =
    let l0 = funded 1m [ a; b ]
    Assert.Equal(Error(InvalidAmount -1m), Ledger.chargeSharedFee -1m [ ghost; a ] "fee" l0)
    Assert.Equal(Error(UnknownAccount ghost), Ledger.chargeSharedFee 100m [ a; ghost ] "fee" l0)
    Assert.Equal(Error(InsufficientFunds(a, 50m)), Ledger.chargeSharedFee 100m [ a; b ] "fee" l0)

[<Fact>]
let ``LEDGER-U3-R1 funds checked against the first account's larger share`` () =
    // 10 / 3: first share 3.34; a holds exactly 3.33, which covers the base share only
    let l0 = funded 3.33m [ a ] |> Ledger.openAccount b |> ok |> Ledger.credit b 5m "s" |> ok |> Ledger.openAccount c |> ok |> Ledger.credit c 5m "s" |> ok
    Assert.Equal(Error(InsufficientFunds(a, 3.34m)), Ledger.chargeSharedFee 10m [ a; b; c ] "fee" l0)
    let l1 = funded 3.34m [ a ] |> Ledger.openAccount b |> ok |> Ledger.credit b 3.33m "s" |> ok |> Ledger.openAccount c |> ok |> Ledger.credit c 5m "s" |> ok
    let l = Ledger.chargeSharedFee 10m [ a; b; c ] "fee" l1 |> ok
    Assert.Equal(Ok 0m, Ledger.balance a l)
    Assert.Equal(Ok 0m, Ledger.balance b l)

[<Fact>]
let ``LEDGER-U3-R1 a later account short of funds records nothing`` () =
    let l0 = funded 5m [ a; b ] |> Ledger.openAccount c |> ok
    Assert.Equal(Error(InsufficientFunds(c, 1m)), Ledger.chargeSharedFee 3m [ a; b; c ] "fee" l0)
