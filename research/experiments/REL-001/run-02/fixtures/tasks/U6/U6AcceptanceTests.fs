module U6AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``LEDGER-U6-R1 a frozen account reports frozen`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok
    Assert.Equal(Ok false, Ledger.isFrozen cash l)
    Assert.Equal(Ok true, Ledger.isFrozen cash (Ledger.freezeAccount cash l |> ok))

[<Fact>]
let ``LEDGER-U6-R2 a frozen account refuses debits`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 10m "seed" |> ok |> Ledger.freezeAccount cash |> ok
    Assert.Equal(Error(AccountFrozen cash), Ledger.debit cash 1m "d" l)
