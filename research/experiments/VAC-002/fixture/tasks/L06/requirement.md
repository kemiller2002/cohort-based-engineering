# L06: Waiving fines

Requirements: LEND-L06-R1, LEND-L06-R2. Owner: Finance. Implements DEC-006 revision 2
(`docs/decisions/DEC-006-fine-authority.md`).

## LEND-L06-R1

A new command `waive <copy> <approver>` waives the most recently assessed fine for that
copy that is not yet waived, when the approver is one of the branch managers named in
DEC-006. Names with spaces are quoted: `waive c1 "Grace Hopper"` prints
`fine for c1 of 0.75 (2026-03-26) waived by Grace Hopper`. Otherwise it prints one of

    error: Bob Smith is not a branch manager
    error: no fine to waive for c1
    error: unknown copy c9

`help` lists `waive <copy> <approver>` directly after `fines <member>`.

## LEND-L06-R2

A waived fine no longer counts towards what its member owes: it is left out of `owes`,
of the borrowing restriction (LEND-L04-R2) and of the fines a payment is applied to
(LEND-L05-R2). What was paid on it before the waiver stays recorded; nothing is
refunded. `fines` shows a waived fine with its approver:
`  c1 2026-03-26 0.75, paid 0.25, waived by Grace Hopper`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
