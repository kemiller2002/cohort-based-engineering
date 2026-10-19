/// REL-001 D reference solution (T1+T2+T3). Harness smoke test only; never
/// copied into an agent workspace.
module Ledger.Ledger

let empty: LedgerState = { Accounts = Set.empty; Postings = []; ClosedPeriods = Map.empty }

let openAccount (id: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if ledger.Accounts.Contains id then Error(DuplicateAccount id)
    else Ok { ledger with Accounts = ledger.Accounts.Add id }

let postings (ledger: LedgerState) : Posting list = List.rev ledger.Postings

let balance (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else ledger.Postings |> List.filter (fun p -> p.Account = id) |> List.sumBy (fun p -> p.Amount) |> Ok

let private post (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) =
    { ledger with Postings = { Account = id; Amount = amount; Reference = reference } :: ledger.Postings }

let credit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    elif not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else Ok(post id amount reference ledger)

let debit (id: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    else
        match balance id ledger with
        | Error e -> Error e
        | Ok current when current < amount -> Error(InsufficientFunds(id, amount))
        | Ok _ -> Ok(post id (-amount) reference ledger)

let transfer (source: AccountId) (destination: AccountId) (amount: decimal) (reference: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    elif not (ledger.Accounts.Contains source) then Error(UnknownAccount source)
    elif not (ledger.Accounts.Contains destination) then Error(UnknownAccount destination)
    elif source = destination then Error(SameAccount source)
    else
        match balance source ledger with
        | Ok current when current < amount -> Error(InsufficientFunds(source, amount))
        | Error e -> Error e
        | Ok _ -> Ok(ledger |> post source (-amount) reference |> post destination amount reference)

let closePeriod (periodId: string) (ledger: LedgerState) : Result<PeriodSummary * LedgerState, LedgerError> =
    match ledger.ClosedPeriods.TryFind periodId with
    | Some summary -> Ok(summary, ledger)
    | None ->
        let charged, fees =
            ledger.Accounts
            |> Set.fold (fun (l, fees) id ->
                let current = balance id l |> Result.defaultValue 0m
                if current >= 1m then post id -1m ("fee:" + periodId) l, Map.add id 1m fees
                else l, Map.add id 0m fees) (ledger, Map.empty)
        let balances = ledger.Accounts |> Seq.map (fun id -> id, balance id charged |> Result.defaultValue 0m) |> Map.ofSeq
        let summary = { PeriodId = periodId; Fees = fees; Balances = balances }
        Ok(summary, { charged with ClosedPeriods = charged.ClosedPeriods.Add(periodId, summary) })
