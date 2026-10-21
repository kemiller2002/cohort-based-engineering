/// Reports in one reporting currency (LEDGER-U9-R3, DEC-U9-ROUND-ONCE):
/// every figure is converted exactly from the native figure, then rounded once.
module Ledger.Reporting

open System

let private reported (table: RateTable) (currency: Currency) (amount: decimal) : Result<decimal, LedgerError> =
    Conversion.convert table currency amount |> Result.map (Rounding.round table.Reporting)

/// Applies `f` left to right; the first failure in list order wins.
let private traverse (f: 'a -> Result<'b, LedgerError>) (xs: 'a list) : Result<'b list, LedgerError> =
    xs
    |> List.fold (fun acc x -> acc |> Result.bind (fun ys -> f x |> Result.map (fun y -> y :: ys))) (Ok [])
    |> Result.map List.rev

let statementIn (table: RateTable) (currencyOf: AccountId -> Currency) (id: AccountId) (fromDate: DateOnly) (toDate: DateOnly) (ledger: LedgerState) : Result<ReportLine list, LedgerError> =
    let currency = currencyOf id
    Ledger.statement id fromDate toDate ledger
    |> Result.bind (fun lines -> Conversion.rateOf table currency |> Result.map (fun _ -> lines))
    |> Result.bind (traverse (fun line ->
        reported table currency line.Amount
        |> Result.bind (fun amount ->
            reported table currency line.Balance
            |> Result.map (fun balance -> { Source = line; ReportedAmount = amount; ReportedBalance = balance }))))

let holdings (table: RateTable) (currencyOf: AccountId -> Currency) (ledger: LedgerState) : Result<HoldingsReport, LedgerError> =
    ledger.Accounts
    |> Set.toList
    |> traverse (fun id ->
        let native = currencyOf id
        Ledger.balance id ledger
        |> Result.bind (fun bal ->
            reported table native bal |> Result.map (fun r -> { Holder = id; Native = native; NativeBalance = bal; Reported = r })))
    |> Result.map (fun hs -> { ReportCurrency = table.Reporting; Holdings = hs; Total = hs |> List.sumBy (fun h -> h.Reported) })
