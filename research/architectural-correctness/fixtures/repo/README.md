# Lending

A small library lending system: members, books and their copies, loans (borrow and
return), a holds queue per book, and fines for late returns. It is driven
from a text command line.

The lending rules the library has agreed are recorded in `docs/decisions/`
(`DEC-*.md`). They are the source of truth for loan periods, limits, fines,
renewals and holds.

## Build and test

    dotnet build Lending.slnx
    dotnet test Lending.slnx

Tests live in `tests/Lending.Tests`; acceptance tests for new work go in
`tests/Lending.Tests/Acceptance/`.

## Run

    dotnet run --project src/Lending.Host -- <data-directory>

The state is kept in `<data-directory>/library.lending.json`; notices are written
to `<data-directory>/outbox.txt`. Commands (type `help`):

    add-member <member> <standard|student|staff> <name>
    add-book <book> <isbn> <title> <author>
    add-copy <copy> <book>
    borrow <member> <copy>
    return <copy>
    hold <member> <book>
    loans <member>

Words containing spaces are written in double quotes, for example
`add-book b1 9780441013593 Dune "Frank Herbert"`.
