module V2AcceptanceTests

open Xunit
open Ledger

let alpha = AccountId "alpha"
let beta = AccountId "beta"
let gamma = AccountId "gamma"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let ledger () =
    Ledger.empty
    |> Ledger.openAccount alpha |> ok |> Ledger.openAccount beta |> ok |> Ledger.openAccount gamma |> ok
    |> Ledger.credit alpha 30m "a" |> ok |> Ledger.credit beta 10m "b" |> ok |> Ledger.credit gamma 20m "c" |> ok

[<Fact>]
let ``LEDGER-V2-R1 the largest balances come first`` () =
    Assert.Equal(Ok [ (alpha, 30m); (gamma, 20m) ], Ledger.richest 2 (ledger ()))

[<Fact>]
let ``LEDGER-V2-R1 a negative count is refused`` () =
    Assert.Equal(Error(InvalidCount -1), Ledger.richest -1 (ledger ()))
