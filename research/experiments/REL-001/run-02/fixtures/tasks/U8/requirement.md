# U8: Account statement for a date range

Requirement: LEDGER-U8-R1.

Customers ask for a statement of one account between two dates. Add to
`src/Ledger/Domain.fs`:

```fsharp
/// One line of an account statement.
type StatementLine =
    { Date: DateOnly
      Reference: string
      Amount: decimal
      /// The account's balance immediately after this posting.
      Balance: decimal }
```

and a new case `InvalidDateRange of DateOnly * DateOnly` on `LedgerError`.
Implement in `src/Ledger/Ledger.fs`:

```fsharp
val statement : id: AccountId -> fromDate: DateOnly -> toDate: DateOnly -> ledger: LedgerState -> Result<StatementLine list, LedgerError>
```

## LEDGER-U8-R1

`Ledger.statement id fromDate toDate ledger` returns one line per posting of
account `id` whose `Date` lies in the range from `fromDate` to `toDate`,
**both ends inclusive**. Postings of other accounts never appear.

- Lines are ordered oldest first: by date, and postings with the same date
  in the order they were recorded.
- Each line carries the posting's `Date`, `Reference` and `Amount`, and
  `Balance`: the account's balance immediately after that posting, counting
  every earlier posting of the account, including postings dated before
  `fromDate`.
- A range with no postings gives an empty list.
- `fromDate` later than `toDate` is refused with
  `Error (InvalidDateRange (fromDate, toDate))`.
- An unknown account is refused with `Error (UnknownAccount id)`. When both
  apply, the date range is checked first.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
