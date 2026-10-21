module OracleU9

open System
open Xunit
open Ledger

let usd = Currency "USD"
let eur = Currency "EUR"
let jpy = Currency "JPY"
let krw = Currency "KRW"
let gbp = Currency "GBP"
let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let d (m: int) (day: int) = DateOnly(2026, m, day)
let table = { Reporting = usd; Rates = Map [ eur, 1.1m; gbp, 1.25m ] }

[<Fact>]
let ``LEDGER-U9-R1 reporting currency converts at 1`` () =
    Assert.Equal(Ok 1m, Conversion.rateOf table usd)
    Assert.Equal(Ok 1m, Conversion.rateOf { table with Rates = table.Rates.Add(usd, 3m) } usd)
    Assert.Equal(Ok 12.345m, Conversion.convert table usd 12.345m)

[<Fact>]
let ``LEDGER-U9-R1 conversion is exact`` () =
    Assert.Equal(Ok 1.1m, Conversion.rateOf table eur)
    Assert.Equal(Ok 12.045m, Conversion.convert table eur 10.95m)
    Assert.Equal(Ok 0.0125m, Conversion.convert table gbp 0.01m)

[<Fact>]
let ``LEDGER-U9-R1 unknown currency refused`` () =
    Assert.Equal(Error(UnknownCurrency jpy), Conversion.rateOf table jpy)
    Assert.Equal(Error(UnknownCurrency jpy), Conversion.convert table jpy 1m)

[<Fact>]
let ``LEDGER-U9-R2 minor units`` () =
    Assert.Equal(0, Rounding.minorUnits jpy)
    Assert.Equal(0, Rounding.minorUnits krw)
    Assert.Equal(2, Rounding.minorUnits usd)
    Assert.Equal(2, Rounding.minorUnits (Currency "CHF"))

[<Fact>]
let ``LEDGER-U9-R2 banker's rounding`` () =
    Assert.Equal(12.04m, Rounding.round usd 12.045m)
    Assert.Equal(12.06m, Rounding.round usd 12.055m)
    Assert.Equal(-12.04m, Rounding.round usd -12.045m)
    Assert.Equal(2m, Rounding.round jpy 2.5m)
    Assert.Equal(4m, Rounding.round krw 3.5m)
    Assert.Equal(40m, Rounding.round jpy 40.125m)

let currencyOf id = if id = a then eur elif id = b then gbp else usd
let setup () =
    Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok |> Ledger.openAccount c |> ok
    |> Ledger.setDate (d 2 1) |> ok |> Ledger.credit a 10.95m "a1" |> ok |> Ledger.credit b 0.01m "b1" |> ok
    |> Ledger.setDate (d 2 2) |> ok |> Ledger.credit a 10.95m "a2" |> ok |> Ledger.credit c 3m "c1" |> ok

[<Fact>]
let ``LEDGER-U9-R3 statement balance converted from the native balance`` () =
    let lines = Reporting.statementIn table currencyOf a (d 1 1) (d 12 31) (setup ()) |> ok
    // amounts: 12.045 -> 12.04 each; balances: 12.045 -> 12.04, 24.09 -> 24.09 (not 12.04 + 12.04)
    Assert.Equal<(decimal * decimal) list>([ 12.04m, 12.04m; 12.04m, 24.09m ], lines |> List.map (fun l -> l.ReportedAmount, l.ReportedBalance))
    Assert.Equal<string list>([ "a1"; "a2" ], lines |> List.map (fun l -> l.Source.Reference))
    Assert.Equal(21.9m, (List.last lines).Source.Balance)

[<Fact>]
let ``LEDGER-U9-R3 statement keeps the range and its errors`` () =
    let lines = Reporting.statementIn table currencyOf a (d 2 2) (d 2 2) (setup ()) |> ok
    Assert.Equal<(decimal * decimal) list>([ 12.04m, 24.09m ], lines |> List.map (fun l -> l.ReportedAmount, l.ReportedBalance))
    Assert.Equal(Error(InvalidDateRange(d 2 3, d 2 2)), Reporting.statementIn table currencyOf a (d 2 3) (d 2 2) (setup ()))
    Assert.Equal(Error(UnknownAccount ghost), Reporting.statementIn table currencyOf ghost (d 1 1) (d 2 2) (setup ()))

[<Fact>]
let ``LEDGER-U9-R3 statement refuses an unknown currency even without lines`` () =
    let noJpy id = if id = a then jpy else usd
    Assert.Equal(Error(UnknownCurrency jpy), Reporting.statementIn table noJpy a (d 5 1) (d 5 2) (setup ()))

[<Fact>]
let ``LEDGER-U9-R3 holdings total is the sum of the rounded figures`` () =
    let report = Reporting.holdings table currencyOf (setup ()) |> ok
    Assert.Equal<Holding list>(
        [ { Holder = a; Native = eur; NativeBalance = 21.9m; Reported = 24.09m }
          { Holder = b; Native = gbp; NativeBalance = 0.01m; Reported = 0.01m }
          { Holder = c; Native = usd; NativeBalance = 3m; Reported = 3m } ],
        report.Holdings)
    Assert.Equal(27.1m, report.Total)

[<Fact>]
let ``LEDGER-U9-R3 total adds rounded lines not the rounded exact sum`` () =
    let l = Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok
            |> Ledger.credit a 10.95m "a" |> ok |> Ledger.credit b 10.95m "b" |> ok
    let report = Reporting.holdings table (fun _ -> eur) l |> ok
    // each 12.045 -> 12.04; total 24.08 (the exact sum 24.09 is not what the lines show)
    Assert.Equal(24.08m, report.Total)

[<Fact>]
let ``LEDGER-U9-R3 reporting in yen rounds to whole units`` () =
    let yen = { Reporting = jpy; Rates = Map [ eur, 160.5m; usd, 150m ] }
    let l = Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount c |> ok
            |> Ledger.credit a 0.25m "a" |> ok |> Ledger.credit c 0.01m "c" |> ok
    let report = Reporting.holdings yen (fun id -> if id = a then eur else usd) l |> ok
    // 0.25 x 160.5 = 40.125 -> 40; 0.01 x 150 = 1.5 -> 2
    Assert.Equal<decimal list>([ 40m; 2m ], report.Holdings |> List.map (fun h -> h.Reported))
    Assert.Equal(42m, report.Total)
    Assert.Equal(jpy, report.ReportCurrency)

[<Fact>]
let ``LEDGER-U9-R3 holdings refuse the first account without a rate`` () =
    let cur id = if id = a then usd elif id = b then krw else jpy
    Assert.Equal(Error(UnknownCurrency krw), Reporting.holdings table cur (setup ()))
