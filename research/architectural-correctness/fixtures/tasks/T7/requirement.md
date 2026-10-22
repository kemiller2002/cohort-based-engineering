# T7: Restructure the command line

Requirements: LEND-T7-R1, LEND-T7-R2, LEND-T7-R3.

`src/Lending.Host/Cli/CommandLine.fs` parses words, decides what to call and formats
the answer in one match, and every new command makes it longer. Restructure it so
that parsing, running and rendering are separate, without changing what the program
does.

## LEND-T7-R1

A new module `Lending.Host.Cli.Command` (`src/Lending.Host/Cli/Command.fs`) defines
the commands the line understands:

```fsharp
type Command =
    | Help
    | AddMember of memberId: string * memberType: string * name: string
    | AddBook of bookId: string * isbn: string * title: string * author: string
    | AddCopy of copyId: string * bookId: string
    | Borrow of memberId: string * copyId: string
    | Return of copyId: string
    | Hold of memberId: string * bookId: string
    | Loans of memberId: string
```

## LEND-T7-R2

A new module `Lending.Host.Cli.Parse` (`src/Lending.Host/Cli/Parse.fs`) has
`tokenize : string -> Result<string list, string>` (moved from `CommandLine`, same
behavior) and `command : string -> Result<Command.Command, string>`, which turns a
whole line into a command. Its `Error` is exactly the text `run` prints for a line
that is not a valid command: `error: unterminated quote`, `error: empty command`,
`usage: <the command's help line>` for a known command with the wrong number of
words, or `error: unknown command '<word>' (try help)`. Parsing does not look at the
library's state; for example, `add-member m1 vip Bob` parses (the member type is
checked when the command runs).

## LEND-T7-R3

Rendering of results as text moves to a new module `Lending.Host.Cli.Render`
(`src/Lending.Host/Cli/Render.fs`). `CommandLine` keeps `usage` and
`run : Ports -> string -> string`, which now parses the line, runs the command and
renders its result. For every input line and every state, `run` returns exactly
what it returned before, and changes the state exactly as before.

Acceptance criteria: each statement above holds; all tests pass with
`dotnet test Lending.slnx`.
