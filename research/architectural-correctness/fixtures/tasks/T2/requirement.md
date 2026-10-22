# T2: Loan history

Requirements: LEND-T2-R1, LEND-T2-R2, LEND-T2-R3.

Members want to see what they have borrowed before, and the desk wants to see how
often a member returns late. Today a return forgets the loan. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; the JSON file store is
`Lending.Host.Persistence.JsonFileStore.create : string -> Store`.

## LEND-T2-R1

Every successful `return` records the finished loan in the library's history: the
copy, the member, the day it was borrowed, its due date at the time of the return,
the day it was returned (today), and how many days late it came back (0 when on time).
A refused return records nothing.

## LEND-T2-R2

A new command `history <member>` lists the member's finished loans in the order they
were returned, oldest first:

    history for m1 (Ada Lovelace):
      c1 "Dune" borrowed 2026-03-02, due 2026-03-23, returned 2026-03-26, 3 days late
      c3 "Emma" borrowed 2026-03-24, due 2026-04-14, returned 2026-04-10, on time

A loan returned on or before its due date shows `on time`; one returned 1 day late
shows `1 days late`. A member with no finished loans gets
`no history for m1 (Ada Lovelace)`; an unknown member gets
`error: unknown member m9`. `history` with the wrong number of words prints
`usage: history <member>`, and `help` lists `history <member>` on its own line
directly after `loans <member>`.

## LEND-T2-R3

The JSON file store keeps the history: a library saved by one
`JsonFileStore.create path` and loaded by another for the same path has the same
history. A file written before this change (it has no history) still loads, with an
empty history.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
