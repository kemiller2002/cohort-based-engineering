# L11: Member export

Requirements: LEND-L11-R1, LEND-L11-R2. Owner: Head of Lending.

## LEND-L11-R1

A new command `export-members` prints every member as CSV (RFC 4180): the header line
`id,name,type,status,owes`, then one line per member ordered by member id (ordinal), for
example `m1,Ada Lovelace,standard,active,0.00`. `status` is `active` or `suspended`
(LEND-L01); `owes` is exactly what `owes <member>` reports.

## LEND-L11-R2

A field that contains a comma, a double quote or a line break is enclosed in double
quotes, and each double quote inside it is doubled: the name `Ada "Countess" Lovelace`
is written `"Ada ""Countess"" Lovelace"`. `help` lists `export-members` directly after
`expire-holds`.

Acceptance criteria: each statement above holds; the standing requirements in
`README.md` hold; existing behaviour is unchanged; `dotnet test Lending.slnx` passes.
