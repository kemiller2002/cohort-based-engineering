/// In-memory ledger store: the one place where ledger state changes over time.
/// Each operation is applied to the current state and committed only when it
/// succeeds; a refused operation leaves the store unchanged.
module Ledger.Store

type LedgerStore = private { Cell: LedgerState ref }

let create (initial: LedgerState) : LedgerStore = { Cell = ref initial }

let current (store: LedgerStore) : LedgerState = store.Cell.Value

/// Applies `operation` to the current state and commits the result on success.
let private commit (operation: LedgerState -> Result<LedgerState, LedgerError>) (store: LedgerStore) : Result<unit, LedgerError> =
    operation store.Cell.Value
    |> Result.map (fun next -> store.Cell.Value <- next)

let openAccount (id: AccountId) (store: LedgerStore) = commit (Ledger.openAccount id) store

let credit (id: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) =
    commit (Ledger.credit id amount reference) store

let debit (id: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) =
    commit (Ledger.debit id amount reference) store

let transfer (source: AccountId) (destination: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) =
    commit (Ledger.transfer source destination amount reference) store
