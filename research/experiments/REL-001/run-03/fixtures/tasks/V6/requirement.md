# V6: Bank reconciliation

Requirements: LEDGER-V6-R1, LEDGER-V6-R2, LEDGER-V6-R3.

Finance matches an account's postings against the lines of the bank's
statement. Add to `src/Ledger/Domain.fs`:

```fsharp
type BankLine =
    { BookedOn: DateOnly
      Value: decimal
      Memo: string }

type ReconciliationReport =
    { Matched: (Posting * BankLine) list
      LedgerOnly: Posting list
      BankOnly: BankLine list }
```

and implement a new module `Ledger.Reconciliation` in
`src/Ledger/Reconciliation.fs` (add it to `Ledger.fsproj` after
`Ledger.fs`):

```fsharp
val reconcile : id: AccountId -> lines: BankLine list -> ledger: LedgerState -> Result<ReconciliationReport, LedgerError>
```

A line's `Value` uses the ledger's sign convention (money into the account
is positive, money out is negative) and its `Memo` carries the reference the
ledger recorded.

## LEDGER-V6-R1

`reconcile` refuses an account that is not open with
`Error (UnknownAccount id)`. It considers only the postings of account `id`,
in journal order (oldest first), and it only reads the ledger.

## LEDGER-V6-R2

A bank line and a posting can match when the line's `Value` equals the
posting's `Amount`, the line's `Memo` equals the posting's `Reference`
(exactly, case-sensitive), and `BookedOn` and the posting's `Date` are at
most 2 days apart, in either direction (2 days apart still matches).

Lines are matched one at a time, in the order given. Each line takes, among
the postings that can match it and are not matched yet, the one whose date
is closest to the line's `BookedOn`; when two are equally close, the one earlier
in journal order. A posting is matched at most once; a line with no
candidate is left unmatched.

## LEDGER-V6-R3

The result is `Ok` with:

- `Matched`: each matched line with its posting, as `(posting, line)`, in
  the order of the lines;
- `LedgerOnly`: the account's postings that were not matched, in journal
  order;
- `BankOnly`: the lines that were not matched, in the order given.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
