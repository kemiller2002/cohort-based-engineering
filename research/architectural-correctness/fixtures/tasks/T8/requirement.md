# T8: ISBN-13 validation

Requirements: LEND-T8-R1, LEND-T8-R2.

Cataloguing mistakes in ISBNs are only found when a supplier rejects an order. Check
the ISBN when a book is added. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`.

## LEND-T8-R1

A book's ISBN must be a valid ISBN-13: after removing hyphens and spaces it is 13
digits, it starts with 978 or 979, and its check digit is right (the digits, weighted
1, 3, 1, 3, … from the left, add up to a multiple of 10). `add-book` with any other
ISBN is refused with `error: invalid ISBN-13 '<the ISBN as typed>'`, for example
`error: invalid ISBN-13 '978-0-441-01359-4'`, and adds nothing. The rule holds for
every way a book is added (`Lending.Transition.Catalog.addBook` too).

## LEND-T8-R2

A book is stored with its ISBN as the 13 digits only: `add-book b1 978-0-441-01359-3
Dune Herbert` stores `9780441013593`. `add-book`'s output is unchanged.

The existing test `renewal extends the due date and is limited` in
`tests/Lending.Tests/BaseTests.fs` builds a book with ISBN `x`; give it a valid ISBN.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
