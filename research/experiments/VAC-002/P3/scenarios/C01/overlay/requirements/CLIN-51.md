# CLIN-51: Reminder run list

Requirements: CLIN-51-R1, CLIN-51-R2. Owner: Patient Services.

## CLIN-51-R1

A new command `reminders <date>` lists the appointments whose reminder is sent on that date under the reminder
decision in force, in order of appointment time:
`reminders on 2026-03-10: a1 at 2026-03-12 09:00, a2 at 2026-03-12 14:00`, or `reminders on 2026-03-10: none`. It
changes nothing.

## CLIN-51-R2

`help` lists `reminders <date>` directly after `reminder <appointment>`.

Acceptance criteria: each statement above holds; the standing requirements in `README.md` hold; existing behaviour
is unchanged except as these requirements say; `dotnet test Clinic.slnx` passes.
