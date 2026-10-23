# BILL-22: Payment terms

Requirements: BILL-22-R1, BILL-22-R2. Owner: Sales.

## BILL-22-R1

A new command `terms <customer>` prints how many days the customer has to pay an invoice: `c1 pays within 30 days`.
An unknown customer prints `error: unknown customer c9`. `help` lists `terms <customer>` directly after
`balance <customer>`.

## BILL-22-R2

Premium customers pay within 45 days: their invoices are due 45 days after they are issued, and `terms` prints
`c3 pays within 45 days`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
