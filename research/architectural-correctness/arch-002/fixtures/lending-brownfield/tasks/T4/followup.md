# T4 follow-up: Restoring one member

Requirements: LEND2-T4-F1.

A member was removed by mistake when an old backup was restored. Staff want to bring
back one member from a backup without replacing everything else.

## LEND2-T4-F1

A new command `restore-member <path> <member>` adds the member from the backup at the
path to the current library, with their fines and payments as the backup has them, and
prints, for example,
`restored member m1 (Ada Lovelace) with 2 fines and 1 payments from /tmp/b.json`.
The member's loans, holds and reminders are not restored, and nothing else changes.
It is refused, changing nothing, with `error: no backup at <path>` when there is no
backup, `error: backup has no member m9` when the backup does not hold the member, and
`error: member m1 already exists` when the current library already has that member.
`help` lists `restore-member <path> <member>` directly after `backup-info <path>`.

Acceptance criteria: the statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
