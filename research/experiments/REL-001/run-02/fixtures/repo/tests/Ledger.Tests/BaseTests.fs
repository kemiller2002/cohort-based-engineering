module BaseTests

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let savings = AccountId "savings"

let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount savings |> ok

[<Fact>]
let ``opening an account twice is refused`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok
    Assert.Equal(Error(DuplicateAccount cash), Ledger.openAccount cash l)

[<Fact>]
let ``credit then debit leaves the difference`` () =
    let l = opened () |> Ledger.credit cash 10m "c1" |> ok |> Ledger.debit cash 4m "d1" |> ok
    Assert.Equal(Ok 6m, Ledger.balance cash l)

[<Fact>]
let ``debit beyond balance is refused`` () =
    let l = opened () |> Ledger.credit cash 3m "c1" |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 5m)), Ledger.debit cash 5m "d1" l)

[<Fact>]
let ``non-positive amounts are refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.credit cash 0m "c" (opened ()))
    Assert.Equal(Error(InvalidAmount -1m), Ledger.debit cash -1m "d" (opened ()))

[<Fact>]
let ``postings are stamped with the business date`` () =
    let day = DateOnly(2026, 3, 15)
    let l = opened () |> Ledger.setDate day |> ok |> Ledger.credit cash 5m "c1" |> ok
    Assert.Equal<Posting list>([ { Account = cash; Amount = 5m; Reference = "c1"; Date = day } ], Ledger.postings l)

[<Fact>]
let ``the business date never moves backwards`` () =
    let l = opened () |> Ledger.setDate (DateOnly(2026, 2, 1)) |> ok
    Assert.Equal(Error(DateInPast(DateOnly(2026, 1, 31))), Ledger.setDate (DateOnly(2026, 1, 31)) l)

[<Fact>]
let ``postingsOf lists one account newest first`` () =
    let l = opened () |> Ledger.credit cash 1m "a" |> ok |> Ledger.credit savings 2m "b" |> ok |> Ledger.credit cash 3m "c" |> ok
    Assert.Equal<string list>([ "c"; "a" ], Ledger.postingsOf cash l |> List.map (fun p -> p.Reference))

[<Fact>]
let ``transfer moves money and refuses overdrafts`` () =
    let l = opened () |> Ledger.credit cash 10m "seed" |> ok
    let l2 = Ledger.transfer cash savings 4m "t1" l |> ok
    Assert.Equal(Ok 6m, Ledger.balance cash l2)
    Assert.Equal(Ok 4m, Ledger.balance savings l2)
    Assert.Equal(Error(InsufficientFunds(cash, 11m)), Ledger.transfer cash savings 11m "t2" l)
    Assert.Equal(Error(SameAccount cash), Ledger.transfer cash cash 1m "t3" l)

[<Fact>]
let ``closing a period charges the fee once`` () =
    let l = opened () |> Ledger.credit cash 5m "seed" |> ok
    let s, l2 = Ledger.closePeriod "P1" l |> ok
    Assert.Equal(1m, s.Fees[cash])
    Assert.Equal(0m, s.Fees[savings])
    Assert.Equal(Ok 4m, Ledger.balance cash l2)
    let s2, l3 = Ledger.closePeriod "P1" l2 |> ok
    Assert.Equal(s, s2)
    Assert.Equal(Ok 4m, Ledger.balance cash l3)

[<Fact>]
let ``the store commits successful operations only`` () =
    let store = Store.create (opened ())
    Store.credit cash 10m "seed" store |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 20m)), Store.transfer cash savings 20m "t" store)
    Store.transfer cash savings 4m "t" store |> ok
    Assert.Equal(Ok 6m, Ledger.balance cash (Store.current store))
    Assert.Equal(Ok 4m, Ledger.balance savings (Store.current store))
    Assert.Equal(Ok 6m, Store.balance cash store)
    Assert.Equal(Ok 4m, Store.balance savings store)

[<Fact>]
let ``the store's balance cache follows every operation`` () =
    let store = Store.create (opened () |> Ledger.credit cash 3m "seed" |> ok)
    Assert.Equal(Ok 3m, Store.balance cash store)
    Store.openAccount (AccountId "new") store |> ok
    Store.credit (AccountId "new") 2m "c" store |> ok
    Store.debit cash 1m "d" store |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 5m)), Store.debit cash 5m "d" store)
    Assert.Equal(Ok 2m, Store.balance (AccountId "new") store)
    Assert.Equal(Ok 2m, Store.balance cash store)
    Assert.Equal(Error(UnknownAccount(AccountId "ghost")), Store.balance (AccountId "ghost") store)
