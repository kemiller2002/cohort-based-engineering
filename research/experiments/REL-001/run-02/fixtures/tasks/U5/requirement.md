# U5: Batch transfers

Requirements: LEDGER-U5-R1, LEDGER-U5-R2. Decision: DEC-U5-BATCH-ATOMICITY.

Payroll submits many transfers at once, and a batch must never be half
applied. Add to `src/Ledger/Domain.fs`:

```fsharp
/// One transfer of a batch.
type TransferInstruction =
    { Source: AccountId
      Destination: AccountId
      Amount: decimal
      Reference: string }
```

and a new case `BatchFailed of index: int * reason: LedgerError` on
`LedgerError`. Implement `Ledger.transferBatch` in `src/Ledger/Ledger.fs`
and `Store.transferBatch` in `src/Ledger/Store.fs`:

```fsharp
// Ledger
val transferBatch : batch: TransferInstruction list -> ledger: LedgerState -> Result<LedgerState, LedgerError>
// Store
val transferBatch : batch: TransferInstruction list -> store: LedgerStore -> Result<unit, LedgerError>
```

## LEDGER-U5-R1

`Ledger.transferBatch batch ledger` applies the instructions in list order,
each one exactly as `Ledger.transfer` would (same rules, same postings), and
each instruction sees the effect of the instructions before it. For example,
money received by an account earlier in the batch can be sent on later in
the same batch.

- If every instruction succeeds, the result is the ledger with all their
  postings, in order.
- If the instruction at zero-based position `i` is refused by the transfer
  rules with error `e`, the whole batch is refused with
  `Error (BatchFailed (i, e))` and none of its postings are recorded.
- An empty batch succeeds and records nothing.

## LEDGER-U5-R2

`Store.transferBatch batch store` is all-or-nothing on the store (decision
DEC-U5-BATCH-ATOMICITY):

- when the batch succeeds, all of its postings are committed, and
  `Store.balance` reports every account's balance including them;
- when it is refused, it returns the same error as `Ledger.transferBatch`,
  and the store's state is exactly what it was before the call: no
  instruction of the batch is committed, `Store.current` lists the same
  postings and `Store.balance` reports the same balances as before.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
