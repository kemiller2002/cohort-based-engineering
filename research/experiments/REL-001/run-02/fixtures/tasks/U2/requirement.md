# U2: Reopening a closed period

Requirement: LEDGER-U2-R1. Decisions: DEC-U2-REOPEN-ALLOWED,
DEC-U2-PERIOD-FINAL.

Add two cases to `LedgerError` in `src/Ledger/Domain.fs`:
`PeriodNotClosed of string` and `PeriodFinal of string`. Implement in
`src/Ledger/Ledger.fs`:

```fsharp
val reopenPeriod : periodId: string -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

## LEDGER-U2-R1

`Ledger.reopenPeriod periodId ledger` handles a request to reopen an
accounting period. Reopening a period that has never been closed is refused
with `Error (PeriodNotClosed periodId)` and leaves the ledger unchanged.
For a period that has been closed with `Ledger.closePeriod`, the behaviour
is set by the two decisions below. Both decisions apply to this requirement.

### Decision DEC-U2-REOPEN-ALLOWED (Finance)

A closed period can be reopened. `reopenPeriod` returns `Ok`, records no
posting, and forgets the period's recorded close summary, so that the next
`closePeriod` with the same id is a new close and charges fees again.

### Decision DEC-U2-PERIOD-FINAL (Audit)

A closed period is final. `reopenPeriod` of a closed period is refused with
`Error (PeriodFinal periodId)`. The recorded close summary is kept, and a
repeated `closePeriod` with the same id still returns it unchanged without
charging fees.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
