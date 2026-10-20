module V3AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 100m "seed" |> ok

[<Fact>]
let ``LEDGER-V3-R1 a hold reduces the available amount but not the balance`` () =
    let l = funded () |> Ledger.placeHold "card-1" cash 30m |> ok
    Assert.Equal(Ok 70m, Ledger.available cash l)
    Assert.Equal(Ok 100m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V3-R2 held money cannot be debited`` () =
    let l = funded () |> Ledger.placeHold "card-1" cash 30m |> ok
    Assert.Equal(Error(InsufficientFunds(cash, 80m)), Ledger.debit cash 80m "atm" l)
