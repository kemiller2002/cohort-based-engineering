# T3 follow-up: Branch shelf capacity

Requirements: LEND-T3-F1, LEND-T3-F2.

The library now has two branches, `main` and `east`, and every copy is shelved at one
of them. The Head of Lending has accepted a new decision; add it as
`docs/decisions/DEC-009-shelf-capacity.md`:

> **DEC-009: Shelf capacity.** Each branch has room for a fixed number of copies:
> main 8, east 4. A copy is never added to a branch that is full.

## LEND-T3-F1

Every copy belongs to a branch. `add-copy <copy> <book>` shelves the copy at `main`.
The JSON file store keeps each copy's branch, and a copy stored before this change
(without a branch) is at `main`. `add-copy` to a full `main` is refused with
`error: branch main is full (8 copies)`. (The existing test in
`tests/Lending.Tests/BaseTests.fs` that builds a `Copy` record needs the new field.)

## LEND-T3-F2

`import` also accepts the header `book,isbn,title,author,copies,branch`, whose rows
have a sixth field naming the branch (`main` or `east`) for all the row's copies; with
the old five-field header all copies go to `main`. With the new header a row needs 6
fields (`expected 6 fields`), and an unknown branch skips the row with
`unknown branch <name>`. A row whose copies would take its branch over DEC-009's
capacity (counting the copies already shelved there and those added by earlier rows)
is skipped, all or nothing as before, with `branch east has room for 1 more copies`
(the room left before the row). Error messages for a wrong header name both headers:
`error: the first line must be book,isbn,title,author,copies or book,isbn,title,author,copies,branch`.

Acceptance criteria: each statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
