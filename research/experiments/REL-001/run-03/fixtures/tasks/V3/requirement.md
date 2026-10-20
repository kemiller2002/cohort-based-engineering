# V3: Holds on funds

Requirements: LEDGER-V3-R1, LEDGER-V3-R2.

Card payments are authorised before they settle. Until then the amount is
held: it still belongs to the account, but it cannot be spent. Add to
`src/Ledger/Domain.fs` the error cases

```fsharp
| DuplicateHold of string
| UnknownHold of string
```

and keep the active holds in the ledger state (how they are stored is up to
you). Implement in `src/Ledger/Ledger.fs`:

```fsharp
val available : id: AccountId -> ledger: LedgerState -> Result<decimal, LedgerError>
val placeHold : holdId: string -> id: AccountId -> amount: decimal -> ledger: LedgerState -> Result<LedgerState, LedgerError>
val releaseHold : holdId: string -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

## LEDGER-V3-R1

- `available id` is the account's balance minus the amounts of all its
  active holds; `Error (UnknownAccount id)` for an account that is not open.
- `placeHold holdId id amount` refuses, in this order: `amount` zero or
  negative, `Error (InvalidAmount amount)`; the account is not open,
  `Error (UnknownAccount id)`; an active hold with the same `holdId` exists
  (on any account), `Error (DuplicateHold holdId)`; `amount` is more than the
  account's available amount, `Error (InsufficientFunds (id, amount))`.
  Otherwise it adds an active hold of `amount` on the account.
- `releaseHold holdId` refuses with `Error (UnknownHold holdId)` when there is
  no active hold with that id; otherwise the hold stops being active. A
  released hold id may be used again.
- Holds never record postings and never change `balance`.

## LEDGER-V3-R2

Money that is held cannot be spent:

- `debit` and `transfer` (for the source account) refuse with
  `Error (InsufficientFunds (id, amount))` when `amount` is more than the
  account's available amount, even when the balance would cover it. Their
  other refusals and their order are unchanged.
- `closePeriod` is unchanged: its fee depends on the balance, not on holds.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
