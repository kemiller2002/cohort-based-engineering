# CLIN-23: Dose limits

Requirements: CLIN-23-R1, CLIN-23-R2. Owner: Pharmacy.

## CLIN-23-R1

`prescribe` refuses a dose above the drug's maximum single dose in `docs/formulary.md`:
`error: dose 900 mg exceeds the maximum 800 mg for ibuprofen`. A dose equal to the maximum is accepted. A drug that
is not in the formulary is refused: `error: drug aspirin is not in the formulary`.

## CLIN-23-R2

Before this change is released, Pharmacy verifies that the maximum doses the program uses match the formulary, and
records that verification in `docs/verification/`. CLIN-23 is complete only when that verification is recorded.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged; `dotnet test Clinic.slnx` passes.
