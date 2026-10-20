# V8: Daily withdrawal limit

Requirements: LEDGER-V8-R1, LEDGER-V8-R2.

Cash withdrawals are limited to 500.00 per account per business day. Add an
error case to `LedgerError` in `src/Ledger/Domain.fs`:

```fsharp
| DailyLimitExceeded of AccountId * decimal
```

and implement in `src/Ledger/Ledger.fs`:

```fsharp
val withdraw : id: AccountId -> amount: decimal -> ledger: LedgerState -> Result<LedgerState, LedgerError>
val withdrawnToday : id: AccountId -> ledger: LedgerState -> Result<decimal, LedgerError>
```

A withdrawal is a posting on the account with reference `withdraw`.

## LEDGER-V8-R1

`withdraw id amount` refuses, and records nothing, in this order:

1. `amount` zero or negative: `Error (InvalidAmount amount)`;
2. the account is not open: `Error (UnknownAccount id)`;
3. `amount` is more than the balance: `Error (InsufficientFunds (id, amount))`;
4. the account's withdrawals dated with the current business date, plus
   `amount`, would come to more than 500.00:
   `Error (DailyLimitExceeded (id, remaining))`, where `remaining` is 500.00
   minus what the account has already withdrawn that business date.

Otherwise it records one posting of minus `amount`, reference `withdraw`,
dated with the business date. The limit is inclusive: withdrawals on one
business date may add up to exactly 500.00. Only withdrawals count towards
the limit (not debits, transfers or fees); refused withdrawals do not count;
the limit starts again when the business date moves on.

## LEDGER-V8-R2

`withdrawnToday id` is the total amount the account has withdrawn on the
current business date, as a positive number (0 when none);
`Error (UnknownAccount id)` for an account that is not open.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
