# BILL-12: Sales tax on invoices

Requirements: BILL-12-R1, BILL-12-R2. Owner: Finance.

## BILL-12-R1

Invoices add sales tax as DEC-B04 decides. `invoice` prints the amount, the tax and the total:
`i1 issued to c1: 100.00 + tax 13.00 = 113.00 due 2026-04-01`.

## BILL-12-R2

`show <invoice>` shows the tax after the amount, and what is outstanding includes it:
`i1 c1 amount 100.00, tax 13.00, late fee 0.00, paid 0.00, outstanding 113.00, due 2026-04-01`. A customer's balance
includes the tax on their invoices.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
