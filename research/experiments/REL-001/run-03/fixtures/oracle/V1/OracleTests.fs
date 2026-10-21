module OracleV1

open Xunit
open Ledger

let cash = AccountId "cash"
let savings = AccountId "savings"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount savings |> ok

[<Fact>]
let ``LEDGER-V1-R1 an account that was never opened is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.closeAccount ghost (opened ()))

[<Fact>]
let ``LEDGER-V1-R1 closing twice is refused as unknown`` () =
    let l = opened () |> Ledger.closeAccount cash |> ok
    Assert.Equal(Error(UnknownAccount cash), Ledger.closeAccount cash l)

[<Fact>]
let ``LEDGER-V1-R1 a non-zero balance is refused with that balance`` () =
    let l = opened () |> Ledger.credit cash 10.5m "seed" |> ok
    Assert.Equal(Error(NonZeroBalance(cash, 10.5m)), Ledger.closeAccount cash l)

[<Fact>]
let ``LEDGER-V1-R1 an emptied account closes and keeps its postings`` () =
    let l = opened () |> Ledger.credit cash 4m "in" |> ok |> Ledger.transfer cash savings 4m "out" |> ok
    let closed = Ledger.closeAccount cash l |> ok
    Assert.True((Ledger.postings closed = Ledger.postings l))
    Assert.False(closed.Accounts.Contains cash)
    Assert.True(closed.Accounts.Contains savings)
    Assert.Equal(Ok 4m, Ledger.balance savings closed)

[<Fact>]
let ``LEDGER-V1-R1 operations naming a closed account are refused as unknown`` () =
    let l = opened () |> Ledger.credit savings 5m "s" |> ok |> Ledger.closeAccount cash |> ok
    Assert.Equal(Error(UnknownAccount cash), Ledger.credit cash 1m "c" l)
    Assert.Equal(Error(UnknownAccount cash), Ledger.debit cash 1m "d" l)
    Assert.Equal(Error(UnknownAccount cash), Ledger.transfer savings cash 1m "t" l)
    Assert.Equal(Error(UnknownAccount cash), Ledger.transfer cash savings 1m "t" l)

[<Fact>]
let ``LEDGER-V1-R1 a closed id without postings is never reopened`` () =
    let l = opened () |> Ledger.closeAccount cash |> ok
    Assert.Equal(Error(DuplicateAccount cash), Ledger.openAccount cash l)

[<Fact>]
let ``LEDGER-V1-R1 a closed id with history is never reopened`` () =
    let l = opened () |> Ledger.credit cash 3m "in" |> ok |> Ledger.debit cash 3m "out" |> ok |> Ledger.closeAccount cash |> ok
    Assert.Equal(Error(DuplicateAccount cash), Ledger.openAccount cash l)

[<Fact>]
let ``LEDGER-V1-R1 a period close no longer charges or lists a closed account`` () =
    let l = opened () |> Ledger.credit savings 5m "s" |> ok |> Ledger.closeAccount cash |> ok
    let summary, _ = Ledger.closePeriod "P1" l |> ok
    Assert.False(summary.Fees.ContainsKey cash)
    Assert.False(summary.Balances.ContainsKey cash)
    Assert.Equal(1m, summary.Fees.[savings])
