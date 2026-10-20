# V5: Standing orders

Requirements: LEDGER-V5-R1, LEDGER-V5-R2, LEDGER-V5-R3.

Customers set up recurring payments on a fixed day of the month. The
background is in `docs/design/standing-orders.md`. Add to
`src/Ledger/Domain.fs`:

```fsharp
type StandingOrder =
    { OrderId: string
      Payer: AccountId
      Payee: AccountId
      Value: decimal
      DayOfMonth: int }

type OrderOutcome =
    | Paid of orderId: string
    | Skipped of orderId: string * reason: LedgerError
    | AlreadyPaid of orderId: string
```

and the error case `| InvalidOrder of string` to `LedgerError`. Implement a
new module `Ledger.StandingOrders` in `src/Ledger/StandingOrders.fs` (add it
to `Ledger.fsproj` after `Ledger.fs`):

```fsharp
val run : date: DateOnly -> orders: StandingOrder list -> ledger: LedgerState -> Result<OrderOutcome list * LedgerState, LedgerError>
```

`orders` is the full list of the ledger's standing orders, due or not.

## LEDGER-V5-R1

Before anything else, `run` checks every order in `orders`, due or not, in
list order. The first order that has a `Value` of zero or less, a
`DayOfMonth` outside 1 to 31, or an `OrderId` that an earlier order in the list
already used, refuses the whole run with `Error (InvalidOrder id)`, naming
that order's id. Only then is the date checked: a `date` before the ledger's
business date is refused with `Error (DateInPast date)`. A refused run
changes nothing. Otherwise the business date moves to `date` (as
`Ledger.setDate` does), even when no order is due.

## LEDGER-V5-R2

An order is due on `date` when its `DayOfMonth` equals the day of `date`, or
when its `DayOfMonth` is larger than the number of days in `date`'s month and
`date` is the last day of that month (a 31st-of-the-month order is due on
30 April and on 28 February, or 29 February in a leap year).

Due orders are paid one after another in ascending order of `OrderId`, compared
ordinally, whatever their order in the list; each payment sees the effect of
the ones before it. A payment is `Ledger.transfer Payer Payee Value reference`
with reference `standing:<OrderId>:<date as yyyy-MM-dd>`, for example
`standing:rent:2026-04-30`. Whether an order the source cannot fully cover is
paid in part or not at all is decided in `docs/design/standing-orders.md`;
follow it. An order whose transfer is refused is reported as
`Skipped (id, error)` with the transfer's error, and the run carries on with
the next order.

The result lists one outcome per due order, in the order they were
processed: `Paid id` for an order that was paid. Orders that are not due
have no outcome.

## LEDGER-V5-R3

Running again for the same date never pays an order twice. A due order
whose reference for that date is already in the journal is reported as
`AlreadyPaid id` and records nothing. An order that was skipped earlier has
no such posting, so a later run for the same date pays it if the funds are
now there.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
