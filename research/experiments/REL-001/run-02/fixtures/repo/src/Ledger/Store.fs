/// In-memory ledger store: the one place where ledger state changes over time.
/// It holds the journal (`current`) and a balance cache (`balance`) that is kept
/// in step with the journal by every operation, so balance reads do not rescan
/// the journal. An operation is validated against the current state first; a
/// refused operation leaves both the journal and the cache unchanged.
module Ledger.Store

type LedgerStore =
    private
        { Journal: LedgerState ref
          Balances: Map<AccountId, decimal> ref }

let create (initial: LedgerState) : LedgerStore =
    let balances =
        initial.Accounts
        |> Seq.map (fun id -> id, Ledger.balance id initial |> Result.defaultValue 0m)
        |> Map.ofSeq
    { Journal = ref initial; Balances = ref balances }

/// The committed ledger state (journal).
let current (store: LedgerStore) : LedgerState = store.Journal.Value

/// The account's balance, read from the balance cache.
let balance (id: AccountId) (store: LedgerStore) : Result<decimal, LedgerError> =
    match store.Balances.Value.TryFind id with
    | Some amount -> Ok amount
    | None -> Error(UnknownAccount id)

let private shiftBalance (id: AccountId) (delta: decimal) (store: LedgerStore) =
    store.Balances.Value <- store.Balances.Value.Change(id, fun current -> Some(Option.defaultValue 0m current + delta))

let openAccount (id: AccountId) (store: LedgerStore) : Result<unit, LedgerError> =
    Ledger.openAccount id store.Journal.Value
    |> Result.map (fun next ->
        store.Journal.Value <- next
        store.Balances.Value <- store.Balances.Value.Add(id, 0m))

let credit (id: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) : Result<unit, LedgerError> =
    Ledger.credit id amount reference store.Journal.Value
    |> Result.map (fun next ->
        store.Journal.Value <- next
        shiftBalance id amount store)

let debit (id: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) : Result<unit, LedgerError> =
    Ledger.debit id amount reference store.Journal.Value
    |> Result.map (fun next ->
        store.Journal.Value <- next
        shiftBalance id (-amount) store)

let transfer (source: AccountId) (destination: AccountId) (amount: decimal) (reference: string) (store: LedgerStore) : Result<unit, LedgerError> =
    Ledger.transfer source destination amount reference store.Journal.Value
    |> Result.map (fun next ->
        store.Journal.Value <- next
        shiftBalance source (-amount) store
        shiftBalance destination amount store)
