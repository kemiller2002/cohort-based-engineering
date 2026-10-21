/// Ledger module: accounts, postings, balances, transfers and
/// period close. Public signatures in this module are the module's contract;
/// keep them.
module Ledger.Ledger

open System

/// Business date of a new, empty ledger.
let startDate = DateOnly(2026, 1, 1)

let empty: LedgerState =
    { Accounts = Set.empty
      Postings = []
      ClosedPeriods = Map.empty
      Today = startDate }

let openAccount (id: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if ledger.Accounts.Contains id then Error(DuplicateAccount id)
    else Ok { ledger with Accounts = ledger.Accounts.Add id }

/// Moves the business date forward. Dates never move backwards.
let setDate (date: DateOnly) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if date < ledger.Today then Error(DateInPast date)
    else Ok { ledger with Today = date }

/// All postings in journal (recording) order, oldest first.
let postings (ledger: LedgerState) : Posting list = List.rev ledger.Postings

/// Shared helper: the postings of one account, newest first.
/// Every per-account query in this module is built on it.
let postingsOf (id: AccountId) (ledger: LedgerState) : Posting list =
    ledger.Postings |> List.filter (fun p -> p.Account = id)

let balance (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else postingsOf id ledger |> List.sumBy (fun p -> p.Amount) |> Ok

let private post (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) =
    let posting = { Account = id; Amount = amount; Reference = reference; Date = ledger.Today }
    { ledger with Postings = posting :: ledger.Postings }

/// Adds `amount` (> 0) to the account.
let credit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    elif not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else Ok(post id amount reference ledger)

/// Removes `amount` (> 0) from the account. The ledger does not allow overdrafts.
let debit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    else
        match balance id ledger with
        | Error e -> Error e
        | Ok current when current < amount -> Error(InsufficientFunds(id, amount))
        | Ok _ -> Ok(post id (-amount) reference ledger)

/// Moves `amount` from `source` to `destination` as two postings carrying
/// `reference`. Refusals, in this order: InvalidAmount, UnknownAccount source,
/// UnknownAccount destination, SameAccount, InsufficientFunds.
let transfer (source: AccountId) (destination: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    elif not (ledger.Accounts.Contains source) then Error(UnknownAccount source)
    elif not (ledger.Accounts.Contains destination) then Error(UnknownAccount destination)
    elif source = destination then Error(SameAccount source)
    else
        match balance source ledger with
        | Error e -> Error e
        | Ok current when current < amount -> Error(InsufficientFunds(source, amount))
        | Ok _ -> Ok(ledger |> post source (-amount) reference |> post destination amount reference)

/// Closes an accounting period: charges a 1.00 fee (reference "fee:<periodId>")
/// to every account whose balance is at least 1.00. Idempotent per period id:
/// a repeated close records nothing and returns the first close's summary.
let closePeriod (periodId: string) (ledger: LedgerState) : Result<PeriodSummary * LedgerState, LedgerError> =
    match ledger.ClosedPeriods.TryFind periodId with
    | Some summary -> Ok(summary, ledger)
    | None ->
        let charge (l: LedgerState, fees: Map<AccountId, decimal>) id =
            let current = balance id l |> Result.defaultValue 0m
            if current >= 1m then post id -1m ("fee:" + periodId) l, fees.Add(id, 1m)
            else l, fees.Add(id, 0m)
        let charged, fees = ledger.Accounts |> Set.fold charge (ledger, Map.empty)
        let balances =
            ledger.Accounts
            |> Seq.map (fun id -> id, balance id charged |> Result.defaultValue 0m)
            |> Map.ofSeq
        let summary = { PeriodId = periodId; Fees = fees; Balances = balances }
        Ok(summary, { charged with ClosedPeriods = charged.ClosedPeriods.Add(periodId, summary) })

/// Moves the source's whole balance to the target (reference "sweep").
let sweep (source: AccountId) (target: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if not (ledger.Accounts.Contains source) then Error(UnknownAccount source)
    elif not (ledger.Accounts.Contains target) then Error(UnknownAccount target)
    elif source = target then Error(SameAccount source)
    else
        match balance source ledger with
        | Error e -> Error e
        | Ok amount when amount > 0m -> transfer source target amount "sweep" ledger
        | Ok _ -> Error(InvalidAmount 0m)
