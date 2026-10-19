# T2: Atomic transfer between accounts

Complexity: medium. Requirements: LEDGER-T2-R1, LEDGER-T2-R2, LEDGER-T2-R3.

Implement `Ledger.transfer source destination amount reference ledger`.

## LEDGER-T2-R1

A successful transfer records exactly two postings, both carrying
`reference`: `-amount` on `source` and `+amount` on `destination`. Both
happen or neither does.

## LEDGER-T2-R2

A transfer is refused, and the ledger is returned unchanged, when:
the amount is zero or negative (`InvalidAmount amount`); either account does
not exist (`UnknownAccount id`, checking `source` first); `source` and
`destination` are the same account (`SameAccount source`); or `source` holds
less than `amount` (`InsufficientFunds (source, amount)`). Errors are checked
in that order: amount, source exists, destination exists, same account, funds.

## LEDGER-T2-R3

Transfers conserve money: the sum of all account balances is identical before
and after any transfer, successful or refused.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
