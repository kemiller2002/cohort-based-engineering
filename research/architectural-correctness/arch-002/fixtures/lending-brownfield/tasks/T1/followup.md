# T1 follow-up: Renewal limits by member type

Requirements: LEND2-T1-F1.

Finance and the Head of Lending have revised DEC-004: the most renewals a loan may
have now depends on the borrower's member type. Update
`docs/decisions/DEC-004-renewals.md` (revision 2) and the system.

## LEND2-T1-F1

The renewal limit of a loan is the borrower's: standard 2, student 1, staff 4. Every
other part of DEC-004 is unchanged. `renew`, `renew-all` and `loans` use the borrower's
limit everywhere they used the single limit before: `renew` prints, for example,
`c1 renewed, due 2026-04-13 (renewal 1 of 4)` for a staff member's loan; a student's
loan renewed once is refused with `error: copy c1 has already been renewed 1 times`,
`loans` shows it as `not renewable: renewed 1 of 1 times`, and `renew-all` reports it
as `c1 not renewed: renewed 1 of 1 times`.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
