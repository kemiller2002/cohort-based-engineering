module OracleV3

open Xunit
open Ledger

let cash = AccountId "cash"
let savings = AccountId "savings"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount savings |> ok
    |> Ledger.credit cash 100m "seed" |> ok

[<Fact>]
let ``LEDGER-V3-R1 placing a hold refuses in the stated order`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 30m |> ok
    Assert.Equal(Error(InvalidAmount 0m), Ledger.placeHold "h1" ghost 0m l)
    Assert.Equal(Error(InvalidAmount -2m), Ledger.placeHold "h9" cash -2m l)
    Assert.Equal(Error(UnknownAccount ghost), Ledger.placeHold "h1" ghost 5m l)
    Assert.Equal(Error(DuplicateHold "h1"), Ledger.placeHold "h1" savings 500m l)

[<Fact>]
let ``LEDGER-V3-R1 a hold cannot exceed the available amount`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 30m |> ok |> Ledger.placeHold "h2" cash 30m |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 41m)), Ledger.placeHold "h3" cash 41m l)
    let all = Ledger.placeHold "h3" cash 40m l |> ok
    Assert.Equal(Ok 0m, Ledger.available cash all)

[<Fact>]
let ``LEDGER-V3-R1 releasing restores the available amount and frees the id`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 30m |> ok |> Ledger.releaseHold "h1" |> ok
    Assert.Equal(Ok 100m, Ledger.available cash l)
    Assert.Equal(Error(UnknownHold "h1"), Ledger.releaseHold "h1" l)
    let again = Ledger.placeHold "h1" cash 60m l |> ok
    Assert.Equal(Ok 40m, Ledger.available cash again)

[<Fact>]
let ``LEDGER-V3-R1 releasing an unknown hold is refused`` () =
    Assert.Equal(Error(UnknownHold "nope"), Ledger.releaseHold "nope" (funded ()))

[<Fact>]
let ``LEDGER-V3-R1 holds record no postings and keep the balance`` () =
    let start = funded ()
    let held = start |> Ledger.placeHold "h1" cash 30m |> ok
    let released = held |> Ledger.releaseHold "h1" |> ok
    Assert.True((Ledger.postings held = Ledger.postings start))
    Assert.True((Ledger.postings released = Ledger.postings start))
    Assert.Equal(Ok 100m, Ledger.balance cash held)

[<Fact>]
let ``LEDGER-V3-R1 the available amount of an unknown account is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.available ghost (funded ()))

[<Fact>]
let ``LEDGER-V3-R2 held money cannot be transferred`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 30m |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 80m)), Ledger.transfer cash savings 80m "t" l)
    let moved = Ledger.transfer cash savings 70m "t" l |> ok
    Assert.Equal(Ok 30m, Ledger.balance cash moved)
    Assert.Equal(Ok 0m, Ledger.available cash moved)

[<Fact>]
let ``LEDGER-V3-R2 the whole available amount can be debited`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 30m |> ok |> Ledger.debit cash 70m "atm" |> ok
    Assert.Equal(Ok 30m, Ledger.balance cash l)
    Assert.Equal(Error(InsufficientFunds(cash, 0.01m)), Ledger.debit cash 0.01m "atm" l)

[<Fact>]
let ``LEDGER-V3-R2 holds on another account do not block`` () =
    let l = funded () |> Ledger.transfer cash savings 50m "t" |> ok |> Ledger.placeHold "h1" savings 50m |> ok
    let spent = Ledger.debit cash 50m "atm" l |> ok
    Assert.Equal(Ok 0m, Ledger.balance cash spent)
    Assert.Equal(Error(InsufficientFunds(savings, 1m)), Ledger.transfer savings cash 1m "t" l)

[<Fact>]
let ``LEDGER-V3-R2 the other refusals keep their order`` () =
    let l = funded () |> Ledger.placeHold "h1" cash 90m |> ok
    Assert.Equal(Error(InvalidAmount 0m), Ledger.transfer cash savings 0m "t" l)
    Assert.Equal(Error(UnknownAccount ghost), Ledger.transfer cash ghost 50m "t" l)
    Assert.Equal(Error(SameAccount cash), Ledger.transfer cash cash 50m "t" l)
    Assert.Equal(Error(InvalidAmount -1m), Ledger.debit cash -1m "d" l)

[<Fact>]
let ``LEDGER-V3-R2 the period fee still depends on the balance`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 1m "seed" |> ok |> Ledger.placeHold "h1" cash 1m |> ok
    let summary, closed = Ledger.closePeriod "P1" l |> ok
    Assert.Equal(1m, summary.Fees.[cash])
    Assert.Equal(Ok 0m, Ledger.balance cash closed)
