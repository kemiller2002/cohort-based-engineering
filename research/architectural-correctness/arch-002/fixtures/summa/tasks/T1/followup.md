# T1 follow-up: Statement aging and a CSV statement

Requirements: SUMMA-T1-F1, SUMMA-T1-F2.

Customers' accounts payable teams asked for two things on the statement introduced by
SUMMA-T1: how old the balance is, and a spreadsheet form.

## SUMMA-T1-F1

`Statement` gains `Aging: Aging`, with

    type Aging = { Current: Money; Days1To30: Money; Days31To60: Money; Days61To90: Money; Over90: Money }

the closing balance split by how far past due each invoice's part of it is on `until`
(`Payments.bucket until dueDate`, so `Current` is not yet due). An invoice's part is the
sum of its own statement lines dated up to `until`, including those before `from`. The
five amounts add up to `Closing`.

The document becomes `summa.customer-statement` version 2: version 1 plus an `aging`
member after `closing`:

    "aging":{"current":{...},"days1to30":{...},"days31to60":{...},"days61to90":{...},"over90":{...}}

with each amount written as money is everywhere else in the document.

## SUMMA-T1-F2

On a customer's page, the engine message `StatementCsvRequested of range: string` (kernel
event `statementCsvExported`, value the range) offers the same statement as one CSV
download and no other effect: `statement-<customer id>-<from>-<until>.csv`, media type
`text/csv`. The file starts with the header lines every CSV export has
(`Exports.withHeader`): kind `customer-statement`, the period `from`..`until`, generated
now, the books' data version and the filters `currency=USD` and `customer=<customer id>`.
Then come the column line `date,kind,invoice,reference,amount,balance`, a row
`<from>,opening,,,,<opening>`, one row per statement line and a row
`<until>,closing,,,,<closing>`. Dates are `yyyy-MM-dd`; the kind is written as in the
document; the reference is a CSV field as the other exports write one
(`Reports.csvField`); amounts are plain decimals with two places and a leading `-` when
negative (`6050.00`, `-2000.00`). The errors are those of SUMMA-T1-R3. `app/index.html`
offers it beside the JSON statement.

Acceptance criteria: each statement above holds; SUMMA-T1 holds except where this
follow-up changes it; all tests pass with `dotnet test Summa.sln`.
