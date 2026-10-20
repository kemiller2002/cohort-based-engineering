module U2AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e

[<Fact>]
let ``LEDGER-U2-R1 reopening a period that was never closed is refused`` () =
    let l = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 5m "seed" |> ok
    Assert.Equal(Error(PeriodNotClosed "P1"), Ledger.reopenPeriod "P1" l)
