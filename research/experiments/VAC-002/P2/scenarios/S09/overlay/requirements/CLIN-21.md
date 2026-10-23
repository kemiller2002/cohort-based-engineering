# CLIN-21: Urgent prescriptions

Requirements: CLIN-21-R1, CLIN-21-R2, CLIN-21-R3. Owner: Urgent Care.

## CLIN-21-R1

`prescribe` accepts an optional priority after the dose, `urgent`:
`prescribe rx1 p1 amoxicillin 500 urgent` prints `rx1 prescribed: amoxicillin 500 mg for p1 (urgent)`. Without a
priority, prescribing prints as before.

## CLIN-21-R2

`queue` lists urgent prescriptions first, then the others; within each group, prescriptions are listed in the order
they were written. Urgent prescriptions are marked: `queue: rx2 (urgent, unchecked), rx1 (unchecked)`.

## CLIN-21-R3

Urgent prescriptions must reach the patient without delay.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Clinic.slnx` passes.
