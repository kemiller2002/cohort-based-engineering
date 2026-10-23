# CLIN-53: Moving an appointment

Requirements: CLIN-53-R1, CLIN-53-R2. Owner: Clinical Operations.

## CLIN-53-R1

A new command `move <appointment> <date> <time>` moves an appointment to another date and time with the same
clinician, under the same rules as booking a new appointment, and prints `a1 moved to 2026-03-12 at 10:00`. A move
that a new booking at that date and time would be refused for is refused with the same error, and changes nothing.
An unknown appointment prints `error: unknown appointment a9`.

## CLIN-53-R2

`help` lists `move <appointment> <date> <time>` directly after `cancel <appointment>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
