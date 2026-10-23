# CLIN-41: Next free day

Requirements: CLIN-41-R1, CLIN-41-R2. Owner: Clinical Operations.

## CLIN-41-R1

A new command `next-free <clinician> <time>` finds the first day, from tomorrow, on which the clinician has no
appointment at that time and an appointment can be booked under the booking-horizon decision in force, and prints
`k1 free at 09:00 on 2026-03-03`. If there is no such day it prints `k1 has no free day at 09:00`. It books nothing.
An unknown clinician prints `error: unknown clinician k9`.

## CLIN-41-R2

`help` lists `next-free <clinician> <time>` directly after `schedule <clinician> <date>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
