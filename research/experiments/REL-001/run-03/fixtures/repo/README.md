# Ledger

A small ledger: accounts, dated postings, balances, transfers, period close
and an in-memory store.

- `src/Ledger/Domain.fs`: domain types.
- `src/Ledger/Ledger.fs`: pure operations on `LedgerState`.
- `src/Ledger/Store.fs`: the stateful store that commits successful operations.
- `tests/Ledger.Tests`: xunit tests; acceptance tests live in `Acceptance/`.
- `docs/design/`: design notes.

    dotnet test Ledger.slnx
