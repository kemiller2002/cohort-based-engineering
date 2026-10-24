# T3 follow-up: Due on a day of the next month

Requirements: SUMMA-T3-F1, SUMMA-T3-F2.

Other customers pay on a fixed day of the following month ("due the 15th of next
month"). Add these terms the way SUMMA-T3 added end-of-month terms.

## SUMMA-T3-F1

`Invoicing.PaymentTerms` gains `DayOfNextMonth of day: int`, for a day from 1 to 28. An
invoice on these terms is due on that day of the month after the month it is issued in:
issued 2026-10-07 on the 15th of next month, it is due 2026-11-15; issued 2026-12-20 on
the 10th, 2027-01-10. In words they are `Due the 15th of next month` (with the English
ordinal: 1st, 2nd, 3rd, 4th, ... 21st, 22nd, 23rd, 24th, ... 28th), on invoices, on the
customer pages and in the audit trail. They are stored as
`{"kind":"day-of-next-month","day":15}` in every record that holds terms and read back.

## SUMMA-T3-F2

The customer form's terms field also accepts `day` followed by a day from 1 to 28 (`day
15`, `Day 1`, `day15`) as these terms. The error for anything else becomes
`Terms are a number of days between 0 and 365, optionally followed by EOM, a day of next month such as day 15 (1 to 28), or empty for the organization's default.`

Acceptance criteria: each statement above holds; SUMMA-T3 holds except where this
follow-up changes it; all tests pass with `dotnet test Summa.sln`.
