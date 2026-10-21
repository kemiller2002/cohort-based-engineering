module V7AcceptanceTests

open Xunit
open Ledger

let pocket = AccountId "pocket"
let main = AccountId "main"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount pocket |> ok |> Ledger.openAccount main |> ok

[<Fact>]
let ``LEDGER-V7-R1 a sweep moves the whole balance`` () =
    let l = opened () |> Ledger.credit pocket 25m "change" |> ok |> Ledger.sweep pocket main |> ok
    Assert.Equal(Ok 0m, Ledger.balance pocket l)
    Assert.Equal(Ok 25m, Ledger.balance main l)
