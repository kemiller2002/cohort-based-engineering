# BILL-13: Approved discounts

Requirements: BILL-13-R1, BILL-13-R2. Owner: Finance.

## BILL-13-R1

Invoices apply the discounts that Finance has approved (`docs/approvals/`). `invoice` prints the discounted amount
and the discount: `i1 issued to c2: 90.00 (discount 10.00) due 2026-04-01`. An invoice without a discount prints as
before.

## BILL-13-R2

The discounted amount is the invoice's amount everywhere: `show`, the balance and the late fee use it.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
