# L07: Overdue notices

Requirements: LEND-L07-R1, LEND-L07-R2, LEND-L07-R3. Owner: Head of Lending. Implements
DEC-008 (`docs/decisions/DEC-008-overdue-notices.md`) through the existing `Notifier` port.

## LEND-L07-R1

A new command `send-notices` sends an overdue notice for every loan that is past its due
date today and still needs one (R2). A notice goes to the borrower with the subject
`Overdue: Dune` (the book's title) and the body
`Copy c1 of "Dune" was due on 2026-03-23.` The command prints a summary and then one line
per notice sent, in copy-id order, with what the channel reported (`delivered`,
`rejected` or `unknown`):

    notices: 2 sent, 1 delivered, 1 rejected, 0 unknown
      c1 to m1: delivered
      c3 to s1: rejected

When nothing needs sending it prints `notices: 0 sent, 0 delivered, 0 rejected, 0 unknown`.

## LEND-L07-R2

A loan needs a notice unless a notice for its current due date was delivered, or its
delivery is unknown. A notice the channel rejected was not delivered, so the loan needs
a notice again on the next run. When the channel gives no answer, the delivery is
unknown and the notice is not sent again automatically (DEC-008).

`unknown-notices` lists the notices whose delivery is unknown, in copy-id order:

    unknown notices: 1
      c1 to m1, sent 2026-03-30

(`unknown notices: 0` when there are none). Staff record what the member said with
`confirm-notice <copy> delivered` or `confirm-notice <copy> not-delivered`, which print
`notice for c1 recorded as delivered` (or `as not delivered`). A notice confirmed as
delivered counts as delivered; one confirmed as not delivered makes the loan need a
notice again on the next run. For a copy without an unknown notice it prints
`error: no unknown notice for c1`; any other answer prints
`error: answer must be delivered or not-delivered`.

## LEND-L07-R3

Each loan is notified on its own: when a copy is returned and later lent again, the new
loan needs its own notice once it is overdue. `help` lists `send-notices`,
`unknown-notices` and `confirm-notice <copy> <delivered|not-delivered>`, in that order,
directly after `waive <copy> <approver>`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
