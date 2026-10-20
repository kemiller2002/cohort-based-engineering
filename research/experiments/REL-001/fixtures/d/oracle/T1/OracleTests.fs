module OracleT1

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 10m "seed" |> ok

[<Fact>]
let ``LEDGER-T1-R1 credit zero refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.credit cash 0m "x" (opened ()))

[<Fact>]
let ``LEDGER-T1-R1 credit negative refused`` () =
    Assert.Equal(Error(InvalidAmount -2.5m), Ledger.credit cash -2.5m "x" (opened ()))

[<Fact>]
let ``LEDGER-T1-R1 debit zero refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.debit cash 0m "x" (opened ()))

[<Fact>]
let ``LEDGER-T1-R1 debit negative refused before funds check`` () =
    Assert.Equal(Error(InvalidAmount -50m), Ledger.debit cash -50m "x" (opened ()))

[<Fact>]
let ``LEDGER-T1-R1 refusal records nothing`` () =
    let l = opened ()
    let before = Ledger.postings l
    match Ledger.credit cash -1m "x" l with
    | Error _ -> Assert.Equal<Posting list>(before, Ledger.postings l)
    | Ok l2 -> Assert.Fail(sprintf "accepted, postings %A" (Ledger.postings l2))

[<Fact>]
let ``LEDGER-T1-R1 positive amounts unchanged`` () =
    let l = opened () |> Ledger.debit cash 3m "d" |> ok |> Ledger.credit cash 1m "c" |> ok
    Assert.Equal(Ok 8m, Ledger.balance cash l)
    Assert.Equal(Error(InsufficientFunds(cash, 100m)), Ledger.debit cash 100m "d" l)
    Assert.Equal(Error(UnknownAccount(AccountId "nope")), Ledger.credit (AccountId "nope") 1m "c" l)
