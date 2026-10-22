# L08: Notice history and follow-up

Requirements: LEND-L08-R1, LEND-L08-R2. Requested by Customer Services.

## LEND-L08-R1

A new command `notices <member>` lists the overdue notices sent to a member, newest
first (by the day sent; notices sent on the same day by copy id), each with what is
known about its delivery (`delivered`, `rejected`, `unknown`, `confirmed delivered` or
`confirmed not delivered`):

    notices for m1:
      2026-04-02 c1 "Dune": delivered
      2026-03-30 c1 "Dune": unknown

or `no notices for m1`; an unknown member prints `error: unknown member m9`. `help` lists
`notices <member>` directly after `confirm-notice <copy> <delivered|not-delivered>`.

## LEND-L08-R2

Members keep telling us they never received their overdue notice. Customer Services has
decided that from now on `send-notices` sends a notice again, automatically, once its
delivery has been unknown for 2 days or more, so that nobody is left without one.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
