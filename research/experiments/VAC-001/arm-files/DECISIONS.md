# Decision records

Accepted decisions for this repository. A decision is changed only by a new record that names the decision it
supersedes and the evidence that justifies the change. Add your decisions at the end, in the same format.

| Field | Meaning |
|---|---|
| ID | stable identifier |
| Status | `accepted`, `superseded by <ID>` or `rejected` |
| Requirement | the requirement IDs it serves, or `base` |
| Decision | what was decided |
| Evidence | files, requirements or records that support it |
| Provenance | who recorded it, and when (unit number) |

## DEC-BASE-DERIVED-BALANCES

- Status: accepted
- Requirement: base
- Decision: balances are derived from the postings; `LedgerState` stores no balances.
- Evidence: `src/Ledger/Domain.fs` (`LedgerState` comment); `docs/architecture/RULES.md` AR-4
- Provenance: starting state

## DEC-BASE-NEWEST-FIRST

- Status: accepted
- Requirement: base
- Decision: `LedgerState.Postings` is stored newest first; `Ledger.postings` returns journal (oldest-first) order.
- Evidence: `src/Ledger/Domain.fs` (`LedgerState` comment); `src/Ledger/Ledger.fs#postings`
- Provenance: starting state

## DEC-BASE-REFUSALS-AS-DATA

- Status: accepted
- Requirement: base
- Decision: refused operations return `Error` of `LedgerError` and change nothing; they never throw.
- Evidence: `src/Ledger/Ledger.fs`; `docs/architecture/RULES.md` AR-3
- Provenance: starting state

## DEC-BASE-STORE-CACHE

- Status: accepted
- Requirement: base
- Decision: `Store` keeps a balance cache in step with the journal on every operation it commits.
- Evidence: `src/Ledger/Store.fs` (module comment)
- Provenance: starting state

## DEC-V5-PAID-IN-FULL

- Status: accepted
- Requirement: LEDGER-V5 (standing orders)
- Decision: a standing order is paid in full or not at all; partial payment was considered and rejected.
- Evidence: `docs/design/standing-orders.md`
- Provenance: starting state (Payments design note)
