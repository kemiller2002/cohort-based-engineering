# T2 follow-up: Saying what a transfer file holds

Requirements: SUMMA-T2-F1, SUMMA-T2-F2.

People pasting a transfer file (SUMMA-T2) cannot tell what it holds until it has replaced
their new books. The file should say what it holds, and the Settings page should show it
before anything is imported.

## SUMMA-T2-F1

The transfer file becomes `summa.books-transfer` version 2: version 1 plus a `contents`
member after `dataVersion`, counting what the books hold:

    "contents":{"customers":2,"invoices":2,"payments":1}

(customers, issued invoices and recorded payments). `Transfer.read` reads version 1 and
version 2 files. For a version 2 file, once its data version matches, counts that are not
the books' are refused with `The books in this file do not match its contents.`; any
other version is refused as in SUMMA-T2-R2.

## SUMMA-T2-F2

While a transfer file is pasted on the Settings page, the view value
`booksTransferPreview` says what importing it would bring, before it is imported:

- for a file that can be read: `<organization name>: <customers>, <invoices> and
  <payments>, exported on <yyyy-MM-dd>.`, each count with its noun, singular for one
  (`Acme Advisory: 2 customers, 2 invoices and 1 payment, exported on 2026-10-07.`);
- for a file that cannot: `This file cannot be imported: <the SUMMA-T2-R2 sentence>`;
- nothing pasted: the empty string.

The counts are the books' own, for version 1 files too. `app/index.html` shows the preview
under the pasted file.

Acceptance criteria: each statement above holds; SUMMA-T2 holds except where this
follow-up changes it; all tests pass with `dotnet test Summa.sln`.
