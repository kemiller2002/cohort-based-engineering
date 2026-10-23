# BILL-21: Customer discounts

Requirements: BILL-21-R1, BILL-21-R2. Owner: Finance.

## BILL-21-R1

Invoices apply the customer discounts that DEC-B06 and DEC-B07 decide. The discount is taken off the amount given to
`invoice`, and the invoice is issued for what remains. When a discount applies, `invoice` prints the amount, the
discount and the amount invoiced: `i1 issued to c3: 100.00 - discount 5.00 = 95.00 due 2026-04-01`. When no discount
applies, the output is unchanged.

## BILL-21-R2

`show`, balances and late fees use the amount invoiced, after the discount.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
