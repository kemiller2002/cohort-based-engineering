# CLIN-32: Repeat prescriptions

Requirements: CLIN-32-R1, CLIN-32-R2. Owner: Medical Director.

## CLIN-32-R1

A new command `repeat <prescription> <new-prescription>` issues a dispensed prescription again under the new id, for
the same patient, drug and dose, and prints `rx2 repeats rx1: amoxicillin 500 mg for p1`. Only a dispensed
prescription can be repeated; otherwise it prints `error: rx1 has not been dispensed`. An unknown prescription prints
`error: unknown prescription rx9`, and a new id that is already used prints `error: prescription rx2 already exists`.

## CLIN-32-R2

`help` lists `repeat <prescription> <new-prescription>` directly after `dispense <prescription>`. A repeat joins the
queue like any new prescription.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
