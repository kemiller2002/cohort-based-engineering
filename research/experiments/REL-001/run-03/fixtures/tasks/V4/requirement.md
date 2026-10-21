# V4: Fee preview, then a new fee rule

Requirements: LEDGER-V4-R1, LEDGER-V4-R2. Do R1 first, then R2.

## LEDGER-V4-R1

Customers want to see the fee the next period close will charge them.

- Move the fee rule that `closePeriod` uses today (a balance of at least
  1.00 pays 1.00, anything less pays nothing) into one public function in
  `src/Ledger/Ledger.fs`:

  ```fsharp
  val periodFee : balance: decimal -> decimal
  ```

  `closePeriod` must charge exactly `periodFee` of each account's balance.
- Add

  ```fsharp
  val feeFor : id: AccountId -> ledger: LedgerState -> Result<decimal, LedgerError>
  ```

  the fee the next `closePeriod` would charge the account given its current
  balance, built on `periodFee`; `Error (UnknownAccount id)` for an account
  that is not open.

## LEDGER-V4-R2

The fee rule changes. Premium balances pay nothing:

| Balance | Fee |
|---|---|
| below 1.00 | 0 |
| at least 1.00 and below 1,000.00 | 1.00 |
| 1,000.00 or more | 0 |

- `periodFee` implements the new table, and everything built on it follows:
  `feeFor` and `closePeriod` always agree with `periodFee`.
- `closePeriod` records a fee posting (reference `fee:<periodId>`) only when
  the fee is more than 0; the summary's `Fees` lists every account, with 0
  for an account that paid nothing. Its idempotence is unchanged.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
