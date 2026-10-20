module T2StarterTests

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``LEDGER-T2-R1 transfer moves money`` () =
    let l = Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok |> Ledger.credit a 10m "seed" |> ok
    let l2 = Ledger.transfer a b 4m "t1" l |> ok
    Assert.Equal(Ok 6m, Ledger.balance a l2)
    Assert.Equal(Ok 4m, Ledger.balance b l2)
