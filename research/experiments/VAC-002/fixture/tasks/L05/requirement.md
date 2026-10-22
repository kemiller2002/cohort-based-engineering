# L05: Paying fines

Requirements: LEND-L05-R1, LEND-L05-R2, LEND-L05-R3. Owner: Finance.

## LEND-L05-R1

A new command `pay <member> <amount>` records a payment from a member and prints
`m1 paid 2.00, owes 1.50`. The amount is a number greater than 0 with at most two
decimals (`pay m1 2` and `pay m1 2.00` are the same); anything else prints
`error: invalid amount 'x'` (with the text given). A payment larger than what the
member owes prints `error: m1 owes only 1.50` and records nothing. An unknown member
prints `error: unknown member m9`.

## LEND-L05-R2

A payment is applied when it is made, to the member's fines oldest first (in the order
the fines were assessed): each fine takes as much as it still needs before the next
one gets anything. A payment never changes the amount of a fine (DEC-006); it records
how much of each fine has been paid. What a member owes (LEND-L04-R1, LEND-L04-R2) is
the unpaid part of their fines.

## LEND-L05-R3

A new command `fines <member>` lists the member's fines, oldest first, with the day
each was assessed, its amount and how much of it has been paid:

    fines for m1:
      c1 2026-03-26 0.75, paid 0.75
      c3 2026-04-02 2.00, paid 0.50

or `no fines for m1`. `help` lists `pay <member> <amount>` and `fines <member>`, in
that order, directly after `owes <member>`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
