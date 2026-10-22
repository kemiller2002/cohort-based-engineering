# T3: Bulk import of books

Requirements: LEND-T3-R1, LEND-T3-R2, LEND-T3-R3.

Cataloguing staff receive new stock as a CSV file and today type every book and copy
in by hand. The command line is
`Lending.Host.Cli.CommandLine.run : Ports -> string -> string`.

## LEND-T3-R1

A new command `import <path>` reads a CSV file. Its first line must be exactly

    book,isbn,title,author,copies

otherwise (or when the file is empty) the command prints
`error: the first line must be book,isbn,title,author,copies` and imports nothing. A
file that cannot be read prints `error: cannot read <path>` (the path as typed).
Each later line is one book. Fields are separated by commas; a field written in
double quotes may contain commas (the quotes are not part of the value); spaces around
a field are removed. Blank lines are ignored. `import` with the wrong number of words
prints `usage: import <path>`, and `help` lists `import <path>` on its own line
directly after `add-copy <copy> <book>`.

## LEND-T3-R2

Each row adds its book (id, isbn, title, author) and `copies` copies of it, with copy
ids `<book>-1`, `<book>-2`, … up to `<book>-<copies>`, exactly as `add-book` and
`add-copy` would. Rows are taken in file order, and a row is all or nothing: a row is
skipped, and adds neither its book nor any of its copies, when it does not have 5
fields (`expected 5 fields`), when `copies` is not a whole number from 1 to 20
(`copies must be a whole number from 1 to 20`), or when `add-book` or `add-copy` would
refuse the book or one of its copies (the error text, for example
`book b1 already exists` or `copy b1-1 already exists`). The other rows are still
imported.

## LEND-T3-R3

`import` prints a summary line and then one line per skipped row, in file order,
numbering lines from 1 for the header and counting blank lines:

    imported 2 books, 5 copies
      line 3: skipped: book b1 already exists
      line 5: skipped: copies must be a whole number from 1 to 20

Acceptance criteria: each statement above holds; existing commands keep their output;
all tests pass with `dotnet test Lending.slnx`.
