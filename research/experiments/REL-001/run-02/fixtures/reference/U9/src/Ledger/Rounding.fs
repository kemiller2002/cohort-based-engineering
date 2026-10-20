/// Rounding policy (LEDGER-U9-R2): minor units per currency, half to even.
module Ledger.Rounding

open System

let private zeroDecimal = set [ Currency "JPY"; Currency "KRW" ]

let minorUnits (currency: Currency) : int = if zeroDecimal.Contains currency then 0 else 2

let round (currency: Currency) (amount: decimal) : decimal =
    Math.Round(amount, minorUnits currency, MidpointRounding.ToEven)
