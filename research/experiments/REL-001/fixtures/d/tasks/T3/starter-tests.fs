module T3StarterTests

open Xunit
open Ledger

let a = AccountId "a"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``LEDGER-T3-R1 close charges the fee`` () =
    let l = Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.credit a 5m "seed" |> ok
    let summary, l2 = Ledger.closePeriod "2026-09" l |> ok
    Assert.Equal(Ok 4m, Ledger.balance a l2)
    Assert.Equal(1m, summary.Fees[a])
