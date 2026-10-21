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

type LedgerError =
    | UnknownAccount of AccountId
    | DuplicateAccount of AccountId
    | InvalidAmount of decimal
    | InsufficientFunds of AccountId * decimal
    | SameAccount of AccountId
    | DateInPast of DateOnly
    | DailyLimitExceeded of AccountId * decimal

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
