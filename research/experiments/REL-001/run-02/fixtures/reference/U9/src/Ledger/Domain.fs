namespace Ledger

open System

/// An account identifier, e.g. AccountId "cash".
type AccountId = AccountId of string

/// One immutable entry in the journal. Positive amounts credit the account,
/// negative amounts debit it. `Date` is the ledger's business date when the
/// posting was recorded.
type Posting =
    { Account: AccountId
      Amount: decimal
      Reference: string
      Date: DateOnly }

/// An ISO 4217 currency code, e.g. Currency "EUR".
type Currency = Currency of string

type LedgerError =
    | UnknownAccount of AccountId
    | DuplicateAccount of AccountId
    | InvalidAmount of decimal
    | InsufficientFunds of AccountId * decimal
    | SameAccount of AccountId
    | DateInPast of DateOnly
    | InvalidDateRange of DateOnly * DateOnly
    | UnknownCurrency of Currency

/// Result of closing an accounting period.
type PeriodSummary =
    { PeriodId: string
      /// Fee actually charged to each account at this close (0 when none).
      Fees: Map<AccountId, decimal>
      /// Balance of each account immediately after the close.
      Balances: Map<AccountId, decimal> }

/// The ledger state. Balances are always derivable from Postings.
/// Postings are stored newest first; use `Ledger.postings` for journal order.
type LedgerState =
    { Accounts: Set<AccountId>
      Postings: Posting list
      ClosedPeriods: Map<string, PeriodSummary>
      /// Current business date; new postings are stamped with it.
      Today: DateOnly }

/// One line of an account statement.
type StatementLine =
    { Date: DateOnly
      Reference: string
      Amount: decimal
      /// The account's balance immediately after this posting.
      Balance: decimal }

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
