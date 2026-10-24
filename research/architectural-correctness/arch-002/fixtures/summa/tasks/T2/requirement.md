# T2: Moving local books to another browser

Requirements: SUMMA-T2-R1, SUMMA-T2-R2, SUMMA-T2-R3.

A deployment without a data location keeps its books only in this browser
(DF-SUMMA-2026-0009), so a person who changes computer loses them. Summa should let them
carry the books over in a file: a transfer file written in one browser and imported in
another. The file is a financial export (DF-SUMMA-2026-0041), and imported books are
trusted no more than any stored books: they are checked, and refused when they fail
(DF-SUMMA-2026-0009).

## SUMMA-T2-R1

A new module `Summa.Storage.Transfer` writes the transfer file:

    Transfer.export : Organization.OrganizationManifest -> Receivables -> exportedAt: DateTimeOffset
                      -> Result<string, string>

The file is the JSON document `summa.books-transfer` version 1, with no whitespace:

    {"schema":"summa.books-transfer","version":1,"classification":"confidential financial data",
     "organization":{"id":"org_local","name":"Demo Consulting"},"exportedAt":"2026-10-07T09:00:00Z",
     "dataVersion":"sha256:...","snapshot":"..."}

`organization` is the manifest's id and display name; `exportedAt` is UTC to the second;
`dataVersion` is the books' data version (`Exports.dataVersion`); `snapshot` is the text
this browser keeps its books as (`LocalSnapshot.encode`), as one JSON string. Books that
cannot be stored are an `Error` with the reason as a sentence.

## SUMMA-T2-R2

`Transfer.read : string -> Result<Transferred, string>` reads a transfer file back, with

    type Transferred = { Manifest: Organization.OrganizationManifest; Books: Receivables
                         ExportedAt: DateTimeOffset; DataVersion: string }

It refuses, with exactly these sentences and checked in this order:

1. text that is not a JSON object whose `schema` is `summa.books-transfer`:
   `This is not a Summa books transfer file.`;
2. another version: `Transfer files of version 2 cannot be read here.` (with its number);
3. a snapshot that cannot be read back, or whose books fail any check:
   `The books in this file failed their checks: <the first problem>`;
4. books whose data version is not the file's `dataVersion`:
   `The books in this file do not match its data version.`

## SUMMA-T2-R3

On the Settings page (`Routes.Settings`) of local books:

- The engine message `BooksTransferRequested` offers the transfer file, exported now, as
  one download and no other effect: `summa-books-<organization id>-<business date>.json`
  (date `yyyy-MM-dd`), media type `application/json`.
- `BooksTransferTextChanged of string` keeps a pasted transfer file (view value
  `booksTransferText`), and `BooksTransferImported` imports it:
  - books that already hold a customer, draft, invoice or payment are not replaced:
    `Error = Some "Books can only be imported into new books; these books already hold records."`;
  - a refused file: `Error = Some "This file cannot be imported: <the R2 sentence>"`;
  - otherwise the file's manifest and books replace this browser's, the browser saves
    them (one `SaveBooks` effect), the pasted text is cleared and the notice is
    `Books imported from a transfer file exported on 2026-10-07.` (the export's UTC date).
- Without the files pack, `BooksTransferRequested` sets the existing error
  `This browser cannot offer downloads here.`. Books on GitHub are moved with their
  repository, so on them both messages offer nothing and set the error
  `Books on GitHub are moved with their repository, not with a transfer file.`.
- The kernel events are `booksTransferRequested`, `booksTransferTextChanged` (value: the
  text) and `booksTransferImported`; `app/index.html`'s Settings page offers them.

Acceptance criteria: each statement above holds; existing behaviour is unchanged; all
tests pass with `dotnet test Summa.sln`.
