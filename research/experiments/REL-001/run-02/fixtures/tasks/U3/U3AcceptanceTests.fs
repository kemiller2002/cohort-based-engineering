module U3AcceptanceTests

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    [ a; b; c ] |> List.fold (fun l id -> l |> Ledger.openAccount id |> ok |> Ledger.credit id 20m "seed" |> ok) Ledger.empty

[<Fact>]
let ``LEDGER-U3-R2 even split across three accounts`` () =
    let l = Ledger.chargeSharedFee 9m [ a; b; c ] "fee:custody" (setup ()) |> ok
    Assert.Equal(Ok 17m, Ledger.balance a l)
    Assert.Equal(Ok 17m, Ledger.balance b l)
    Assert.Equal(Ok 17m, Ledger.balance c l)

[<Fact>]
let ``LEDGER-U3-R2 even split across two accounts`` () =
    let l = Ledger.chargeSharedFee 10m [ a; b ] "fee:custody" (setup ()) |> ok
    Assert.Equal(Ok 15m, Ledger.balance a l)
    Assert.Equal(Ok 15m, Ledger.balance b l)
    Assert.Equal(Ok 20m, Ledger.balance c l)

[<Fact>]
let ``LEDGER-U3-R1 zero total is refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.chargeSharedFee 0m [ a; b ] "fee:custody" (setup ()))
