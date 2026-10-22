# DEC-008: Overdue notices

Status: accepted (2026-02-17, owner: Head of Lending). Not yet implemented.

A member is sent one overdue notice for each loan that is past its due date. A loan
is never sent a second notice for the same due date once a notice was delivered.

Our notice channel does not always answer. When we do not know whether a notice
arrived, we must not send it again automatically (members complained about
duplicates); instead a member of staff checks with the member and records whether
the notice arrived. A notice the channel rejected was not delivered and is sent
again on the next run.
