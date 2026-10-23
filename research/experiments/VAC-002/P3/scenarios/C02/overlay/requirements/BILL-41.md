# BILL-41: Quotes

Requirements: BILL-41-R1, BILL-41-R2. Owner: Sales Operations.

## BILL-41-R1

A new command `quote <customer> <amount>` tells a customer when an invoice for that amount, issued today, would have
to be paid under the payment-terms decision in force: `quote c1 100.00 payable by 2026-03-23`. It issues nothing. An
unknown customer prints `error: unknown customer c9`, and an amount that is not a positive amount of money prints
`error: invalid amount x`.

## BILL-41-R2

`help` lists `quote <customer> <amount>` directly after `invoice <invoice> <customer> <amount>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
