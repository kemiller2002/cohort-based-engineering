# L04: Money owed

Requirements: LEND-L04-R1, LEND-L04-R2, LEND-L04-R3.
Owners: Head of Lending (R1, R2); Staff Services (R3).

## LEND-L04-R1

A new command `owes <member>` prints the total of the member's fines:
`m1 owes 1.50`, or `m1 owes 0.00` when there are none. An unknown member prints
`error: unknown member m9`. `help` lists `owes <member>` directly after
`overdue`.

## LEND-L04-R2

A member who owes more than 5.00 cannot borrow: the borrow prints
`error: member m1 owes 5.25`. A member who owes exactly 5.00 may borrow.

## LEND-L04-R3

Staff members must always be able to borrow while they are below their loan limit
(DEC-002). A staff member's borrow is never refused for any other reason.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
