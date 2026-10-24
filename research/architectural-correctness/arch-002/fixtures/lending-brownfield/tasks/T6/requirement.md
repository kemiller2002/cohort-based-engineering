# T6: Finding books and copies

Requirements: LEND2-T6-R1, LEND2-T6-R2, LEND2-T6-R3.

Members ask the desk whether the library has a book and where its copies are. Copies
are shelved at branches (DEC-011); a copy is *on shelf* when it is not on loan. The
command line is `Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests
drive it with an in-memory store and a clock they control (see
`tests/Lending.Tests/Support.fs`). The fields of `Ports` stay as they are.

## LEND2-T6-R1

A new command `search <text>` lists the books whose title or author contains the text,
ignoring case, in book id order, each with how many of its copies are on shelf:

    2 books match "e":
      b1 "Dune" by Frank Herbert: 1 of 2 copies on shelf
      b2 "Emma" by Jane Austen: 1 of 1 copies on shelf

When no book matches it prints `no books match "xyz"`.

## LEND2-T6-R2

A new command `copies <book>` lists the book's copies in copy id order with their
branch and whether they are on loan:

    copies of b1 (Dune):
      c1 at main, on loan, due 2026-03-23
      c2 at east, on shelf

A book without copies prints `no copies of b3 (Atlas)`, and an unknown book
`error: unknown book b9`.

## LEND2-T6-R3

A new command `branches` lists every branch in branch id order with its number of
copies and how many are on shelf:

    branches:
      east East Branch: 1 copies, 1 on shelf
      main Main Library: 2 copies, 1 on shelf

For all three: with the wrong number of words they print `usage: search <text>`,
`usage: copies <book>` and `usage: branches`, and `help` lists `search <text>`,
`copies <book>` and `branches`, in that order, directly after `holds <book>`.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
