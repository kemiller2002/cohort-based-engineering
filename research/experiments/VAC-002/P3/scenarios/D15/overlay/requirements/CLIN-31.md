# CLIN-31: Clinician leave

Requirements: CLIN-31-R1, CLIN-31-R2. Owner: Clinical Operations.

## CLIN-31-R1

A new command `leave <clinician> <date>` records that the clinician is away for that whole day, and prints
`k1 on leave 2026-03-10`. An unknown clinician prints `error: unknown clinician k9`. `help` lists
`leave <clinician> <date>` directly after `schedule <clinician> <date>`.

## CLIN-31-R2

Booking a clinician on a day they are on leave is refused: `error: k1 is on leave on 2026-03-10`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
