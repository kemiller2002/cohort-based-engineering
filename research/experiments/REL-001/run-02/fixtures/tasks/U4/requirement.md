# U4: Recent activity, then reversals

Category: moderate. Requirements: LEDGER-U4-R1, LEDGER-U4-R2.
Decision: DEC-U4-SHARED-VIEW.

This work has two steps. Implement LEDGER-U4-R1 first, then LEDGER-U4-R2.
The work is complete only when both are implemented and all tests pass at
the same commit.

## LEDGER-U4-R1

Implement in `src/Ledger/Ledger.fs`:

```fsharp
val recent : id: AccountId -> count: int -> ledger: LedgerState -> Result<Posting list, LedgerError>
```

`Ledger.recent id count ledger` returns the `count` most recent postings of
the account, newest first, or all of them when there are fewer than
`count`. A `count` of zero or less gives an empty list. An unknown account
is refused with `Error (UnknownAccount id)`.

`recent` must be built on the shared helper `Ledger.postingsOf`
(decision DEC-U4-SHARED-VIEW): it shows exactly the postings that
`postingsOf` lists, in the same order, so that every per-account view of
the ledger agrees.

## LEDGER-U4-R2

Postings can be reversed. Add two cases to `LedgerError` in
`src/Ledger/Domain.fs`: `UnknownReference of string` and
`AlreadyReversed of string`. Implement in `src/Ledger/Ledger.fs`:

```fsharp
val reverse : reference: string -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

- `Ledger.reverse reference ledger` records, for every posting whose
  reference is exactly `reference` (on any account), one compensating
  posting on the same account with the negated amount and reference
  `reversal:<reference>`, dated with the ledger's business date, in the
  order the original postings were recorded.
- It is refused with `Error (UnknownReference reference)` when no posting
  carries `reference`, or when `reference` itself starts with `reversal:`.
  It is refused with `Error (AlreadyReversed reference)` when `reference`
  was already reversed. A refusal records nothing.
- Change the shared helper `Ledger.postingsOf` so that it no longer lists
  reversed postings or their compensating `reversal:` postings. Balances
  are unchanged by a reversal's hiding (each hidden pair nets to zero), and
  `Ledger.postings` still lists the full journal, including both.

Reusing a reference after it has been reversed is outside this requirement.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
