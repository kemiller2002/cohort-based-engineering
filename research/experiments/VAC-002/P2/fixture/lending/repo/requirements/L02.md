# L02: Overdue report

Requirements: LEND-L02-R1, LEND-L02-R2. Owner: Head of Lending.

## LEND-L02-R1

A new command `overdue` lists every loan that is past its due date as of today, most
overdue first; loans that are equally overdue are listed by copy id:

    overdue loans: 2
      c1 "Dune", m1 Ada Lovelace, due 2026-03-23, 3 days overdue
      c3 "Emma", s1 Sam Student, due 2026-03-25, 1 day overdue

(`1 day`, otherwise `N days`). With no overdue loans it prints `overdue loans: 0`. A
loan due today is not overdue. `help` lists `overdue` directly after `member <member>`.

## LEND-L02-R2

The number of days overdue is the number of days late under the fine schedule
(DEC-003): it must always agree with the days late that returning the copy today would
report.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
