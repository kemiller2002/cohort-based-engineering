module U1AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 10m "seed" |> ok

[<Fact>]
let ``LEDGER-U1-R1 increase adds to the balance`` () =
    let l = Ledger.adjust cash Increase 2.5m "typo" (opened ()) |> ok
    Assert.Equal(Ok 12.5m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-U1-R1 zero amount is refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.adjust cash Increase 0m "typo" (opened ()))
