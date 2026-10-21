module U5AcceptanceTests

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    [ a; b; c ] |> List.fold (fun l id -> l |> Ledger.openAccount id |> ok) Ledger.empty |> Ledger.credit a 10m "seed" |> ok
let tx s d amount reference = { Source = s; Destination = d; Amount = amount; Reference = reference }

[<Fact>]
let ``LEDGER-U5-R1 a batch applies every transfer`` () =
    let l = Ledger.transferBatch [ tx a b 3m "p1"; tx a c 2m "p2" ] (setup ()) |> ok
    Assert.Equal(Ok 5m, Ledger.balance a l)
    Assert.Equal(Ok 3m, Ledger.balance b l)
    Assert.Equal(Ok 2m, Ledger.balance c l)

[<Fact>]
let ``LEDGER-U5-R2 store refuses a batch whose first transfer fails`` () =
    let store = Store.create (setup ())
    Assert.Equal(Error(BatchFailed(0, InsufficientFunds(b, 1m))), Store.transferBatch [ tx b c 1m "p1"; tx a b 1m "p2" ] store)
    Assert.Equal(Ok 10m, Ledger.balance a (Store.current store))
