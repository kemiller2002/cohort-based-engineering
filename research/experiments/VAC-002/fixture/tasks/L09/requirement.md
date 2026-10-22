# L09: Due dates on open days

Requirements: LEND-L09-R1, LEND-L09-R2. Owner: Head of Lending. Implements DEC-001 and
DEC-004 revision 2.

## LEND-L09-R1

A due date never falls on a day the library is closed. When the due date that DEC-001
(borrowing) or DEC-004 (renewal) gives falls on a closed day, it moves to the next day
the library is open. The library's calendar is the vendored OpenDays package
(`src/Lending.Transition/Vendor/`): it is closed on Sundays and public holidays. For
example, a copy borrowed on 2026-05-04 is due on 2026-05-26, because 2026-05-25 is a
public holiday.

## LEND-L09-R2

A new command `open <date>` prints `2026-05-25 is closed; next open day 2026-05-26` or
`2026-05-26 is open`. A date that is not written `yyyy-MM-dd` prints
`error: invalid date 'x' (yyyy-MM-dd)`. `help` lists `open <date>` directly after
`notices <member>`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
