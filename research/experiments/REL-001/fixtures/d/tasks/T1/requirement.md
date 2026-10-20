# T1: Reject non-positive posting amounts

Complexity: low. Requirement: LEDGER-T1-R1.

## LEDGER-T1-R1

`Ledger.credit` and `Ledger.debit` must refuse any amount that is zero or
negative with `Error (InvalidAmount amount)`, where `amount` is the value
supplied, and must not record any posting when they refuse.

Acceptance criteria:

1. `credit` with 0 or a negative amount returns `Error (InvalidAmount amount)`.
2. `debit` with 0 or a negative amount returns `Error (InvalidAmount amount)`;
   this check applies before the funds check.
3. A refused call leaves the ledger unchanged (no posting is recorded).
4. Positive amounts behave exactly as before (credit adds, debit removes,
   overdrafts refused with `InsufficientFunds`, unknown accounts with
   `UnknownAccount`).
5. Existing public signatures in `src/Ledger` are kept; all tests pass with
   `dotnet test Ledger.slnx`.
