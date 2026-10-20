module OracleV6

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let other = AccountId "other"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let day d = DateOnly(2026, 1, d)
let line d value memo = { BookedOn = day d; Value = value; Memo = memo }
/// Deposits on cash: (day, amount, reference), in journal order.
let deposits (entries: (int * decimal * string) list) =
    entries
    |> List.fold
        (fun l (d, amount, reference) -> l |> Ledger.setDate (day d) |> ok |> Ledger.credit cash amount reference |> ok)
        (Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount other |> ok)
let reconcile lines l = Reconciliation.reconcile cash lines l |> ok
let pairs (r: ReconciliationReport) = r.Matched |> List.map (fun (p, l) -> p.Date.Day, l.BookedOn.Day)

[<Fact>]
let ``LEDGER-V6-R1 an unknown account is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Reconciliation.reconcile ghost [ line 1 5m "x" ] (deposits [ (1, 5m, "x") ]))

[<Fact>]
let ``LEDGER-V6-R1 only the account's own postings are considered`` () =
    let l = deposits [ (2, 10m, "dep") ] |> Ledger.credit other 10m "dep" |> ok
    let r = reconcile [ line 2 10m "dep"; line 2 10m "dep" ] l
    Assert.Equal(1, r.Matched.Length)
    Assert.True(r.Matched |> List.forall (fun (p, _) -> p.Account = cash))
    Assert.True(List.isEmpty r.LedgerOnly)
    Assert.Equal(1, r.BankOnly.Length)

[<Fact>]
let ``LEDGER-V6-R2 the date window is two days either way, inclusive`` () =
    let l = deposits [ (8, 30m, "dep") ]
    Assert.Equal(1, (reconcile [ line 10 30m "dep" ] l).Matched.Length)
    Assert.Equal(1, (reconcile [ line 6 30m "dep" ] l).Matched.Length)
    Assert.Equal(0, (reconcile [ line 11 30m "dep" ] l).Matched.Length)
    Assert.Equal(0, (reconcile [ line 5 30m "dep" ] l).Matched.Length)

[<Fact>]
let ``LEDGER-V6-R2 each line takes the closest posting`` () =
    let l = deposits [ (1, 30m, "dep"); (3, 30m, "dep") ]
    Assert.True((pairs (reconcile [ line 3 30m "dep"; line 1 30m "dep" ] l) = [ (3, 3); (1, 1) ]))

[<Fact>]
let ``LEDGER-V6-R2 equally close postings go to the earlier in journal order`` () =
    let l = deposits [ (1, 30m, "dep"); (3, 30m, "dep") ]
    let r = reconcile [ line 2 30m "dep" ] l
    Assert.True((pairs r = [ (1, 2) ]))
    Assert.True((r.LedgerOnly |> List.map (fun p -> p.Date.Day) = [ 3 ]))

[<Fact>]
let ``LEDGER-V6-R2 lines are matched one at a time in the order given`` () =
    let l = deposits [ (2, 30m, "dep") ]
    let r = reconcile [ line 4 30m "dep"; line 2 30m "dep" ] l
    Assert.True((pairs r = [ (2, 4) ]))
    Assert.True((r.BankOnly = [ line 2 30m "dep" ]))

[<Fact>]
let ``LEDGER-V6-R2 value and memo must be equal exactly`` () =
    let l = deposits [ (2, 30m, "Rent") ]
    let r = reconcile [ line 2 30m "rent"; line 2 (-30m) "Rent"; line 2 30.01m "Rent" ] l
    Assert.True(List.isEmpty r.Matched)
    Assert.Equal(3, r.BankOnly.Length)
    Assert.Equal(1, r.LedgerOnly.Length)

[<Fact>]
let ``LEDGER-V6-R2 a posting is matched at most once`` () =
    let l = deposits [ (2, 30m, "dep") ]
    let r = reconcile [ line 2 30m "dep"; line 2 30m "dep" ] l
    Assert.Equal(1, r.Matched.Length)
    Assert.True((r.BankOnly = [ line 2 30m "dep" ]))

[<Fact>]
let ``LEDGER-V6-R3 the three lists keep their stated orders`` () =
    let l = deposits [ (1, 10m, "a"); (2, 20m, "b"); (3, 30m, "c"); (4, 40m, "d") ]
    let r = reconcile [ line 9 99m "z"; line 4 40m "d"; line 9 98m "y"; line 2 20m "b" ] l
    Assert.True((r.Matched |> List.map (fun (p, l) -> p.Reference, l.Memo) = [ ("d", "d"); ("b", "b") ]))
    Assert.True((r.LedgerOnly |> List.map (fun p -> p.Reference) = [ "a"; "c" ]))
    Assert.True((r.BankOnly |> List.map (fun l -> l.Memo) = [ "z"; "y" ]))

[<Fact>]
let ``LEDGER-V6-R3 matched pairs carry the posting and the line`` () =
    let l = deposits [ (5, 12.5m, "dep") ]
    let r = reconcile [ line 6 12.5m "dep" ] l
    let p, matchedLine = List.exactlyOne r.Matched
    Assert.Equal(cash, p.Account)
    Assert.Equal(12.5m, p.Amount)
    Assert.Equal(day 5, p.Date)
    Assert.Equal(line 6 12.5m "dep", matchedLine)
