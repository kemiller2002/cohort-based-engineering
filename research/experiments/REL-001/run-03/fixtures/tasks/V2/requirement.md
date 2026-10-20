# V2: Largest balances

Requirement: LEDGER-V2-R1.

The treasury dashboard shows the accounts holding the most money. Add an
error case to `LedgerError` in `src/Ledger/Domain.fs`:

```fsharp
| InvalidCount of int
```

and implement in `src/Ledger/Ledger.fs`:

```fsharp
val richest : count: int -> ledger: LedgerState -> Result<(AccountId * decimal) list, LedgerError>
```

## LEDGER-V2-R1

1. A negative `count` is refused with `Error (InvalidCount count)`.
2. Otherwise the result is `Ok` with the `count` open accounts that have the
   largest balances, each paired with its balance, largest first. Every open
   account takes part, including accounts with a zero balance.
3. Accounts with equal balances are ordered by account id, ascending,
   comparing the id strings ordinally (character codes, so `"B"` comes before
   `"a"`).
4. A `count` of 0 gives `Ok []`; a `count` larger than the number of open
   accounts gives every open account.

The function only reads the ledger; it records nothing.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
