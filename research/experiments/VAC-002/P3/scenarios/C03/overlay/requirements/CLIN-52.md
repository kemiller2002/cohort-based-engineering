# CLIN-52: Visit fee of an appointment

Requirements: CLIN-52-R1, CLIN-52-R2. Owner: Finance.

## CLIN-52-R1

A new command `fee <appointment>` prints the fee for the appointment's visit, as DEC-C09 sets it:
`a1 visit fee 60.00`. It changes nothing. An unknown appointment prints `error: unknown appointment a9`.

## CLIN-52-R2

`help` lists `fee <appointment>` directly after `cancel <appointment>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
