# BILL-15: Reminder fees

Requirements: BILL-15-R1, BILL-15-R2. Owner: Finance.

## BILL-15-R1

An invoice that is still unpaid more than 30 days after its due date is charged a reminder fee of 5.00, in addition
to its late fee. The reminder fee is charged once per invoice, when late fees are run, and then forms part of what is
outstanding. `run-late-fees` reports both counts: `late fees applied: 1, reminder fees applied: 0`.

## BILL-15-R2

`show <invoice>` shows the reminder fee after the late fee:
`i1 c1 amount 100.00, late fee 2.00, reminder fee 5.00, paid 0.00, outstanding 107.00, due 2026-04-01`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
