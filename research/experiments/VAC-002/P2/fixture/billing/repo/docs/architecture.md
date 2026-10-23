# Billing architecture

Four modules, compiled in this order; each may use only the ones before it.

| Module | Holds |
|---|---|
| `Domain` | Types only: customers, invoices, state, errors |
| `Rules` | Every business rule, as a pure function, each naming the decision record it implements |
| `Commands` | Pure state transitions: state in, next state and output out. No business rules of their own |
| `Cli` | Parsing a command line, running a command against the session, printing. The only mutable state is the session's state reference |

A business rule is written once, in `Rules`. Output formats live in `Commands` and `Cli`.
