module U9AcceptanceTests

open System
open Xunit
open Ledger

let eur = AccountId "eur-account"
let usd = AccountId "usd-account"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let currencyOf id = if id = eur then Currency "EUR" else Currency "USD"
let table = { Reporting = Currency "USD"; Rates = Map [ Currency "EUR", 2m ] }
let setup () =
    Ledger.empty |> Ledger.openAccount eur |> ok |> Ledger.openAccount usd |> ok
    |> Ledger.credit eur 10m "e1" |> ok |> Ledger.credit usd 5m "u1" |> ok

[<Fact>]
let ``LEDGER-U9-R1 converts with the table rate`` () =
    Assert.Equal(Ok 7m, Conversion.convert table (Currency "EUR") 3.5m)

[<Fact>]
let ``LEDGER-U9-R2 rounds to the currency's minor units`` () =
    Assert.Equal(1.23m, Rounding.round (Currency "USD") 1.234m)

[<Fact>]
let ``LEDGER-U9-R3 holdings in the reporting currency`` () =
    let report = Reporting.holdings table currencyOf (setup ()) |> ok
    Assert.Equal(Currency "USD", report.ReportCurrency)
    Assert.Equal<decimal list>([ 20m; 5m ], report.Holdings |> List.map (fun h -> h.Reported))
    Assert.Equal(25m, report.Total)

[<Fact>]
let ``LEDGER-U9-R3 statement in the reporting currency`` () =
    let lines = Reporting.statementIn table currencyOf eur (DateOnly(2026, 1, 1)) (DateOnly(2026, 12, 31)) (setup ()) |> ok
    Assert.Equal<(decimal * decimal) list>([ 20m, 20m ], lines |> List.map (fun l -> l.ReportedAmount, l.ReportedBalance))
