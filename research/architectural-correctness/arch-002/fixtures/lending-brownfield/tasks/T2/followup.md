# T2 follow-up: Blocking balance by member type

Requirements: LEND2-T2-F1.

Finance has revised DEC-009: students are blocked sooner and staff later. Update
`docs/decisions/DEC-009-borrowing-blocks.md` (revision 2) and the system.

## LEND2-T2-F1

The balance at which a member is blocked depends on their member type: standard 5.00,
student 2.00, staff 10.00. A member is blocked when they owe their type's amount or
more. Everywhere the block applies (`borrow`, `hold`, `renew`, `standing`, `members`)
it uses the member's amount, and the refusals name it, for example
`error: member s1 owes 2.25; borrowing is blocked until it is below 2.00`. Everything
else in DEC-009 is unchanged.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
