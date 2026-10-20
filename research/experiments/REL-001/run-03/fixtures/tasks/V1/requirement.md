# V1: Closing accounts

Requirement: LEDGER-V1-R1.

Customers can close an account they no longer use. Add an error case to
`LedgerError` in `src/Ledger/Domain.fs`:

```fsharp
| NonZeroBalance of AccountId * decimal
```

and implement in `src/Ledger/Ledger.fs`:

```fsharp
val closeAccount : id: AccountId -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

## LEDGER-V1-R1

`Ledger.closeAccount` refuses, and changes nothing, when:

1. the account is not open (it was never opened, or it is already closed):
   `Error (UnknownAccount id)`. This check comes first.
2. the account's balance is not zero: `Error (NonZeroBalance (id, balance))`,
   where `balance` is the account's current balance.

Otherwise it closes the account:

- the account is no longer one of the ledger's accounts: `balance`,
  `credit`, `debit` and `transfer` treat it as an unknown account, and a
  period close no longer charges or lists it;
- no posting is recorded, and the account's earlier postings stay in the
  journal unchanged;
- a closed account id is never reused: `openAccount` with that id is
  refused with `Error (DuplicateAccount id)`, whether or not the account ever
  had postings.

How closed accounts are remembered is up to you.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
