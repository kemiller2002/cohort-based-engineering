# T2: Borrowing blocks everywhere

Requirements: LEND2-T2-R1, LEND2-T2-R2, LEND2-T2-R3, LEND2-T2-R4.

DEC-009 (`docs/decisions/DEC-009-borrowing-blocks.md`) blocks members who owe too
much from borrowing, placing holds and renewing, but today only borrowing is blocked,
and the desk cannot see who is blocked or why. What a member owes is their fines less
their payments, as `account` shows it. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests drive it with an
in-memory store and a clock they control (see `tests/Lending.Tests/Support.fs`).
The fields of `Ports` stay as they are.

## LEND2-T2-R1

A member who owes 5.00 or more cannot borrow or place a hold. `borrow` and `hold` by
such a member are refused, whatever the copy or book, with

    error: member m1 owes 5.25; borrowing is blocked until it is below 5.00
    error: member m1 owes 5.25; holds are blocked until it is below 5.00

(the amount owed with two decimals). An unknown member is still reported as
`error: unknown member m9`. The existing test `a member who owes 5.00 or more cannot
borrow` in `tests/Lending.Tests/BaseTests.fs` expects the old refusal text; update it
to the new one.

## LEND2-T2-R2

A loan whose borrower owes 5.00 or more cannot be renewed: `renew <copy>` prints

    error: member m1 owes 5.25; renewals are blocked until it is below 5.00

An unknown copy and a copy that is not on loan are reported as before; the block is
checked before the reasons DEC-004 gives.

## LEND2-T2-R3

A new command `standing <member>` tells the desk where a member stands:

    m1 (Ada Lovelace) owes 5.25: blocked from borrowing, holds and renewals
    m1 (Ada Lovelace) owes 0.75: in good standing

An unknown member prints `error: unknown member m9`. `standing` with the wrong number
of words prints `usage: standing <member>`, and `help` lists `standing <member>` on its
own line directly after `account <member>`.

## LEND2-T2-R4

`members` marks every blocked member by adding `, blocked` to their line, for example
`m1 Ada Lovelace (standard), 0 loans, blocked`. Other lines are unchanged.

Acceptance criteria: each statement above holds; existing commands keep their output
except where a statement above changes it; all tests pass with `dotnet test Lending.slnx`.
