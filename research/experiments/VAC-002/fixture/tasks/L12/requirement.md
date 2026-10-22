# L12: Loan periods by member type

Requirements: LEND-L12-R1, LEND-L12-R2. Owner: Head of Lending. Implements DEC-001
revision 3 and DEC-004 revision 3.

## LEND-L12-R1

A loan lasts as long as the borrower's member type allows: standard 21 days, student 14
days, staff 42 days. This applies to new loans and to renewals: each renewal moves the
due date one loan period of the borrower's type later. Due dates still move to the next
open day (LEND-L09-R1). Loans made before this change keep their due dates.

## LEND-L12-R2

A new command `periods` prints the loan periods:
`loan periods: standard 21 days, student 14 days, staff 42 days`. `help` lists `periods`
directly after `export-members`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged except as stated; `dotnet test
Lending.slnx` passes (update a test only where this requirement changes the behaviour it
checks).
