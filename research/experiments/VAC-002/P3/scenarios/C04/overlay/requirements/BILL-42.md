# BILL-42: Shipping charge lookup

Requirements: BILL-42-R1, BILL-42-R2. Owner: Logistics.

## BILL-42-R1

A new command `shipping <customer>` prints the shipping charge for a delivery to the customer, as DEC-B13 sets it:
`c1 shipping 15.00`. It changes nothing. An unknown customer prints `error: unknown customer c9`.

## BILL-42-R2

`help` lists `shipping <customer>` directly after `balance <customer>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Billing.slnx` passes.
