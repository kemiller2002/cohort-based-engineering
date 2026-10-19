module T1StarterTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``LEDGER-T1-R1 credit of zero is refused`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok
    Assert.Equal(Error(InvalidAmount 0m), Ledger.credit cash 0m "c0" l)
