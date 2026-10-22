# T6 follow-up: Searching one branch

Requirements: LEND2-T6-F1, LEND2-T6-F2.

Members want to know what they can pick up at their own branch, and staff search by
ISBN when a member brings a reading list.

## LEND2-T6-F1

`search <text> <branch>` searches as `search <text>` does but counts only the copies
shelved at the branch, and lists only books with at least one copy there:

    1 books match "dune" at east:
      b1 "Dune" by Frank Herbert: 1 of 1 copies on shelf at east

When no book matches it prints `no books match "dune" at west`; an unknown branch
prints `error: unknown branch west`. `help` shows the command as
`search <text> [<branch>]` (in the same place), and a `search` with the wrong number of
words prints `usage: search <text> [<branch>]`.

## LEND2-T6-F2

`search`, with or without a branch, also matches a book whose ISBN is exactly the text.

Acceptance criteria: each statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
