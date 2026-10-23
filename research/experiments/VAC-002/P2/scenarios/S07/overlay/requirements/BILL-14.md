# BILL-14: Credit notes

Requirements: BILL-14-R1, BILL-14-R2. Owner: Finance.

## BILL-14-R1

A new command `credit <customer> <amount>` issues a credit note to a customer. The credit reduces what the customer
owes, and the command prints the new balance: `c1 credited 20.00, balance 80.00`. An unknown customer prints
`error: unknown customer c9`; an amount that is not a positive amount of money prints `error: invalid amount x`.

## BILL-14-R2

`help` lists `credit <customer> <amount>` directly after `balance <customer>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Billing.slnx` passes.
