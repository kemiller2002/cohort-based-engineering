# T2 follow-up: An append-only log store

Requirements: LEND-T2-F1.

The library wants an audit trail of every saved state. Add a second persistence
provider next to the JSON file store. This is a storage change only: the lending
rules, use cases and views (`src/Lending.Semantic`, `src/Lending.Transition`,
`src/Lending.Application`) must not change.

## LEND-T2-F1

`Lending.Host.Persistence.LogFileStore.create : string -> Store` keeps the library in
an append-only log file. Each `Save` appends exactly one line to the file: the whole
library (history included) in the same JSON representation the JSON file store uses,
written on a single line. Earlier lines are never changed. `Load` returns the library
of the last line; when the file does not exist or has no lines, `Load` returns an
empty library. A library saved through the log store and loaded again, by the same or
another `LogFileStore.create` for the same path, is equal to the one saved.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
