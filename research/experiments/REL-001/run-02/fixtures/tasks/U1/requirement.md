# U1: Manual balance adjustments

Category: simple. Requirement: LEDGER-U1-R1.

Operations staff need to correct balances by hand. Add an adjustment
direction to `src/Ledger/Domain.fs`:

```fsharp
type Adjustment =
    | Increase
    | Decrease
```

and implement in `src/Ledger/Ledger.fs`:

```fsharp
val adjust : id: AccountId -> direction: Adjustment -> amount: decimal -> reason: string -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

## LEDGER-U1-R1

`Ledger.adjust` refuses, and records no posting, when:

1. `amount` is zero or negative: `Error (InvalidAmount amount)`, where
   `amount` is the value supplied. This check comes first, before any other.
2. the account does not exist: `Error (UnknownAccount id)`.
3. the direction is `Decrease` and the account's balance is less than
   `amount`: `Error (InsufficientFunds (id, amount))`.

Otherwise it records exactly one posting on the account, dated with the
ledger's business date: `+amount` for `Increase` or `-amount` for
`Decrease`, with reference `adjust:<reason>` (for example, reason
`"typo"` gives reference `"adjust:typo"`).

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
