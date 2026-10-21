module V1AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount cash |> ok

[<Fact>]
let ``LEDGER-V1-R1 an empty account can be closed`` () =
    let l = opened () |> Ledger.closeAccount cash |> ok
    Assert.Equal(Error(UnknownAccount cash), Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V1-R1 an account holding money is not closed`` () =
    let l = opened () |> Ledger.credit cash 10m "seed" |> ok
    Assert.Equal(Error(NonZeroBalance(cash, 10m)), Ledger.closeAccount cash l)
