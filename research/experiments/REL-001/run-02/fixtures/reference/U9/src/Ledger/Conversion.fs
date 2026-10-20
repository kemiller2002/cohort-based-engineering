/// Currency conversion into a reporting currency (LEDGER-U9-R1). Exact, never rounded.
module Ledger.Conversion

let rateOf (table: RateTable) (currency: Currency) : Result<decimal, LedgerError> =
    if currency = table.Reporting then Ok 1m
    else
        match table.Rates.TryFind currency with
        | Some rate -> Ok rate
        | None -> Error(UnknownCurrency currency)

let convert (table: RateTable) (currency: Currency) (amount: decimal) : Result<decimal, LedgerError> =
    rateOf table currency |> Result.map (fun rate -> amount * rate)
