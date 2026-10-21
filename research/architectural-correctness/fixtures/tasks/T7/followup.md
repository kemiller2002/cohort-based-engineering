# T7 follow-up: A JSON surface

Requirements: LEND-T7-F1, LEND-T7-F2.

The library's web page wants to borrow, return and list loans without screen-scraping
the command line. Add a second text surface next to the command line, in
`src/Lending.Host/Cli/JsonApi.fs`, as module `Lending.Host.Cli.JsonApi`, with
`handle : Ports -> string -> string`: a JSON request in, a JSON response out. It
does what the command line does for the same request, with the same rules and the
same error texts.

## LEND-T7-F1

Requests are objects with a `command` field and the command's fields:

| command | fields | response when it succeeds |
|---|---|---|
| `borrow` | `member`, `copy` | `{"ok": true, "copy": "c1", "member": "m1", "due": "2026-03-23"}` |
| `return` | `copy` | `{"ok": true, "copy": "c1", "daysLate": 3, "fine": "0.75"}`; `"daysLate": 0, "fine": null` when on time |
| `loans` | `member` | `{"ok": true, "member": "m1", "name": "Ada Lovelace", "loans": [{"copy": "c1", "title": "Dune", "due": "2026-03-23"}]}` |

Loans are in the same order as the command line's listing.

## LEND-T7-F2

A refused request gets `{"ok": false, "error": "<text>"}`, where the text is the
command line's error text without `error: `, for example
`{"ok": false, "error": "copy c1 is already on loan"}`. A request that is not a JSON
object gets the error `malformed request`, one without a string `command` field or
with an unknown command gets `unknown command '<command>'` (`unknown command ''` when
it is missing), and one missing a field (or with a field that is not a string) gets
`missing field '<name>'`.

Acceptance criteria: each statement above holds; the command line behaves as before;
all tests pass with `dotnet test Lending.slnx`.
