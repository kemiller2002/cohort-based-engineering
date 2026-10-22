# T5: Fines at the desk

Requirements: LEND-T5-R1, LEND-T5-R2, LEND-T5-R3.

The desk cannot see what a member owes, and branch managers waive fines on paper.
Fines are assessed on return (DEC-003); see also DEC-006. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`.

## LEND-T5-R1

A new command `fines <member>` lists the member's fines in the order they were
assessed, then what the member owes (the fines not waived):

    fines for m1 (Ada Lovelace):
      c1 0.75 assessed 2026-03-26
      c3 2.50 assessed 2026-04-02, waived by Mira Manager
    owed: 0.75

Amounts have two decimals. A member with no fines gets
`no fines for m1 (Ada Lovelace)`, and an unknown member `error: unknown member m9`.

## LEND-T5-R2

A new command `waive <member> <copy> <approver>` waives the member's fine for that
copy, recording the approver's name, and prints
`fine for c1 waived by Mira Manager`. When the member has more than one fine for the
copy that is not waived, the earliest one is waived. When there is none, it prints
`error: m1 has no fine for c1 to waive`; an empty approver prints
`error: a waiver needs an approver`. A waived fine stays in the list, marked as
above, and no longer counts towards what the member owes.

## LEND-T5-R3

Staff are not to be charged. When a staff member returns a copy late, the desk
(the command line) waives the fine straight away with approver `desk`, so that
`fines` shows nothing owed for staff.

For all three: `fines` and `waive` with the wrong number of words print
`usage: fines <member>` and `usage: waive <member> <copy> <approver>`, and `help`
lists those two lines directly after `loans <member>`.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
