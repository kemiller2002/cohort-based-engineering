# BILL-32: Reminder fees

Requirements: BILL-32-R1, BILL-32-R2. Owner: Finance.

## BILL-32-R1

A new command `run-reminders` charges the reminder fee that DEC-B09 decides on every invoice that owes it, and
prints how many were charged: `reminder fees applied: 1`. A charged reminder fee is part of what is outstanding on
the invoice and of the customer's balance. `show` is unchanged.

## BILL-32-R2

`help` lists `run-reminders` directly after `run-late-fees`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
