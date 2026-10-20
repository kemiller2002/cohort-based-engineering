# U6: Freezing accounts

Category: adversarial. Requirements: LEDGER-U6-R1, LEDGER-U6-R2.
Decision: DEC-U6-FREEZE-SCOPE.

Compliance needs to stop money leaving an account under investigation. Add
a case `AccountFrozen of AccountId` to `LedgerError` in
`src/Ledger/Domain.fs` (you may add fields to `LedgerState` and update
`Ledger.empty`). Implement in `src/Ledger/Ledger.fs`:

```fsharp
val freezeAccount : id: AccountId -> ledger: LedgerState -> Result<LedgerState, LedgerError>
val isFrozen : id: AccountId -> ledger: LedgerState -> Result<bool, LedgerError>
```

## LEDGER-U6-R1

`Ledger.freezeAccount id ledger` marks the account as frozen; `Ledger.isFrozen`
reports it. Both refuse an unknown account with `Error (UnknownAccount id)`.
Freezing an account that is already frozen succeeds and changes nothing.
Freezing records no posting and does not change any balance. Accounts are
not frozen when opened.

## LEDGER-U6-R2

A frozen account cannot send money (decision DEC-U6-FREEZE-SCOPE):

- `Ledger.debit` from a frozen account is refused with
  `Error (AccountFrozen id)`. The checks are, in order: amount, unknown
  account, frozen, funds.
- `Ledger.transfer` whose `source` is frozen is refused with
  `Error (AccountFrozen source)`. The checks are, in order: amount, source
  exists, destination exists, same account, source frozen, funds.
- A frozen account still receives money: `Ledger.credit` and transfers
  *to* it work as before.
- A refusal records nothing.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
