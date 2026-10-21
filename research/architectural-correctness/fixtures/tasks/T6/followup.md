# T6 follow-up: Passing a copy down the queue

Requirements: LEND-T6-F1, LEND-T6-F2.

The Head of Lending has extended DEC-007 (update the record): a copy freed from a
hold goes to the next member in the queue instead of back to the shelf, and a hold on
a book with a copy on the shelf gets that copy set aside straight away.

## LEND-T6-F1

When a hold expires and its book has another hold with no copy set aside, the freed
copy is set aside for the first such hold, until the expiry day (today) plus 7 days.
`expire-holds` (and `startup`) then print, after the expired hold's line,
`, now set aside for m1 until 2026-03-17`, for example

    expired holds: 1
      s1 for b1, copy c1, now set aside for m1 until 2026-03-17

## LEND-T6-F2

A hold placed on a book that has a copy on the shelf (not on loan and not set aside)
sets that copy aside for the new hold at once, until today plus 7 days; when several
copies are on the shelf, the one with the lowest copy id (ordinal) is set aside. Such
a copy expires and passes down the queue like any other. `hold` prints nothing new.

Acceptance criteria: each statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
