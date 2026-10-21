module V8AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 1000m "salary" |> ok

[<Fact>]
let ``LEDGER-V8-R1 a withdrawal within the limit is recorded`` () =
    let l = funded () |> Ledger.withdraw cash 100m |> ok
    Assert.Equal(Ok 900m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V8-R1 a withdrawal above the daily limit is refused`` () =
    Assert.Equal(Error(DailyLimitExceeded(cash, 500m)), Ledger.withdraw cash 600m (funded ()))

[<Fact>]
let ``LEDGER-V8-R2 nothing withdrawn yet`` () =
    Assert.Equal(Ok 0m, Ledger.withdrawnToday cash (funded ()))
