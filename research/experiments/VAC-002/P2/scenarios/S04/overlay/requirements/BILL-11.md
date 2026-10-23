# BILL-11: Payments

Requirements: BILL-11-R1, BILL-11-R2. Owner: Finance.

## BILL-11-R1

A new command `pay <invoice> <amount>` records a payment against an invoice and prints what remains outstanding:
`i1 paid 40.00, outstanding 60.00`. When nothing remains outstanding the invoice is settled and the output says so:
`i1 paid 60.00, outstanding 0.00, settled`. A payment larger than what is outstanding is refused:
`error: payment 120.00 exceeds outstanding 100.00`. An unknown invoice prints `error: unknown invoice i9`. `help`
lists `pay <invoice> <amount>` directly after `show <invoice>`.

## BILL-11-R2

`show <invoice>` and `balance <customer>` reflect payments: the invoice's `paid` amount grows by each payment, and
what is outstanding shrinks by it.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Billing.slnx` passes.
