# T3: Idempotent period close with maintenance fee

Complexity: medium (includes a design decision). Requirements: LEDGER-T3-R1,
LEDGER-T3-R2. Decision: DEC-T3-IDEMPOTENCY-KEY.

Implement `Ledger.closePeriod periodId ledger`, returning
`Ok (summary, ledger')`.

## LEDGER-T3-R1

Closing a period charges a maintenance fee of exactly 1.00 to every account
whose balance is at least 1.00, as one posting of `-1.00` with reference
`fee:<periodId>`. Accounts with a balance below 1.00 are charged nothing and
are never overdrawn. The summary's `PeriodId` is `periodId`, `Fees` maps
every account to the fee charged at this close (1.00 or 0), and `Balances`
maps every account to its balance after the close.

## LEDGER-T3-R2

Closing is idempotent per period: closing a period that was already closed
records no posting and returns the summary recorded at its first close,
unchanged, even if balances or accounts changed since. Closing a different
period id is a new close and charges fees again.

## Design decision DEC-T3-IDEMPOTENCY-KEY

Idempotency is keyed by the period id and the first close's summary is kept
in the ledger state. It must not be inferred from the presence of fee
postings (a close that charged nobody leaves no posting), and a repeated
close is not an error.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept (you may add fields to `LedgerState` and update
`Ledger.empty`); all tests pass with `dotnet test Ledger.slnx`.
