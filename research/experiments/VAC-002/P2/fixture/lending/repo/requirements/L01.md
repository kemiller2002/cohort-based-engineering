# L01: Member suspensions

Requirements: LEND-L01-R1, LEND-L01-R2, LEND-L01-R3. Owner: Head of Lending.

## LEND-L01-R1

`suspend <member> <reason>` suspends a member and prints `m1 suspended: <reason>`. The
reason is one word or a quoted phrase, for example `suspend m1 "damaged books"` prints
`m1 suspended: damaged books`. Suspending a member who is already suspended prints
`error: member m1 is already suspended`. `reinstate <member>` lifts the suspension and
prints `m1 reinstated`; reinstating a member who is not suspended prints
`error: member m1 is not suspended`. An unknown member prints `error: unknown member m9`.

## LEND-L01-R2

A suspended member cannot borrow, place holds or renew loans. Each of these prints
`error: member m1 is suspended`. The suspension is checked as soon as the member is
known, before every other lending rule. Returning a copy is not affected.

## LEND-L01-R3

`member <member>` shows the member and their standing:
`m1 Ada Lovelace (standard), active` or
`m1 Ada Lovelace (standard), suspended: damaged books`.

`help` lists the three new commands, `suspend <member> <reason>`, `reinstate <member>`
and `member <member>`, in that order, directly after `loans <member>`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
