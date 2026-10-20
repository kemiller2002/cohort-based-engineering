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

/// WRONG VARIANT (trap proof): the running balance is accumulated from the
/// rounded line amounts instead of converted from the native balance.
let statementIn (table: RateTable) (currencyOf: AccountId -> Currency) (id: AccountId) (fromDate: DateOnly) (toDate: DateOnly) (ledger: LedgerState) : Result<ReportLine list, LedgerError> =
    let currency = currencyOf id
    Ledger.statement id fromDate toDate ledger
    |> Result.bind (fun lines -> Conversion.rateOf table currency |> Result.map (fun _ -> lines))
    |> Result.bind (fun lines ->
        match lines with
        | [] -> Ok []
        | first :: _ ->
            reported table currency (first.Balance - first.Amount)
            |> Result.bind (fun opening ->
                lines
                |> traverse (fun line -> reported table currency line.Amount |> Result.map (fun amount -> line, amount))
                |> Result.map (fun pairs ->
                    pairs
                    |> List.mapFold (fun running (line, amount) ->
                        let after = running + amount
                        { Source = line; ReportedAmount = amount; ReportedBalance = after }, after) opening
                    |> fst)))

let holdings (table: RateTable) (currencyOf: AccountId -> Currency) (ledger: LedgerState) : Result<HoldingsReport, LedgerError> =
    ledger.Accounts
    |> Set.toList
    |> traverse (fun id ->
        let native = currencyOf id
        Ledger.balance id ledger
        |> Result.bind (fun bal ->
            reported table native bal |> Result.map (fun r -> { Holder = id; Native = native; NativeBalance = bal; Reported = r })))
    |> Result.map (fun hs -> { ReportCurrency = table.Reporting; Holdings = hs; Total = Rounding.round table.Reporting (hs |> List.sumBy (fun h -> h.NativeBalance * (Conversion.rateOf table h.Native |> Result.defaultValue 0m))) }) // WRONG: rounded exact sum
