/// The text command line: parse a line, run a command against the session's state, print the result.
/// Stable entry points (README): `Session.create`, `Session.withState`, `run`.
module Billing.Cli

open System
open Billing.Domain

/// A running program: the current state and a clock. The only mutable cell is the state reference.
type Session =
    { State: State ref
      Today: unit -> DateOnly }

[<RequireQualifiedAccess>]
module Session =

    let create (today: unit -> DateOnly) = { State = ref State.empty; Today = today }

    let withState (state: State) (today: unit -> DateOnly) = { State = ref state; Today = today }

/// Splits a command line into words; double quotes group words containing spaces.
let tokenize (line: string) : Result<string list, string> =
    let rec go (chars: char list) (current: char list option) (inQuotes: bool) (words: string list) =
        let flush () =
            match current with
            | Some cs -> String(cs |> List.rev |> List.toArray) :: words
            | None -> words

        match chars, inQuotes with
        | [], true -> Error "unterminated quote"
        | [], false -> Ok(List.rev (flush ()))
        | '"' :: rest, false -> go rest (Some(defaultArg current [])) true words
        | '"' :: rest, true -> go rest current false words
        | c :: rest, false when Char.IsWhiteSpace c -> go rest None false (flush ())
        | c :: rest, _ -> go rest (Some(c :: defaultArg current [])) inQuotes words

    go (List.ofSeq line) None false []

let usage =
    [ "add-customer <customer> <standard|premium> <business|nonprofit> <region> <name>"
      "invoice <invoice> <customer> <amount>"
      "show <invoice>"
      "balance <customer>"
      "run-late-fees"
      "help" ]

let private usageOf (command: string) =
    usage |> List.tryFind (fun u -> u = command || u.StartsWith(command + " ", StringComparison.Ordinal))

let private dispatch (today: DateOnly) (words: string list) (state: State) : Result<State * string, string> =
    let fromDomain result = result |> Result.mapError Commands.describeError

    match words with
    | [ "add-customer"; id; plan; kind; region; name ] ->
        Plan.parse plan
        |> Result.bind (fun p -> CustomerKind.parse kind |> Result.map (fun k -> p, k))
        |> Result.bind (fun (p, k) -> Commands.addCustomer id p k region name state)
        |> fromDomain
    | [ "invoice"; id; customerId; amount ] ->
        Commands.parseAmount amount
        |> Result.bind (fun a -> Commands.issueInvoice today id customerId a state)
        |> fromDomain
    | [ "show"; id ] -> Commands.show id state |> fromDomain
    | [ "balance"; customerId ] -> Commands.balance customerId state |> fromDomain
    | [ "run-late-fees" ] -> Commands.runLateFees today state |> fromDomain
    | [ "help" ] -> Ok(state, String.Join("\n", usage))
    | command :: _ ->
        match usageOf command with
        | Some u -> Error $"usage: {u}"
        | None -> Error $"unknown command {command}"
    | [] -> Error "empty command"

/// Runs one command line against the session and returns its output.
let run (session: Session) (line: string) : string =
    match tokenize line |> Result.bind (fun words -> dispatch (session.Today()) words session.State.Value) with
    | Ok(next, output) ->
        session.State.Value <- next
        output
    | Error message -> "error: " + message
