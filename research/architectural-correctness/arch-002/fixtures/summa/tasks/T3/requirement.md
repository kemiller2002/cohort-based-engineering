# T3: End-of-month payment terms

Requirements: SUMMA-T3-R1, SUMMA-T3-R2, SUMMA-T3-R3.

Several customers pay on "Net 30 EOM" terms: thirty days after the end of the month the
invoice is dated in. Summa only knows due on receipt, Net N and a fixed date, so these
invoices are entered with a hand-computed due date. Summa should know the terms itself.

## SUMMA-T3-R1

`Invoicing.PaymentTerms` gains `NetEndOfMonth of days: int`. An invoice on these terms is
due `days` days after the last day of the month it is issued in: issued 2026-10-07 on
Net 30 EOM, it is due 2026-11-30; issued 2026-02-10 on Net 15 EOM, 2026-03-15. The terms
are written `Net 30 EOM` wherever terms are shown in words (`Documents.termsText`, used on
the invoice and the customer pages) and in the audit trail's description of a change.

## SUMMA-T3-R2

Every stored record that holds terms (customers, drafts, invoices, engagements, recurring
templates) stores them as `{"kind":"net-eom","days":30}` and reads them back. Records
whose terms are of the existing kinds keep their stored bytes.

## SUMMA-T3-R3

The customer form's terms field (`CustomerTermsChanged`) also accepts a number of days
followed by `EOM`, in any case and with or without a space (`30 EOM`, `30eom`), for 1 to
365 days; a new customer added with it has `Net 30 EOM` as their default terms, the
customer page shows them as `Net 30 EOM`, and an invoice issued to that customer is due
on the end-of-month date. Anything else that is not a valid value is refused with the
error `Terms are a number of days between 0 and 365, optionally followed by EOM, or empty for the organization's default.`

Acceptance criteria: each statement above holds; existing behaviour is unchanged; all
tests pass with `dotnet test Summa.sln`.
