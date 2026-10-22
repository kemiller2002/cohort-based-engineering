# T1: Renewals at the desk

Requirements: LEND2-T1-R1, LEND2-T1-R2, LEND2-T1-R3.

Members ask at the desk which of their loans they can renew, and staff want to renew
all of a member's loans in one go. Renewals follow DEC-004
(`docs/decisions/DEC-004-renewals.md`). The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests drive it with an
in-memory store and a clock they control (see `tests/Lending.Tests/Support.fs`).
The fields of `Ports` stay as they are.

## LEND2-T1-R1

`loans <member>` shows, for each loan, whether it can be renewed today. Each loan
line becomes

    c1 "Dune" due 2026-03-23, renewable

or, when it cannot be renewed, `, not renewable: ` followed by the reason DEC-004
gives: `overdue`, `renewed 2 of 2 times` (the renewals had, of the most allowed), or
`book has holds`. When more than one applies, the reason is the first in DEC-004's
list. Everything else in the listing is unchanged. The existing test
`borrowing lends a copy for 21 days` in `tests/Lending.Tests/BaseTests.fs` expects the
old line; update its expectation to the new format.

## LEND2-T1-R2

`renew <copy>` reports the renewal count: on success it prints

    c1 renewed, due 2026-04-13 (renewal 1 of 2)

with the new due date, the number of renewals the loan has now had and the most it may
have. A refused renewal prints `error: ` followed by the existing error text, for
example `error: copy c1 is overdue`, `error: copy c1 has already been renewed 2 times`,
`error: copy c1 has holds waiting`, `error: copy c9 is not on loan` or
`error: unknown copy c9`, and changes nothing. A loan that `loans` shows as renewable
is renewed by `renew` on the same day, and one shown as not renewable is refused for
the same reason. Update the existing test `renewing moves the due date by 21 days` to
the new success line.

## LEND2-T1-R3

A new command `renew-all <member>` renews, today, every loan of the member that can be
renewed, taking the loans in the order `loans` lists them before any is renewed. It
prints one line per loan, then a summary:

    c1 renewed, due 2026-04-13 (renewal 1 of 2)
    c3 not renewed: book has holds
    renewed 1 of 2 loans for m1

A loan that is not renewed shows the same reason `loans` gives. A member with no loans
gets `no loans for m1 (Ada Lovelace)`, and an unknown member `error: unknown member m9`.
`renew-all` with the wrong number of words prints `usage: renew-all <member>`, and
`help` lists `renew-all <member>` on its own line directly after `renew <copy>`.

Acceptance criteria: each statement above holds; existing commands keep their output
except where a statement above changes it; all tests pass with `dotnet test Lending.slnx`.
