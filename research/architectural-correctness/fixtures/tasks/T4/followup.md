# T4 follow-up: SMS notices

Requirements: LEND-T4-F1, LEND-T4-F2, LEND-T4-F3.

The library adds SMS as a second notice channel next to email. DEC-008 is unchanged.

## LEND-T4-F1

A new command `channel <member> <email|sms>` sets how a member is notified and prints
`m1 will be notified by sms` (or `by email`). Every member is notified by email until
they choose otherwise. An unknown member prints `error: unknown member m9`, any other
channel name `error: unknown channel <name> (email or sms)`, and the wrong number of
words `usage: channel <member> <email|sms>`. `help` lists that line directly after
`reconcile <copy> <delivered|not-delivered>`.

## LEND-T4-F2

`Notice` gains a field `Channel: Channel`, where `Channel` is a new union with the
cases `Email` and `Sms` in `Lending.Semantic`. Each overdue notice is sent by its
borrower's channel. The host's notifier delivers each notice by the channel it names.

## LEND-T4-F3

When an SMS notice is `Rejected`, the same notice is sent again at once by email (a
second `Send` with `Channel = Email`, before any other notice), and the notice's
outcome is that of the email attempt. When an SMS notice gets `NoAnswer`, it may have
arrived, so it is not sent by email: its outcome is unknown, as before. The
`notify-overdue` output is unchanged: one line per notice with its final outcome.

Acceptance criteria: each statement above holds; everything else behaves as before;
all tests pass with `dotnet test Lending.slnx`.
