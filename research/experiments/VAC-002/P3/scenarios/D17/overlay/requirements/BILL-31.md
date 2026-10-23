# BILL-31: Late fee preview

Requirements: BILL-31-R1, BILL-31-R2. Owner: Finance.

## BILL-31-R1

A new command `fee-preview <invoice>` shows the late fee the invoice is charged if it is overdue, as the late-fee
decision in force sets it, and whether it is overdue now: `i1 late fee 2.25 (overdue)` or
`i1 late fee 2.25 (not yet due)`. It charges nothing. An unknown invoice prints `error: unknown invoice i9`.

## BILL-31-R2

`help` lists `fee-preview <invoice>` directly after `run-late-fees`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
