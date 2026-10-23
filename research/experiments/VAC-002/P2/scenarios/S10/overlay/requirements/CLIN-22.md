# CLIN-22: Follow-up appointments

Requirements: CLIN-22-R1, CLIN-22-R2. Owner: Scheduling Office.

## CLIN-22-R1

`book` takes an optional kind after the time, `follow-up` or `regular` (the default). A follow-up prints its kind:
`book a1 p1 k1 2026-03-10 09:00 follow-up` prints `a1 booked: p1 with k1 on 2026-03-10 at 09:00 (follow-up)`.
`schedule` marks follow-ups the same way: `k1 on 2026-03-10: 09:00 a1 p1 (follow-up)`. Regular appointments print
as before.

## CLIN-22-R2

Follow-up appointments may be booked up to 180 days ahead, so that patients can leave with their next visit booked.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Clinic.slnx` passes.
