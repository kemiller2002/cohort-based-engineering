# BILL-43: Collection interest

Requirements: BILL-43-R1, BILL-43-R2. Owner: Credit Control.

## BILL-43-R1

A new command `run-interest` charges the collection interest that DEC-B14 decides on every invoice that owes it, and
prints how many invoices were charged: `interest charged: 1`. Charged interest is part of what is outstanding on the
invoice and of the customer's balance. `show` is unchanged.

## BILL-43-R2

`help` lists `run-interest` directly after `run-late-fees`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
