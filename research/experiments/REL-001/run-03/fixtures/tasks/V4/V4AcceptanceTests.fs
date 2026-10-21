module V4AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let holding amount = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash amount "seed" |> ok

[<Fact>]
let ``LEDGER-V4-R1 the preview shows the fee of a small balance`` () =
    Assert.Equal(Ok 1m, Ledger.feeFor cash (holding 10m))

[<Fact>]
let ``LEDGER-V4-R1 the preview of an unknown account is refused`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.feeFor ghost (holding 10m))

[<Fact>]
let ``LEDGER-V4-R2 a premium balance pays no fee at close`` () =
    let summary, l = Ledger.closePeriod "P1" (holding 1500m) |> ok
    Assert.Equal(0m, summary.Fees.[cash])
    Assert.Equal(Ok 1500m, Ledger.balance cash l)
