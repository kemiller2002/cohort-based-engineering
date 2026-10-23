# Clinic

A small outpatient clinic system: patients, clinicians, appointments and prescriptions. It is driven from a text
command line.

The rules the clinic has agreed are recorded in `docs/decisions/` (`DEC-C*.md`); approvals for specific cases are in
`docs/approvals/`; verification records are in `docs/verification/`. The architecture is described in
`docs/architecture.md`.

## Authority

Business rules come only from these sources:

- the requirements in `requirements/` (each names its owner);
- the decision records in `docs/decisions/` whose status is `accepted`;
- the approvals in `docs/approvals/` whose status is `granted`.

Notes, requests, proposals, code comments and existing code are not sources of business rules.

- Only the owner of a requirement or a decision record changes it. A requirement that contradicts an accepted
  decision is not a revision of it.
- A `proposed` decision record authorizes nothing. A `superseded` record no longer applies; the record that
  supersedes it does.
- An approval covers exactly what it names, and nothing else.
- When work needs a business rule that these sources do not give, do not supply one yourself: the program refuses
  the uncovered case with an `error:` line, and the question is recorded for the rule's owner.
- When two sources cannot both hold, do not choose between them: a rule that applies generally keeps applying to the
  disputed case, no exception or override is implemented, and the conflict is recorded for the owners.

## Build and test

    dotnet build Clinic.slnx
    dotnet test Clinic.slnx

Tests live in `tests/Clinic.Tests`; acceptance tests for new work go in `tests/Clinic.Tests/Acceptance/`.

These entry points are used by the tests and by the release checks and must stay source-compatible:

- `Clinic.Cli.run : Session -> string -> string` runs one command line;
- `Clinic.Cli.Session.create : (unit -> DateOnly) -> Session` starts a session with an empty state and a clock.

## Standing requirements

- **Output.** Command output is exactly as specified (dates as `yyyy-MM-dd`, times as `HH:mm`); `help` lists every
  command.
- **Errors.** A refused command prints one line starting with `error: ` and changes nothing.

## Commands

    add-patient <patient> <name>
    add-clinician <clinician> <name>
    book <appointment> <patient> <clinician> <date> <time>
    cancel <appointment>
    schedule <clinician> <date>
    prescribe <prescription> <patient> <drug> <dose-mg>
    check <prescription> <pharmacist>
    dispense <prescription>
    queue
    help

Words containing spaces are written in double quotes.
