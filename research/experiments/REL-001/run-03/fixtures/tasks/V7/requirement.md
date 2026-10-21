# V7: Account sweeps

Requirement: LEDGER-V7-R1.

Operations moves the whole balance of an account into another account, for
example to empty a customer's pocket accounts into their main account every
night. Implement in `src/Ledger/Ledger.fs`:

```fsharp
val sweep : source: AccountId -> target: AccountId -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

## LEDGER-V7-R1

`sweep` refuses, in this order: the source is not open,
`Error (UnknownAccount source)`; the target is not open,
`Error (UnknownAccount target)`; the source and the target are the same
account, `Error (SameAccount source)`.

When the source's balance is more than 0, `sweep` moves the whole balance
to the target as one transfer, reference `sweep`: one posting of minus the
balance on the source and one of plus the balance on the target, both dated
with the business date.

The two teams that use sweeps have each recorded a decision:

- **DEC-V7-EMPTY-NOOP** (Operations). The nightly job sweeps every pocket
  account without checking it first. Sweeping an account whose balance is 0
  succeeds: `sweep` returns `Ok` with the ledger unchanged.
- **DEC-V7-ONE-PAIR** (Audit). Audit counts sweeps from the journal, so every
  sweep that `sweep` accepts records exactly one pair of postings. A sweep
  that would record no postings is refused with `Error (InvalidAmount 0m)`.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
