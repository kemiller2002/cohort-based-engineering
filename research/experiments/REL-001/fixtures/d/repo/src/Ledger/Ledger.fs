/// Echelon-style ledger module: accounts, postings and balances.
/// Public signatures in this module are the module's contract; keep them.
module Ledger.Ledger

let empty: LedgerState = { Accounts = Set.empty; Postings = [] }

let openAccount (id: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if ledger.Accounts.Contains id then Error(DuplicateAccount id)
    else Ok { ledger with Accounts = ledger.Accounts.Add id }

let postings (ledger: LedgerState) : Posting list = List.rev ledger.Postings

let balance (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else
        ledger.Postings
        |> List.filter (fun p -> p.Account = id)
        |> List.sumBy (fun p -> p.Amount)
        |> Ok

let private post (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) =
    { ledger with Postings = { Account = id; Amount = amount; Reference = reference } :: ledger.Postings }

/// Adds `amount` to the account.
let credit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else Ok(post id amount reference ledger)

/// Removes `amount` from the account. The ledger does not allow overdrafts.
let debit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    match balance id ledger with
    | Error e -> Error e
    | Ok current when current < amount -> Error(InsufficientFunds(id, amount))
    | Ok _ -> Ok(post id (-amount) reference ledger)

/// Moves `amount` from one account to another. Not implemented yet.
let transfer (source: AccountId) (destination: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    failwith "transfer: not implemented"

/// Closes an accounting period. Not implemented yet.
let closePeriod (periodId: string) (ledger: LedgerState) : Result<PeriodSummary * LedgerState, LedgerError> =
    failwith "closePeriod: not implemented"
