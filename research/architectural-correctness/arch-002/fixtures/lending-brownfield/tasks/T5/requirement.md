# T5: Payments against fines

Requirements: LEND2-T5-R1, LEND2-T5-R2, LEND2-T5-R3.

Members pay at the desk (`pay <member> <amount>`), but neither they nor the desk can
see which fines a payment covered. Fines are assessed on return (DEC-003) and payments
follow DEC-010 (`docs/decisions/DEC-010-payments.md`); see also DEC-006. The command
line is `Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests drive it
with an in-memory store and a clock they control (see `tests/Lending.Tests/Support.fs`).
The fields of `Ports` stay as they are.

## LEND2-T5-R1

`account <member>` shows how much of each fine has been paid. Payments are applied to
the member's fines oldest first (in the order the fines were assessed), each fine
taking what it needs before the next one gets anything. Each fine line ends with
`, paid` (paid in full), `, paid 0.50 of 0.75` (paid in part) or `, unpaid`:

    account for m1 (Ada Lovelace):
      fine c1 0.75 assessed 2026-03-26, paid
      fine c3 2.50 assessed 2026-04-02, paid 0.25 of 2.50
      paid 1.00
    owed: 2.25
    loans: 0 of 5

Everything else in the account is unchanged. The existing test `fines and payments show
on the account` in `tests/Lending.Tests/BaseTests.fs` expects the old fine line; update
it to the new format.

## LEND2-T5-R2

`pay` names the fines the payment finished paying, in assessment order:

    m1 paid 1.00, owes 2.25 (settled c1)
    m1 paid 2.25, owes 0.00 (settled c3, c5)

A payment that finishes no fine prints as before (`m1 paid 0.25, owes 2.00`). Refused
payments are unchanged.

## LEND2-T5-R3

Members dislike being chased for small change. After a payment, when the member still
owes something but less than 0.50, the desk writes off the rest: the member then owes
0.00, `pay` adds `, rest written off` (for example
`m1 paid 0.50, owes 0.00 (settled c1, rest written off)`), and `account` shows the
fines that were written off with `, written off` instead of their payment status.

Acceptance criteria: each statement above holds; existing commands keep their output
except where a statement above changes it; all tests pass with `dotnet test Lending.slnx`.
