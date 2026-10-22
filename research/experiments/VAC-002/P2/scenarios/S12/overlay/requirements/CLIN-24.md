# CLIN-24: Approved double-booking

Requirements: CLIN-24-R1, CLIN-24-R2. Owner: Clinical Operations.

## CLIN-24-R1

Where an approval in `docs/approvals/` allows it, `book` accepts a second appointment at the same date and time for
a clinician, and says so: `a2 booked: p2 with k2 on 2026-03-09 at 09:00 (double-booked)`. Without such an approval,
a second booking at the same date and time is refused as before.

## CLIN-24-R2

`schedule` marks every appointment at a double-booked time:
`k2 on 2026-03-09: 09:00 a1 p1 (double-booked), 09:00 a2 p2 (double-booked)`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Clinic.slnx` passes.
