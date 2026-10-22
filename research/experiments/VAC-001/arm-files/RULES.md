# Architectural rules (VAC-RULES 1.0.0)

These rules apply the Echelon four-tier architecture (SDE-DOCTRINE-003 v0.2.1, `ordo/doctrine/FOUR-TIER-ARCHITECTURE.md`)
to this repository. `archcheck` checks every rule mechanically. The same rules are used to evaluate your work.

| Tier | Question | Files |
|---|---|---|
| 1 Semantic Model | What can be true? | `src/Ledger/Domain.fs` |
| 2 Transition / Domain Execution | What legal change may happen? | `src/Ledger/Ledger.fs` and every other pure module in `src/Ledger` except `Store.fs` (for example `StandingOrders.fs`, `Reconciliation.fs`) |
| 3/4 Orchestration and Host | Coordinates changes over time; owns mutable state | `src/Ledger/Store.fs` |

Dependencies point downward only: Store → Tier 2 → Tier 1.

## Rules

- **AR-1 Compile order follows the tiers.** In `src/Ledger/Ledger.fsproj`, `Domain.fs` comes first and `Store.fs`
  comes last.
- **AR-2 Tiers 1 and 2 perform no effects.** `Domain.fs` and the Tier 2 modules must not use I/O, the console,
  the system clock, randomness, threads, tasks, async, or mutable state. That excludes `System.IO`, `Console`,
  `printf`, `printfn`, `eprintf`, `DateTime.Now`, `DateTime.UtcNow`, `DateTime.Today`, `DateOnly.FromDateTime`,
  `Stopwatch`, `Random`, `Guid.NewGuid`, `Environment`, `Thread`, `Task`, `async`, `mutable`, `ref` cells and `<-`.
  The business date comes from `LedgerState.Today`.
- **AR-3 Refusals are data.** Tiers 1 and 2 report refusals as `Error` values of `LedgerError`. They do not throw:
  no `failwith`, `failwithf`, `raise`, `invalidArg`, `invalidOp` or `exn`.
- **AR-4 Balances are derived.** A balance is always derivable from the postings. `LedgerState` holds no stored
  balance: no field whose name contains `Balance`.
- **AR-5 No upward references.** `Domain.fs` does not refer to the `Ledger` operations module or to `Store`.
  Tier 2 modules do not refer to `Store`.
- **AR-6 Toolchain pins are fixed.** `global.json`, the `TargetFramework` in `Directory.Build.props` and every
  package version stay exactly as they were in the starting state.
