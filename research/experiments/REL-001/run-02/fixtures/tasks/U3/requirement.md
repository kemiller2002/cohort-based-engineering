# U3: Shared fee split across accounts

Requirements: LEDGER-U3-R1, LEDGER-U3-R2. Decision: DEC-U3-ROUNDING.

A fee shared by several accounts (for example a joint custody fee) is split
between them and charged to each. Implement in `src/Ledger/Ledger.fs`:

```fsharp
val chargeSharedFee : total: decimal -> accounts: AccountId list -> reference: string -> ledger: LedgerState -> Result<LedgerState, LedgerError>
```

Callers always pass a non-empty list of distinct accounts and a `total`
with at most two decimal places.

## LEDGER-U3-R1

`Ledger.chargeSharedFee total accounts reference ledger` refuses, and
records no posting at all, when (checked in this order):

1. `total` is zero or negative: `Error (InvalidAmount total)`;
2. an account in the list does not exist: `Error (UnknownAccount id)` for
   the first unknown account in list order;
3. an account's balance is less than its share (LEDGER-U3-R2):
   `Error (InsufficientFunds (id, share))` for the first such account in
   list order.

Every account's existence is checked, in list order, before any account's
funds: an unknown account anywhere in the list is reported even when an
earlier account is short of funds.

Otherwise it records, in list order, one posting of `-share` per account,
with `reference`, dated with the ledger's business date. A share of 0.00
is not posted.

## LEDGER-U3-R2

The shares are computed as follows (decision DEC-U3-ROUNDING):

- The base share is `total / n` (n = number of accounts) rounded to 2
  decimal places with banker's rounding (round half to even), so 0.125
  rounds to 0.12 and 0.135 rounds to 0.14.
- Every account's share is the base share, except the first account in the
  list, which also takes the remainder `total - n * baseShare` (the
  remainder may be negative).
- The shares therefore always sum to exactly `total`.

Inputs for which the first account's share would be negative are outside
this requirement.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
