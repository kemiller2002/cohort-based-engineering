# L10: Hold pickup

Requirements: LEND-L10-R1, LEND-L10-R2, LEND-L10-R3. Owner: Head of Lending. Implements
DEC-007 revision 2 (`docs/decisions/DEC-007-hold-pickup.md`) together with DEC-005.

## LEND-L10-R1

When a copy is returned and its book has holds, the copy is set aside for the first
member in the book's queue who has no copy set aside yet and is not suspended
(LEND-L01). The pickup deadline is the return day plus 7 days, moved to the next open
day when the library is closed that day (DEC-007 revision 2). `return` then prints,
after its usual text, `, set aside for s1 until 2026-03-09`, for example
`c1 returned, set aside for s1 until 2026-03-09` or
`c1 returned 3 days late, fine 0.75, set aside for s1 until 2026-04-02`.

## LEND-L10-R2

A copy that is set aside can be borrowed only by the member it is set aside for; anyone
else gets `error: copy c1 is reserved for another member`. A copy that is not set aside
follows DEC-005 for the holds of its book that have no copy set aside: it is lent only
to the first of those members, if there is one. Borrowing a copy of a book removes the
borrower's hold on that book, and with it any copy set aside for them, which is then
simply free.

## LEND-L10-R3

A new command `holds <book>` lists the book's queue in order:

    holds for b1 (Dune):
      1. s1, copy c1 set aside until 2026-03-09
      2. m1, waiting

or `no holds for b1 (Dune)`; an unknown book prints `error: unknown book b9`. A new
command `expire-holds` removes every hold whose pickup deadline is before today (a copy
can still be collected on its deadline day); the copy set aside for it becomes free. It
prints how many expired and one line for each, ordered by copy id:

    expired holds: 1
      s1 for b1, copy c1

or `expired holds: 0`. `help` lists `holds <book>` and `expire-holds`, in that order,
directly after `open <date>`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
