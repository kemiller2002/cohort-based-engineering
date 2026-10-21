# T8 follow-up: Older ISBNs

Requirements: LEND-T8-F1.

Donated books often carry only a 10-digit ISBN.

## LEND-T8-F1

`add-book` (and `Catalog.addBook`) also accepts a valid ISBN-10: after removing
hyphens and spaces it is 9 digits followed by a check character that is a digit or
`X` (worth 10), and the ten values, weighted 10, 9, 8, … 1 from the left, add up to
a multiple of 11. Such a book is stored with the equivalent ISBN-13: `978`, then the
first 9 digits, then the ISBN-13 check digit for those 12 digits. For example
`0-441-01359-7` is stored as `9780441013593`. Any ISBN that is neither a valid
ISBN-13 nor a valid ISBN-10 is refused with `error: invalid ISBN '<as typed>'`
(this replaces the `invalid ISBN-13` text; update the T8 acceptance test that expects
the old text).

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
