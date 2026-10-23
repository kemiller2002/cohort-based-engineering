# CLIN-42: Dispense everything that is ready

Requirements: CLIN-42-R1, CLIN-42-R2. Owner: Pharmacy.

## CLIN-42-R1

A new command `dispense-ready` dispenses, in queue order, every prescription in the queue that may be dispensed now,
and prints the ids it dispensed: `dispensed: rx1, rx3`, or `dispensed: none`. Prescriptions it does not dispense stay
in the queue.

## CLIN-42-R2

`help` lists `dispense-ready` directly after `dispense <prescription>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
