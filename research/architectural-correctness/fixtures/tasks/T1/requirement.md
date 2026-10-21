# T1: Renewals at the command line

Requirements: LEND-T1-R1, LEND-T1-R2.

Members ask at the desk whether they can renew, and staff want to renew from the
command line. Renewals follow DEC-004 (`docs/decisions/DEC-004-renewals.md`). The
command line is `Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests
drive it with an in-memory store and a clock they control (see
`tests/Lending.Tests/Support.fs`).

## LEND-T1-R1

A new command `renew <copy>` renews the loan of that copy today, following DEC-004.
On success it prints

    c1 renewed, due 2026-04-13 (renewal 1 of 2)

with the new due date (yyyy-MM-dd), the number of renewals the loan has now had, and the
most renewals it may have. A refused renewal prints `error: ` followed by the
existing error text, for example `error: copy c1 is overdue`,
`error: copy c1 has already been renewed 2 times`, `error: copy c1 has holds waiting`,
`error: copy c9 is not on loan` or `error: unknown copy c9`. A refused renewal changes
nothing. `renew` with the wrong number of words prints `usage: renew <copy>`, and
`help` lists `renew <copy>` on its own line directly after `return <copy>`.

## LEND-T1-R2

`loans <member>` shows, for each loan, whether it can be renewed today. Each loan
line becomes

    c1 "Dune" due 2026-03-23, renewable

or, when it cannot be renewed, `, not renewable: ` followed by the reason DEC-004
gives: `overdue`, `renewed 2 of 2 times` (the renewals had, of the most allowed), or
`book has holds`. When more than one applies, the reason is the first in DEC-004's
list. Everything else in the listing is unchanged. A loan that `loans` shows as
renewable is renewed by `renew` on the same day, and one shown as not renewable is
refused for the same reason.

The existing test `borrowing lends a copy for 21 days` in
`tests/Lending.Tests/BaseTests.fs` expects the old listing; update its expectation
to the new line format.

Acceptance criteria: each statement above holds; existing commands keep their
output except the loan lines of `loans`; all tests pass with `dotnet test Lending.slnx`.
