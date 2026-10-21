# T1 follow-up: Renewal limits by member type

Requirements: LEND-T1-F1.

Finance and the Head of Lending have revised DEC-004: the most renewals a loan may
have now depends on the borrower's member type. Update
`docs/decisions/DEC-004-renewals.md` (revision 2) and the system.

## LEND-T1-F1

The renewal limit of a loan is the borrower's: standard 2, student 1, staff 4. Every
other part of DEC-004 is unchanged. `renew` and `loans` use the borrower's limit
everywhere they used the single limit before: `renew` prints, for example,
`c1 renewed, due 2026-04-13 (renewal 1 of 4)` for a staff member, a refused renewal
prints `error: copy c1 has already been renewed 1 times` for a student's loan renewed
once, and `loans` shows `not renewable: renewed 1 of 1 times` for it.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
