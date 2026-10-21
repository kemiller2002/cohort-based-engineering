# T4: Overdue notices

Requirements: LEND-T4-R1, LEND-T4-R2, LEND-T4-R3, LEND-T4-R4.

Implement DEC-008 (`docs/decisions/DEC-008-overdue-notices.md`). Notices are delivered
through the existing `Notifier` port (`Ports.Notifier.Send : Notice -> Async<DeliveryReport>`),
which reports `Delivered`, `Rejected reason` or `NoAnswer` (the channel did not answer
in time, so we do not know whether the notice arrived). The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`; tests give it a
notifier that answers as they choose (see `worldWith` in
`tests/Lending.Tests/Support.fs`).

## LEND-T4-R1

A new command `notify-overdue` sends one notice for each loan that is overdue today
(today is after its due date), unless a notice for that loan's current due date was
delivered, or its outcome is unknown and not yet reconciled (LEND-T4-R3). The notice
goes to the borrower, with subject `Overdue: <title>` and body
`<copy> "<title>" was due <due date>. Please return it.`, for example
`c1 "Dune" was due 2026-03-23. Please return it.` Notices are sent one at a time,
each send finishing before the next starts, ordered by member id and then copy id
(ordinal).

## LEND-T4-R2

Each send's report is interpreted as DEC-008 says: `Delivered` is delivered (never
sent again for that due date); `Rejected reason` is failed (sent again on the next
run); `NoAnswer` is unknown. `notify-overdue` prints a summary and one line per
notice sent, in sending order:

    overdue notices: 1 delivered, 1 failed, 1 unknown
      c1 to m1: delivered
      c2 to s1: failed (mailbox full)
      c3 to t1: unknown, needs reconciliation

With nothing to send it prints `overdue notices: 0 delivered, 0 failed, 0 unknown`.

## LEND-T4-R3

An unknown outcome is kept as an obligation to reconcile: the notice is not sent
again automatically. `obligations` lists the open ones, ordered by copy id:

    awaiting reconciliation:
      c3 to t1, sent 2026-03-25

or `nothing awaits reconciliation`. `reconcile <copy> delivered` records that the
notice arrived (it is then treated as delivered) and prints
`c3 reconciled: delivered`; `reconcile <copy> not-delivered` records that it did not
(it is sent again on the next run) and prints
`c3 reconciled: not delivered, will be sent again`. Reconciling a copy with no open
obligation prints `error: no notice for c3 awaits reconciliation`. Returning the copy
does not close its obligation.

## LEND-T4-R4

`notify-overdue` and `obligations` with extra words, and `reconcile` without exactly
a copy and `delivered` or `not-delivered`, print `usage: ` and the command's line in
`help`. `help` lists, directly after `loans <member>`, the lines `notify-overdue`,
`obligations` and `reconcile <copy> <delivered|not-delivered>`.

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
