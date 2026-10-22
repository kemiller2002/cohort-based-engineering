# T4: Restoring backups

Requirements: LEND2-T4-R1, LEND2-T4-R2, LEND2-T4-R3.

The desk can write a backup (`backup <path>`) but cannot use one: there is no way to
restore it or to see what it holds, and a backup silently overwrites an older one. The
command line is `Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests
drive it with an in-memory store and a clock they control (see
`tests/Lending.Tests/Support.fs`), and keep backups on disk. The fields of `Ports`
stay as they are.

Below, a *summary* of a library is `3 members, 2 books, 3 copies, 1 loans` (the
number of members, books, copies and active loans).

## LEND2-T4-R1

A new command `restore <path>` replaces the whole state of the library with the backup
at the path (everything a backup holds: members, books, branches, copies, loans, holds,
fines, payments and reminders) and prints `restored <summary> from <path>`, for example
`restored 3 members, 2 books, 3 copies, 1 loans from /tmp/b.json`. When there is no
backup at the path it prints `error: no backup at <path>` and changes nothing.

## LEND2-T4-R2

A new command `backup-info <path>` describes a backup without restoring it:

    backup /tmp/b.json: 3 members, 2 books, 3 copies, 1 loans, 2 holds, 0.75 owed

with the summary, the number of holds, and the total all members owe in it (fines less
payments, two decimals). When there is no backup at the path it prints
`error: no backup at <path>`.

## LEND2-T4-R3

`backup <path>` no longer overwrites: when a file already exists at the path it prints
`error: <path> already exists` and leaves the file as it was. A backup it writes prints
`backed up <summary> to <path>`. The existing test `a backup holds the whole library`
in `tests/Lending.Tests/BaseTests.fs` expects the old output; update it.

For all three: with the wrong number of words they print `usage: restore <path>`,
`usage: backup-info <path>` and `usage: backup <path>`, and `help` lists
`restore <path>` and `backup-info <path>`, in that order, directly after
`backup <path>`.

Acceptance criteria: each statement above holds; existing commands keep their output
except where a statement above changes it; all tests pass with `dotnet test Lending.slnx`.
