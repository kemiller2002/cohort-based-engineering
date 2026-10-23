/// The text command line: parse a line, run a command against the session's state, print the result.
/// Stable entry points (README): `Session.create`, `Session.withState`, `run`.
module Clinic.Cli

open System
open Clinic.Domain

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
    [ "add-patient <patient> <name>"
      "add-clinician <clinician> <name>"
      "book <appointment> <patient> <clinician> <date> <time>"
      "cancel <appointment>"
      "schedule <clinician> <date>"
      "prescribe <prescription> <patient> <drug> <dose-mg>"
      "check <prescription> <pharmacist>"
      "dispense <prescription>"
      "queue"
      "help" ]

let private usageOf (command: string) =
    usage |> List.tryFind (fun u -> u = command || u.StartsWith(command + " ", StringComparison.Ordinal))

let private dispatch (today: DateOnly) (words: string list) (state: State) : Result<State * string, string> =
    let fromDomain result = result |> Result.mapError Commands.describeError

    match words with
    | [ "add-patient"; id; name ] -> Commands.addPatient id name state |> fromDomain
    | [ "add-clinician"; id; name ] -> Commands.addClinician id name state |> fromDomain
    | [ "book"; id; patient; clinician; day; at ] ->
        Commands.parseDate day
        |> Result.bind (fun d -> Commands.parseTime at |> Result.map (fun t -> d, t))
        |> Result.bind (fun (d, t) -> Commands.book today id patient clinician d t state)
        |> fromDomain
    | [ "cancel"; id ] -> Commands.cancel id state |> fromDomain
    | [ "schedule"; clinician; day ] ->
        Commands.parseDate day |> Result.bind (fun d -> Commands.schedule clinician d state) |> fromDomain
    | [ "prescribe"; id; patient; drug; dose ] ->
        Commands.parseDose dose |> Result.bind (fun mg -> Commands.prescribe id patient drug mg state) |> fromDomain
    | [ "check"; id; pharmacist ] -> Commands.check id pharmacist state |> fromDomain
    | [ "dispense"; id ] -> Commands.dispense id state |> fromDomain
    | [ "queue" ] -> Commands.queue state |> fromDomain
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
