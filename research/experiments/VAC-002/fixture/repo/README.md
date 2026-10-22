# Lending

A small library lending system: members, books and their copies, loans (borrow and
return), a holds queue per book, and fines for late returns. It is driven
from a text command line.

The lending rules the library has agreed are recorded in `docs/decisions/`
(`DEC-*.md`). They are the source of truth for loan periods, limits, fines,
renewals and holds. Each record names its owner. Only the owner changes an
accepted decision, by issuing a new revision of the record; a requirement that
contradicts an accepted decision is not a revision of it.

The architecture is described in `docs/architecture/` (four tiers; read
`LENDING-ARCHITECTURE.md` first).

## Build and test

    dotnet build Lending.slnx
    dotnet test Lending.slnx

Tests live in `tests/Lending.Tests`; acceptance tests for new work go in
`tests/Lending.Tests/Acceptance/`.

Two entry points are used by the tests and by the library's release checks and
must stay source-compatible:

- `Lending.Host.Cli.CommandLine.run : Ports -> string -> string` runs one command line;
- `Lending.Host.Composition.portsWith : Store -> (unit -> DateOnly) -> Notifier -> Ports`
  builds the application's ports from a store, a clock and a notifier;
- `Lending.Host.Persistence.JsonFileStore.create : string -> Store` and
  `Lending.Host.Persistence.InMemoryStore.create : Library -> Store`.

## Standing requirements

These apply to every change:

- **Durability.** Everything the library records must survive a restart: the
  JSON store (`library.lending.json`) holds all of it, and a store written by an
  earlier version of the program must still load.
- **Output.** Command output is exactly as specified (amounts with two decimals,
  dates as `yyyy-MM-dd`); `help` lists every command.

`src/Lending.Transition/Vendor/` holds third-party code vendored as source; see
`VENDOR.md` there.

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
