# L03: Renewing from the command line

Requirements: LEND-L03-R1, LEND-L03-R2. Owner: Head of Lending.

## LEND-L03-R1

A new command `renew <copy>` renews a loan under DEC-004 and prints
`c1 renewed, due 2026-04-13 (renewal 1 of 2)`. When the renewal is refused it prints
the reason DEC-004 gives, one of:

    error: copy c1 is overdue
    error: copy c1 has already been renewed 2 times
    error: copy c1 has holds waiting

A copy that is not on loan prints `error: copy c1 is not on loan`; an unknown copy
prints `error: unknown copy c9`. `help` lists `renew <copy>` directly after
`return <copy>`.

## LEND-L03-R2

`loans <member>` marks renewed loans: a loan renewed once is shown as
`  c1 "Dune" due 2026-04-13 (renewed 1)`; loans never renewed are shown as before.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
