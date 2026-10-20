module OracleU1

open Xunit
open Ledger

let cash = AccountId "cash"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 10m "seed" |> ok
let added (before: LedgerState) (after: LedgerState) =
    Ledger.postings after |> List.skip (List.length (Ledger.postings before))

[<Fact>]
let ``LEDGER-U1-R1 zero refused in both directions`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.adjust cash Increase 0m "r" (opened ()))
    Assert.Equal(Error(InvalidAmount 0m), Ledger.adjust cash Decrease 0m "r" (opened ()))

[<Fact>]
let ``LEDGER-U1-R1 negative refused with the supplied amount`` () =
    Assert.Equal(Error(InvalidAmount -3.25m), Ledger.adjust cash Increase -3.25m "r" (opened ()))
    Assert.Equal(Error(InvalidAmount -0.01m), Ledger.adjust cash Decrease -0.01m "r" (opened ()))

[<Fact>]
let ``LEDGER-U1-R1 amount check comes before the account check`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.adjust ghost Increase 0m "r" (opened ()))
    Assert.Equal(Error(InvalidAmount -1m), Ledger.adjust ghost Decrease -1m "r" (opened ()))

[<Fact>]
let ``LEDGER-U1-R1 unknown account refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.adjust ghost Increase 1m "r" (opened ()))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.adjust ghost Decrease 1m "r" (opened ()))

[<Fact>]
let ``LEDGER-U1-R1 decrease beyond balance refused`` () =
    Assert.Equal(Error(InsufficientFunds(cash, 10.01m)), Ledger.adjust cash Decrease 10.01m "r" (opened ()))

[<Fact>]
let ``LEDGER-U1-R1 decrease of the whole balance allowed`` () =
    let l = Ledger.adjust cash Decrease 10m "r" (opened ()) |> ok
    Assert.Equal(Ok 0m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-U1-R1 one posting with the adjust reference`` () =
    let l0 = opened ()
    let up = Ledger.adjust cash Increase 2m "typo" l0 |> ok
    Assert.Equal<Posting list>([ { Account = cash; Amount = 2m; Reference = "adjust:typo"; Date = l0.Today } ], added l0 up)
    let down = Ledger.adjust cash Decrease 4m "refund" l0 |> ok
    Assert.Equal<Posting list>([ { Account = cash; Amount = -4m; Reference = "adjust:refund"; Date = l0.Today } ], added l0 down)

[<Fact>]
let ``LEDGER-U1-R1 posting dated with the business date`` () =
    let day = System.DateOnly(2026, 5, 4)
    let l0 = opened () |> Ledger.setDate day |> ok
    let l = Ledger.adjust cash Increase 1m "r" l0 |> ok
    Assert.Equal(day, (List.exactlyOne (added l0 l)).Date)

[<Fact>]
let ``LEDGER-U1-R1 refusals record no posting`` () =
    let l0 = opened ()
    for r in [ Ledger.adjust cash Increase 0m "r" l0; Ledger.adjust cash Decrease 11m "r" l0; Ledger.adjust ghost Increase 1m "r" l0 ] do
        Assert.True(Result.isError r)
    Assert.Equal(1, List.length (Ledger.postings l0))
