# T3: Exports for the branch managers

Requirements: LEND2-T3-R1, LEND2-T3-R2, LEND2-T3-R3.

Branch managers already get the overdue export (`export-overdue <path>`); they now want
a stock list per branch, the holds queues, and the member list in the format
`import-members` reads, so that they can move members between systems. Branches follow
DEC-011 and holds DEC-005. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests drive it with an
in-memory store and a clock they control (see `tests/Lending.Tests/Support.fs`), and
read the exported files from disk. The fields of `Ports` stay as they are.

All exports write a CSV file at the given path, replacing any file there: a header line,
then one line per row, fields separated by commas, no quoting. They change nothing in
the library.

## LEND2-T3-R1

A new command `export-inventory <branch> <path>` writes the copies shelved at the
branch, in copy id order:

    copy,book,title,status
    c1,b1,Dune,on loan until 2026-03-23
    c2,b1,Dune,on shelf

and prints `exported 2 copies at main to <path>`. A branch with no copies writes only
the header (`exported 0 copies at east to <path>`); an unknown branch prints
`error: unknown branch west` and writes nothing.

## LEND2-T3-R2

A new command `export-holds <path>` writes every hold, books in book id order and each
book's queue in order:

    book,position,member,since
    b1,1,s1,2026-03-02
    b1,2,m1,2026-03-04

and prints `exported 2 holds to <path>`.

## LEND2-T3-R3

A new command `export-members <path>` writes every member, in member id order, in the
format `import-members` reads (`member,type,name`):

    member,type,name
    m1,standard,Ada Lovelace

and prints `exported 1 members to <path>`. A file it writes, read back with
`import-members` into a library without those members, adds the same members.

For all three: with the wrong number of words they print `usage: export-inventory
<branch> <path>`, `usage: export-holds <path>` and `usage: export-members <path>`, and
`help` lists those three lines, in that order, directly after `export-overdue <path>`.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
