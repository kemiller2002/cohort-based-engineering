module U7AcceptanceTests

open Xunit
open Ledger

let savings = AccountId "savings"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let flat rate = InterestRates.create [ { UpTo = None; Rate = rate } ] |> ok

[<Fact>]
let ``LEDGER-U7-R1 an empty schedule is invalid`` () =
    Assert.True(match InterestRates.create [] with Error(InvalidRateSchedule _) -> true | _ -> false)

[<Fact>]
let ``LEDGER-U7-R2 a single tier pays its rate`` () =
    Assert.Equal(20m, InterestRates.interestFor (flat 0.02m) 1000m)

[<Fact>]
let ``LEDGER-U7-R3 interest is paid on the closed balance`` () =
    let l =
        Ledger.empty |> Ledger.openAccount savings |> ok |> Ledger.credit savings 101m "seed" |> ok
    let _, closed = Ledger.closePeriod "P1" l |> ok
    let paid, after = Ledger.accrueInterest "P1" (flat 0.1m) closed |> ok
    Assert.Equal(10m, paid[savings])
    Assert.Equal(Ok 110m, Ledger.balance savings after)
