# U9: Multi-currency reporting view

Category: complex. Requirements: LEDGER-U9-R1, LEDGER-U9-R2,
LEDGER-U9-R3. Decision: DEC-U9-ROUND-ONCE.

Accounts hold money in different currencies, and management wants reports
in one reporting currency. Build on the existing `Ledger.statement` (its
`StatementLine` shape is unchanged). Each account's currency is supplied by
the caller as a function `currencyOf: AccountId -> Currency`.

Add to `src/Ledger/Domain.fs` (declare `Currency` before `LedgerError`):

```fsharp
/// An ISO 4217 currency code, e.g. Currency "EUR".
type Currency = Currency of string

/// Conversion rates into one reporting currency.
type RateTable =
    { Reporting: Currency
      /// Units of `Reporting` that one unit of the key currency is worth.
      Rates: Map<Currency, decimal> }

/// A statement line with its amounts in the reporting currency.
type ReportLine =
    { Source: StatementLine
      ReportedAmount: decimal
      ReportedBalance: decimal }

/// One account's balance in its own and in the reporting currency.
type Holding =
    { Holder: AccountId
      Native: Currency
      NativeBalance: decimal
      Reported: decimal }

type HoldingsReport =
    { ReportCurrency: Currency
      Holdings: Holding list
      Total: decimal }
```

and a case `UnknownCurrency of Currency` on `LedgerError`. The three
modules below are new files in `src/Ledger/`, compiled after `Ledger.fs` in
`src/Ledger/Ledger.fsproj`.

## LEDGER-U9-R1

Module `Ledger.Conversion` (`Conversion.fs`):

```fsharp
val rateOf : table: RateTable -> currency: Currency -> Result<decimal, LedgerError>
val convert : table: RateTable -> currency: Currency -> amount: decimal -> Result<decimal, LedgerError>
```

- `rateOf` is 1 for the table's `Reporting` currency (any entry for it in
  `Rates` is ignored) and the `Rates` entry for any other currency. A
  currency with no entry is refused with `Error (UnknownCurrency currency)`.
- `convert table currency amount` is `amount * rateOf table currency`,
  exact and **not rounded**.

## LEDGER-U9-R2

Module `Ledger.Rounding` (`Rounding.fs`):

```fsharp
val minorUnits : currency: Currency -> int
val round : currency: Currency -> amount: decimal -> decimal
```

- `minorUnits` is 0 for `Currency "JPY"` and `Currency "KRW"`, and 2 for
  every other currency.
- `round currency amount` rounds to `minorUnits currency` decimal places
  with banker's rounding (round half to even).

## LEDGER-U9-R3

Module `Ledger.Reporting` (`Reporting.fs`). Rounding policy (decision
DEC-U9-ROUND-ONCE): every reported figure is converted exactly from the
native figure and then rounded once, with `Rounding.round` in the
reporting currency. Reported figures are never derived from other rounded
figures, except the holdings total below.

```fsharp
val statementIn : table: RateTable -> currencyOf: (AccountId -> Currency) -> id: AccountId -> fromDate: DateOnly -> toDate: DateOnly -> ledger: LedgerState -> Result<ReportLine list, LedgerError>
val holdings : table: RateTable -> currencyOf: (AccountId -> Currency) -> ledger: LedgerState -> Result<HoldingsReport, LedgerError>
```

- `statementIn` returns one `ReportLine` per line of
  `Ledger.statement id fromDate toDate ledger`, in the same order, with the
  original line as `Source`. `ReportedAmount` is the line's `Amount`
  converted and rounded; `ReportedBalance` is the line's (native) `Balance`
  converted and rounded. Errors from `Ledger.statement` are returned as
  they are; otherwise an account whose currency has no rate is refused with
  `Error (UnknownCurrency currency)`, even when there are no lines.
- `holdings` returns one `Holding` per account, in ascending account order:
  `NativeBalance` is the account's balance and `Reported` is that balance
  converted and rounded. `ReportCurrency` is the table's `Reporting`
  currency. `Total` is the sum of the `Reported` values exactly as shown,
  so the report always adds up. If any account's currency has no rate, the
  report is refused with `Error (UnknownCurrency currency)` for the first
  such account in ascending order.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
