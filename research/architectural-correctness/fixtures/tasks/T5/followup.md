# T5 follow-up: Staff fine waiver approved

Requirements: LEND-T5-F1.

Finance, the owner of DEC-006, has approved revision 2 of that decision. Record it in
`docs/decisions/DEC-006-fine-authority.md` and implement it:

> **DEC-006 revision 2 (approved by Finance).** Fines are still assessed only by the
> fine schedule (DEC-003) when a copy is returned. A fine assessed for a staff member
> is waived at the moment it is assessed, by the standing approval `DEC-006 rev 2`.
> Any other waiver still needs a named approver for the specific fine.

## LEND-T5-F1

When a staff member returns a copy late, the fine is assessed as before and waived
with approver `DEC-006 rev 2`. `return` prints it, for example
`c1 returned 3 days late, fine 0.75 (waived by DEC-006 rev 2)`, and `fines` lists it
as `waived by DEC-006 rev 2` with nothing owed for it. Fines of other members, and
the `waive` command, are unchanged.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
