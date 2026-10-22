# Lending

A library lending system: members, books and their copies at one or more branches,
loans (borrow, return, renew), a holds queue per book, fines for late returns,
payments, overdue reports and reminders, member imports and backups. It is driven from
a text command line.

The lending rules the library has agreed are recorded in `docs/decisions/`
(`DEC-*.md`). They are the source of truth for loan periods, limits, fines,
renewals, holds, reminders, borrowing blocks, payments and branches.

## Build and test

    dotnet build Lending.slnx
    dotnet test Lending.slnx

Tests live in `tests/Lending.Tests`; acceptance tests for new work go in
`tests/Lending.Tests/Acceptance/`. The tests build the `Ports` record themselves
(`tests/Lending.Tests/Support.fs`) with an in-memory store and a clock they control.

## Run

    dotnet run --project src/Lending.Host -- <data-directory>

The state is kept in `<data-directory>/library.lending.json` (format `lending/2`);
notices are written to `<data-directory>/outbox.txt`. Commands (type `help`):

    add-member <member> <standard|student|staff> <name>
    add-book <book> <isbn> <title> <author>
    add-branch <branch> <name>
    add-copy <copy> <book> [<branch>]
    transfer <copy> <branch>
    shelf <branch>
    borrow <member> <copy>
    return <copy>
    renew <copy>
    hold <member> <book>
    cancel-hold <member> <book>
    holds <book>
    loans <member>
    account <member>
    pay <member> <amount>
    overdue
    export-overdue <path>
    remind
    reconcile <copy> <arrived|missing>
    members
    import-members <path>
    backup <path>

Words containing spaces are written in double quotes, for example
`add-book b1 9780441013593 Dune "Frank Herbert"`. Copies added without a branch are
shelved at the main branch (`main`, "Main Library"). Amounts have at most two decimals.
