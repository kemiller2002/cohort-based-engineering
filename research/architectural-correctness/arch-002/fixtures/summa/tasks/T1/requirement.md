# T1: Customer statements

Requirements: SUMMA-T1-R1, SUMMA-T1-R2, SUMMA-T1-R3.

Customers ask for a statement of account: what they owed when a period began, every
invoice and settlement in it, and what they owe at its end. Settlement is what
`Payments.settlement` already lists for an invoice (DF-SUMMA-2026-0028). A statement
file is a financial export (DF-SUMMA-2026-0041).

## SUMMA-T1-R1

A new module `Summa.Ledger.Statements` computes a customer's statement:

    Statements.statement : customerId: string -> currency: string -> from: DateOnly -> until: DateOnly
                           -> Receivables -> Result<Statement, string>

    type LineKind = Invoiced | Paid | PaymentReturned | Credited | WrittenOff | Voided
    type Line = { Date: DateOnly; Kind: LineKind; Invoice: string; Reference: string; Amount: Money; Balance: Money }
    type Statement = { CustomerId: string; Currency: string; From: DateOnly; Until: DateOnly
                       Opening: Money; Lines: Line list; Closing: Money }

Only the customer's invoices in `currency` count. Each gives one `Invoiced` line on its
issue date (amount: its total; reference: empty) and one line per entry of its
settlement: a payment applied is `Paid` (reference: the payment's reference), a payment
reversed is `PaymentReturned`, a credit applied is `Credited` (reference: empty), a
write-off is `WrittenOff` and a void is `Voided` (each with its reason as reference).
The amount is the entry's effect, so a reduction is negative. A settlement entry dated
before its invoice was issued counts on the issue date. `Invoice` is the invoice number.

`Opening` is the sum of the amounts of the lines dated before `from`. `Lines` are the
lines dated `from` to `until`, both included, ordered by date, then each invoice's
`Invoiced` line before any settlement line, then by invoice number; the settlement lines
of one invoice keep their settlement order. Each line's `Balance` is the running total
from `Opening`, and `Closing` is `Opening` plus every line (`Opening` when there are
none). An unknown customer is `Error "unknown customer CUST-9"`; a period that ends
before it starts is `Error "the statement period ends before it starts"`.

## SUMMA-T1-R2

A statement is offered as a versioned machine-readable document,
`summa.customer-statement` version 1, written the way the invoice's machine-readable
document is (`Documents.toJson`): a fixed member order and no whitespace, so the same
statement is always the same bytes. Money is written as the invoice document writes it.
For example (wrapped here):

    {"schema":"summa.customer-statement","version":1,"classification":"confidential financial data",
     "customer":{"id":"CUST-0001","name":"ABC Corp"},"currency":"USD","from":"2026-10-01","until":"2026-10-31",
     "opening":{"currency":"USD","minor":0},
     "lines":[{"date":"2026-10-07","kind":"invoiced","invoice":"EF-2026-0001","reference":"",
               "amount":{"currency":"USD","minor":605000},"balance":{"currency":"USD","minor":605000}}],
     "closing":{"currency":"USD","minor":605000}}

The kinds are written `invoiced`, `paid`, `payment-returned`, `credited`, `written-off`
and `voided`; dates as `yyyy-MM-dd`.

## SUMMA-T1-R3

On a customer's page (`Routes.Customer(id, _)`), the engine message
`StatementExportRequested of range: string`, where the range is one of the report ranges
of `Accounting.dateRange` relative to the organization's business today, offers the
customer's USD statement for that period as one download and no other effect:
`statement-<customer id>-<from>-<until>.json`, media type `application/json`, holding
the R2 document. An unknown range offers nothing and sets the error
`Unknown statement period.`; without the files pack the error is the existing
`This browser cannot offer downloads here.`. On books on GitHub it needs the same
capability as the other financial exports. The page sends it as the kernel event
`statementExportRequested`, whose value is the range, from a "Download statement" control
on the customer page of `app/index.html`.

Acceptance criteria: each statement above holds; existing behaviour is unchanged; all
tests pass with `dotnet test Summa.sln`.
