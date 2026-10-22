# T5 follow-up: Waivers

Requirements: LEND2-T5-F1.

Branch managers waive fines on paper. DEC-006 allows a waiver given by a named approver
for a specific fine; the desk now wants to record them.

## LEND2-T5-F1

A new command `waive <member> <copy> <approver>` waives the member's earliest fine for
that copy that still has something unpaid, and prints `fine for c1 waived by Mira Manager`.
Waiving a fine waives what is still unpaid on it; what was already paid on it stays
paid. A waived fine no longer counts towards what the member owes and takes no further
payments: later payments go to the member's other fines, oldest first. In `account` a
waived fine ends with `, waived by Mira Manager` when nothing had been paid on it, and
with `, paid 0.50 of 0.75, rest waived by Mira Manager` when part had been paid. It is
refused, changing nothing, with `error: m1 has no fine for c1 to waive` when the member
has no such fine, `error: a waiver needs an approver` when the approver is empty, and
`error: unknown member m9` for an unknown member. `waive` with the wrong number of
words prints `usage: waive <member> <copy> <approver>`, and `help` lists
`waive <member> <copy> <approver>` directly after `pay <member> <amount>`.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
