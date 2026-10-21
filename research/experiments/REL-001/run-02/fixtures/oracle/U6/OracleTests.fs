module OracleU6

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok
    |> Ledger.credit a 10m "seed" |> ok |> Ledger.credit b 10m "seed" |> ok
let frozenA () = setup () |> Ledger.freezeAccount a |> ok

[<Fact>]
let ``LEDGER-U6-R1 unknown account refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.freezeAccount ghost (setup ()))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.isFrozen ghost (setup ()))

[<Fact>]
let ``LEDGER-U6-R1 freezing is idempotent and only affects that account`` () =
    let l = frozenA () |> Ledger.freezeAccount a |> ok
    Assert.Equal(Ok true, Ledger.isFrozen a l)
    Assert.Equal(Ok false, Ledger.isFrozen b l)
    Assert.Equal(frozenA (), l)

[<Fact>]
let ``LEDGER-U6-R1 no posting and balances unchanged`` () =
    let l = frozenA ()
    Assert.Equal<Posting list>(Ledger.postings (setup ()), Ledger.postings l)
    Assert.Equal(Ok 10m, Ledger.balance a l)

[<Fact>]
let ``LEDGER-U6-R1 new accounts are not frozen`` () =
    let l = frozenA () |> Ledger.openAccount (AccountId "c") |> ok
    Assert.Equal(Ok false, Ledger.isFrozen (AccountId "c") l)

[<Fact>]
let ``LEDGER-U6-R2 debit check order`` () =
    let l = frozenA ()
    Assert.Equal(Error(InvalidAmount 0m), Ledger.debit a 0m "d" l)
    Assert.Equal(Error(AccountFrozen a), Ledger.debit a 1m "d" l)
    Assert.Equal(Error(AccountFrozen a), Ledger.debit a 100m "d" l)

[<Fact>]
let ``LEDGER-U6-R2 outgoing transfer refused with check order`` () =
    let l = frozenA ()
    Assert.Equal(Error(InvalidAmount -1m), Ledger.transfer a b -1m "t" l)
    Assert.Equal(Error(UnknownAccount ghost), Ledger.transfer a ghost 1m "t" l)
    Assert.Equal(Error(SameAccount a), Ledger.transfer a a 1m "t" l)
    Assert.Equal(Error(AccountFrozen a), Ledger.transfer a b 1m "t" l)
    Assert.Equal(Error(AccountFrozen a), Ledger.transfer a b 100m "t" l)

[<Fact>]
let ``LEDGER-U6-R2 frozen account still receives`` () =
    let l = frozenA () |> Ledger.credit a 5m "c" |> ok |> Ledger.transfer b a 4m "t" |> ok
    Assert.Equal(Ok 19m, Ledger.balance a l)
    Assert.Equal(Ok 6m, Ledger.balance b l)

[<Fact>]
let ``LEDGER-U6-R2 other accounts unaffected`` () =
    let l = frozenA () |> Ledger.debit b 1m "d" |> ok
    Assert.Equal(Ok 9m, Ledger.balance b l)
    Assert.Equal(Error(InsufficientFunds(b, 50m)), Ledger.debit b 50m "d" l)
