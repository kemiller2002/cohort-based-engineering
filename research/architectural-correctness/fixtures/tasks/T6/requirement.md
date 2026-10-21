# T6: Hold pickup and expiry

Requirements: LEND-T6-R1, LEND-T6-R2, LEND-T6-R3, LEND-T6-R4.

Implement DEC-007 (`docs/decisions/DEC-007-hold-pickup.md`) together with the existing
holds rule DEC-005. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`.

## LEND-T6-R1

When a copy is returned and its book has a hold with no copy set aside, the copy is
set aside for the first such hold in the book's queue, until the return day plus 7
days (the pickup deadline). `return` then prints, after its usual text,
`, set aside for s1 until 2026-03-09`, for example
`c1 returned, set aside for s1 until 2026-03-09` or
`c1 returned 3 days late, fine 0.75, set aside for s1 until 2026-04-02`.

## LEND-T6-R2

A copy that is set aside can be borrowed only by the member it is set aside for;
anyone else gets `error: copy c1 is reserved for another member`. For a copy that is
not set aside, DEC-005 applies to the holds of its book that have no copy set aside:
it is lent only to the first of them, if there is one. Borrowing a copy of a book
removes the borrower's hold on that book, and with it any copy set aside for them,
which is then simply free.

## LEND-T6-R3

A new command `holds <book>` lists the book's queue in order:

    holds for b1 (Dune):
      1. s1, copy c1 set aside until 2026-03-09
      2. m1, waiting

or `no holds for b1 (Dune)`; an unknown book prints `error: unknown book b9`. A new
command `expire-holds` removes every hold whose pickup deadline is before today (a
hold can still be collected on its deadline day); the copy set aside for it becomes
free. It prints how many expired and one line each, ordered by copy id:

    expired holds: 1
      s1 for b1, copy c1

or `expired holds: 0`. With the wrong number of words they print
`usage: holds <book>` and `usage: expire-holds`; `help` lists `holds <book>` and
`expire-holds`, in that order, directly after `hold <member> <book>`.

## LEND-T6-R4

The program expires holds every time it starts:
`Lending.Host.Composition.startup : Ports -> string` runs the same expiry as
`expire-holds` and returns the same text, and `main` prints it before reading the
first command.

Acceptance criteria: each statement above holds; existing commands keep their output
except as stated; all tests pass with `dotnet test Lending.slnx`.
