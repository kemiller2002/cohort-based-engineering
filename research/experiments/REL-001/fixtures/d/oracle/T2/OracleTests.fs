module OracleT2

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok
    |> Ledger.credit a 10m "seed-a" |> ok |> Ledger.credit b 2m "seed-b" |> ok
let total l = [ a; b ] |> List.sumBy (fun id -> Ledger.balance id l |> ok)

[<Fact>]
let ``LEDGER-T2-R1 two postings with the reference`` () =
    let l = setup ()
    let l2 = Ledger.transfer a b 4m "t-1" l |> ok
    let added = Ledger.postings l2 |> List.skip (List.length (Ledger.postings l))
    Assert.Equal(2, added.Length)
    Assert.Contains({ Account = a; Amount = -4m; Reference = "t-1" }, added)
    Assert.Contains({ Account = b; Amount = 4m; Reference = "t-1" }, added)

[<Fact>]
let ``LEDGER-T2-R1 balances move`` () =
    let l2 = Ledger.transfer a b 10m "t" (setup ()) |> ok
    Assert.Equal(Ok 0m, Ledger.balance a l2)
    Assert.Equal(Ok 12m, Ledger.balance b l2)

[<Fact>]
let ``LEDGER-T2-R2 invalid amount first`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.transfer ghost ghost 0m "t" (setup ()))
    Assert.Equal(Error(InvalidAmount -1m), Ledger.transfer a b -1m "t" (setup ()))

[<Fact>]
let ``LEDGER-T2-R2 unknown source then destination`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.transfer ghost b 1m "t" (setup ()))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.transfer a ghost 1m "t" (setup ()))

[<Fact>]
let ``LEDGER-T2-R2 same account`` () =
    Assert.Equal(Error(SameAccount a), Ledger.transfer a a 1m "t" (setup ()))

[<Fact>]
let ``LEDGER-T2-R2 insufficient funds leaves ledger unchanged`` () =
    let l = setup ()
    Assert.Equal(Error(InsufficientFunds(a, 10.01m)), Ledger.transfer a b 10.01m "t" l)
    Assert.Equal(Ok 10m, Ledger.balance a l)

[<Fact>]
let ``LEDGER-T2-R3 conservation`` () =
    let l = setup ()
    let before = total l
    let l2 = l |> Ledger.transfer a b 3m "t1" |> ok |> Ledger.transfer b a 5m "t2" |> ok
    Assert.Equal(before, total l2)
    match Ledger.transfer b a 1000m "t3" l2 with
    | Error _ -> Assert.Equal(before, total l2)
    | Ok _ -> Assert.Fail "overdraft accepted"
