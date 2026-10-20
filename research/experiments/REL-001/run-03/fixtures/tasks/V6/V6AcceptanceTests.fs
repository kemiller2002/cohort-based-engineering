module V6AcceptanceTests

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let day d = DateOnly(2026, 1, d)
let line d value memo = { BookedOn = day d; Value = value; Memo = memo }
let ledger () =
    Ledger.empty |> Ledger.openAccount cash |> ok
    |> Ledger.setDate (day 5) |> ok |> Ledger.credit cash 100m "salary" |> ok
    |> Ledger.setDate (day 8) |> ok |> Ledger.debit cash 30m "rent" |> ok

[<Fact>]
let ``LEDGER-V6-R1 an unknown account is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Reconciliation.reconcile ghost [] (ledger ()))

[<Fact>]
let ``LEDGER-V6-R2 lines match postings with the same value and memo`` () =
    let r = Reconciliation.reconcile cash [ line 6 100m "salary"; line 9 (-30m) "rent"; line 9 (-5m) "fee" ] (ledger ()) |> ok
    Assert.True((r.Matched |> List.map (fun (p, l) -> p.Reference, l.Memo) = [ ("salary", "salary"); ("rent", "rent") ]))
    Assert.True((r.BankOnly = [ line 9 (-5m) "fee" ]))
    Assert.True(List.isEmpty r.LedgerOnly)

[<Fact>]
let ``LEDGER-V6-R3 unmatched postings are listed in journal order`` () =
    let r = Reconciliation.reconcile cash [] (ledger ()) |> ok
    Assert.True((r.LedgerOnly |> List.map (fun p -> p.Reference) = [ "salary"; "rent" ]))
    Assert.True(List.isEmpty r.Matched)
    Assert.True(List.isEmpty r.BankOnly)
