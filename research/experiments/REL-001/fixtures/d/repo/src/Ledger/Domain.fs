namespace Ledger

/// An account identifier, e.g. AccountId "cash".
type AccountId = AccountId of string

/// One immutable entry in the journal. Positive amounts credit the account,
/// negative amounts debit it.
type Posting =
    { Account: AccountId
      Amount: decimal
      Reference: string }

type LedgerError =
    | UnknownAccount of AccountId
    | DuplicateAccount of AccountId
    | InvalidAmount of decimal
    | InsufficientFunds of AccountId * decimal
    | SameAccount of AccountId

/// Result of closing an accounting period.
type PeriodSummary =
    { PeriodId: string
      /// Fee actually charged to each account at this close (0 when none).
      Fees: Map<AccountId, decimal>
      /// Balance of each account immediately after the close.
      Balances: Map<AccountId, decimal> }

/// The ledger state. Balances are always derivable from Postings.
type LedgerState =
    { Accounts: Set<AccountId>
      Postings: Posting list }
