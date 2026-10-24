# T3 follow-up: Stock imports and held copies

Requirements: LEND2-T3-F1, LEND2-T3-F2.

Branch managers receive new stock as CSV files and want to see on the stock list
which shelved copies are wanted by members waiting.

## LEND2-T3-F1

A new command `import-copies <branch> <path>` reads a CSV file with a header line and
then lines `copy,book`, and adds every listed copy at the branch, following DEC-011.
It is all or nothing: when any line is wrong (wrong number of fields, a duplicate or
unknown copy or book), nothing is added and it prints `error: line 3: ` followed by
the error text for the first wrong line (lines are numbered from 1, the header being
line 1), for example `error: line 3: unknown book b9`. Blank lines are skipped. On
success it prints `imported 2 copies at east`. An unknown branch prints
`error: unknown branch west`, and a file that cannot be read `error: cannot read <path>`.
`help` lists `import-copies <branch> <path>` directly after `import-members <path>`.

## LEND2-T3-F2

In `export-inventory`, a copy on the shelf whose book has holds has the status
`on shelf (2 holds waiting)` (the number of holds on the book) instead of `on shelf`.
Other statuses are unchanged.

Acceptance criteria: each statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
