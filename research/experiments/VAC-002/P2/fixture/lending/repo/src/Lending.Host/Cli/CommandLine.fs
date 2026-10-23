/// The text command line: parse a line, run a use case, render its view.
module Lending.Host.Cli.CommandLine

open System
open Lending.Application

/// Splits a command line into words; double quotes group words containing spaces.
let tokenize (line: string) : Result<string list, string> =
    let rec go (chars: char list) (current: char list option) (inQuotes: bool) (words: string list) =
        let flush () =
            match current with
            | Some cs -> (String(cs |> List.rev |> List.toArray)) :: words
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
    [ "add-member <member> <standard|student|staff> <name>"
      "add-book <book> <isbn> <title> <author>"
      "add-copy <copy> <book>"
      "borrow <member> <copy>"
      "return <copy>"
      "renew <copy>"
      "hold <member> <book>"
      "loans <member>"
      "suspend <member> <reason>"
      "reinstate <member>"
      "member <member>"
      "overdue"
      "help" ]

let private usageOf (command: string) =
    usage |> List.tryFind (fun u -> u = command || u.StartsWith(command + " ", StringComparison.Ordinal))

let private render (show: 'a -> string) (outcome: Result<'a, Lending.Semantic.LendingError>) =
    match outcome with
    | Ok view -> show view
    | Error error -> "error: " + Views.describeError error

let private showMember (v: Views.MemberView) = $"member {v.Member} added: {v.Name} ({v.Type})"
let private showBook (v: Views.BookView) = $"book {v.Book} added: {v.Title} by {v.Author}"
let private showCopy (v: Views.CopyView) = $"copy {v.Copy} added for book {v.Book}"
let private showBorrow (v: Views.BorrowView) = $"{v.Copy} lent to {v.Member}, due {v.Due}"

let private showReturn (v: Views.ReturnView) =
    match v.Fine with
    | Some fine -> $"{v.Copy} returned {v.DaysLate} days late, fine {fine}"
    | None -> $"{v.Copy} returned"

let private showHold (v: Views.HoldView) = $"{v.Member} holds {v.Book} at position {v.Position}"

let private showLoans (v: Views.MemberLoansView) =
    match v.Loans with
    | [] -> $"no loans for {v.Member} ({v.Name})"
    | loans ->
        $"loans for {v.Member} ({v.Name}):"
        :: (loans
            |> List.map (fun loan ->
                let renewed = if loan.Renewals > 0 then $" (renewed {loan.Renewals})" else ""
                $"  {loan.Copy} \"{loan.Title}\" due {loan.Due}{renewed}"))
        |> String.concat "\n"

let private showSuspended (v: Views.StandingView) =
    $"{v.Member} suspended: {defaultArg v.Suspension String.Empty}"

let private showReinstated (v: Views.StandingView) = $"{v.Member} reinstated"

let private showStanding (v: Views.StandingView) =
    match v.Suspension with
    | Some reason -> $"{v.Member} {v.Name} ({v.Type}), suspended: {reason}"
    | None -> $"{v.Member} {v.Name} ({v.Type}), active"

let private plural n unit = if n = 1 then $"{n} {unit}" else $"{n} {unit}s"

let private showOverdue (lines: Views.OverdueLine list) =
    $"overdue loans: {List.length lines}"
    :: (lines
        |> List.map (fun l ->
            let days = plural l.DaysOverdue "day"
            $"  {l.Copy} \"{l.Title}\", {l.Member} {l.Name}, due {l.Due}, {days} overdue"))
    |> String.concat "\n"

let private showRenew (v: Views.RenewView) =
    $"{v.Copy} renewed, due {v.Due} (renewal {v.Renewal} of {v.Limit})"

/// Runs one command line against the ports and returns the text to show.
let run (ports: Ports) (line: string) : string =
    match tokenize line with
    | Error message -> "error: " + message
    | Ok [] -> "error: empty command"
    | Ok [ "help" ] -> String.concat "\n" usage
    | Ok [ "add-member"; m; kind; name ] -> UseCases.addMember ports m kind name |> render showMember
    | Ok [ "add-book"; b; isbn; title; author ] -> UseCases.addBook ports b isbn title author |> render showBook
    | Ok [ "add-copy"; c; b ] -> UseCases.addCopy ports c b |> render showCopy
    | Ok [ "borrow"; m; c ] -> UseCases.borrow ports m c |> render showBorrow
    | Ok [ "return"; c ] -> UseCases.returnCopy ports c |> render showReturn
    | Ok [ "renew"; c ] -> UseCases.renew ports c |> render showRenew
    | Ok [ "hold"; m; b ] -> UseCases.placeHold ports m b |> render showHold
    | Ok [ "loans"; m ] -> UseCases.loans ports m |> render showLoans
    | Ok [ "suspend"; m; reason ] -> UseCases.suspend ports m reason |> render showSuspended
    | Ok [ "reinstate"; m ] -> UseCases.reinstate ports m |> render showReinstated
    | Ok [ "member"; m ] -> UseCases.standing ports m |> render showStanding
    | Ok [ "overdue" ] -> UseCases.overdue ports |> showOverdue
    | Ok(command :: _) ->
        match usageOf command with
        | Some u -> "usage: " + u
        | None -> $"error: unknown command '{command}' (try help)"
