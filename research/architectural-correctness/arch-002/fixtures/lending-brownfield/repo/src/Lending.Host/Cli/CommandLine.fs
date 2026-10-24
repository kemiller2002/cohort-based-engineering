/// The text command line: parse a line, run a use case, render its view.
module Lending.Host.Cli.CommandLine

open System
open Lending.Semantic
open Lending.Transition
open Lending.Application
open Lending.Host.Persistence

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
      "add-branch <branch> <name>"
      "add-copy <copy> <book> [<branch>]"
      "transfer <copy> <branch>"
      "shelf <branch>"
      "borrow <member> <copy>"
      "return <copy>"
      "renew <copy>"
      "hold <member> <book>"
      "cancel-hold <member> <book>"
      "holds <book>"
      "loans <member>"
      "account <member>"
      "pay <member> <amount>"
      "overdue"
      "export-overdue <path>"
      "remind"
      "reconcile <copy> <arrived|missing>"
      "members"
      "import-members <path>"
      "backup <path>"
      "help" ]

let private usageOf (command: string) =
    usage |> List.tryFind (fun u -> u = command || u.StartsWith(command + " ", StringComparison.Ordinal))

let private render (show: 'a -> string) (outcome: Result<'a, LendingError>) =
    match outcome with
    | Ok view -> show view
    | Error error -> "error: " + Views.describeError error

let private lines (header: string) (items: string list) =
    header :: (items |> List.map (fun item -> "  " + item)) |> String.concat "\n"

let private showMember (v: Views.MemberView) = $"member {v.Member} added: {v.Name} ({v.Type})"
let private showBook (v: Views.BookView) = $"book {v.Book} added: {v.Title} by {v.Author}"
let private showBranch (v: Views.BranchView) = $"branch {v.Branch} added: {v.Name}"
let private showCopy (v: Views.CopyView) = $"copy {v.Copy} added for book {v.Book} at {v.Branch}"
let private showTransfer (v: Views.TransferView) = $"{v.Copy} moved to {v.Branch} ({v.BranchName})"
let private showBorrow (v: Views.BorrowView) = $"{v.Copy} lent to {v.Member}, due {v.Due}"

let private showReturn (v: Views.ReturnView) =
    match v.Fine with
    | Some fine -> $"{v.Copy} returned {v.DaysLate} days late, fine {fine}"
    | None -> $"{v.Copy} returned"

let private showHold (v: Views.HoldView) = $"{v.Member} holds {v.Book} at position {v.Position}"
let private showCancelHold (v: Views.CancelHoldView) = $"{v.Member} no longer holds {v.Book}"

let private showQueue (v: Views.HoldQueueView) =
    match v.Queue with
    | [] -> $"no holds for {v.Book} ({v.Title})"
    | queue ->
        queue
        |> List.map (fun e -> $"{e.Position}. {e.Member} ({e.Name}) since {e.Since}")
        |> lines $"holds for {v.Book} ({v.Title}):"

let private showShelf (v: Views.ShelfView) =
    match v.Copies with
    | [] -> $"no copies at {v.Branch} ({v.Name})"
    | copies ->
        copies
        |> List.map (fun c ->
            match c.DueBack with
            | Some due -> $"{c.Copy} \"{c.Title}\" on loan, due {due}"
            | None -> $"{c.Copy} \"{c.Title}\" on shelf")
        |> lines $"copies at {v.Branch} ({v.Name}):"

let private showLoans (v: Views.MemberLoansView) =
    match v.Loans with
    | [] -> $"no loans for {v.Member} ({v.Name})"
    | loans -> loans |> List.map (fun loan -> $"{loan.Copy} \"{loan.Title}\" due {loan.Due}") |> lines $"loans for {v.Member} ({v.Name}):"

let private showAccount (v: Views.AccountView) =
    [ yield! v.Fines |> List.map (fun f -> $"fine {f.Copy} {f.Amount} assessed {f.AssessedOn}")
      yield! v.Payments |> List.map (fun p -> $"paid {p}") ]
    |> lines $"account for {v.Member} ({v.Name}):"
    |> fun body -> $"{body}\nowed: {v.Owed}\nloans: {v.LoansHeld} of {v.LoanAllowance}"

let private showPayment (v: Views.PaymentView) = $"{v.Member} paid {v.Paid}, owes {v.Owed}"

let private showOverdue (v: Views.OverdueView) =
    match v.Loans with
    | [] -> $"no overdue loans on {v.Today}"
    | loans ->
        loans
        |> List.map (fun l -> $"{l.Copy} \"{l.Title}\" lent to {l.Member}, due {l.Due}, {l.DaysOverdue} days overdue")
        |> lines $"overdue loans on {v.Today}:"

let private showExport (v: Views.ExportView) = $"exported {v.Rows} overdue loans to {v.Path}"

let private showReminders (v: Views.ReminderRunView) =
    $"reminders: {v.Sent} sent, {v.Bounced} bounced, {v.Unconfirmed} unconfirmed"

let private showReconcile (v: Views.ReconcileView) =
    if v.Arrived then
        $"reminder for {v.Copy} marked arrived"
    else
        $"reminder for {v.Copy} marked missing; it will be sent again"

let private showMembers (members: Views.MemberSummaryView list) =
    match members with
    | [] -> "no members"
    | members ->
        members
        |> List.map (fun m -> $"{m.Member} {m.Name} ({m.Type}), {m.Loans} loans")
        |> lines $"{members.Length} members:"

let private showImport (v: Views.ImportView) = $"imported {v.Imported} members"

/// Runs one command line against the ports and returns the text to show.
let run (ports: Ports) (line: string) : string =
    match tokenize line with
    | Error message -> "error: " + message
    | Ok [] -> "error: empty command"
    | Ok [ "help" ] -> String.concat "\n" usage
    | Ok [ "add-member"; m; kind; name ] -> UseCases.addMember ports m kind name |> render showMember
    | Ok [ "add-book"; b; isbn; title; author ] -> UseCases.addBook ports b isbn title author |> render showBook
    | Ok [ "add-branch"; b; name ] -> UseCases.addBranch ports b name |> render showBranch
    | Ok [ "add-copy"; c; b ] -> UseCases.addCopy ports c b |> render showCopy
    | Ok [ "add-copy"; c; b; branch ] -> UseCases.addCopyAt ports c b branch |> render showCopy
    | Ok [ "transfer"; c; branch ] -> UseCases.transfer ports c branch |> render showTransfer
    | Ok [ "shelf"; branch ] -> UseCases.shelf ports branch |> render showShelf
    | Ok [ "borrow"; m; c ] ->
        // DEC-009: a member who owes 5.00 or more may not borrow.
        let library = ports.Store.Load()
        let fines = library.Fines |> List.filter (fun f -> f.Member = MemberId m) |> List.sumBy (fun f -> f.Amount)
        let paid = library.Payments |> List.filter (fun p -> p.Member = MemberId m) |> List.sumBy (fun p -> p.Amount)

        if fines - paid >= 5.00m then
            Error(BorrowingBlocked(MemberId m)) |> render showBorrow
        else
            UseCases.borrow ports m c |> render showBorrow
    | Ok [ "return"; c ] -> UseCases.returnCopy ports c |> render showReturn
    | Ok [ "renew"; c ] ->
        let library = ports.Store.Load()

        match Loans.renew (ports.Clock()) (CopyId c) library with
        | Ok(next, loan) ->
            ports.Store.Save next
            $"{c} renewed, due {Views.date loan.DueDate}"
        | Error error -> "error: " + Views.describeError error
    | Ok [ "hold"; m; b ] -> UseCases.placeHold ports m b |> render showHold
    | Ok [ "cancel-hold"; m; b ] -> UseCases.cancelHold ports m b |> render showCancelHold
    | Ok [ "holds"; b ] -> UseCases.holds ports b |> render showQueue
    | Ok [ "loans"; m ] -> UseCases.loans ports m |> render showLoans
    | Ok [ "account"; m ] -> UseCases.account ports m |> render showAccount
    | Ok [ "pay"; m; amount ] -> UseCases.pay ports m amount |> render showPayment
    | Ok [ "overdue" ] -> UseCases.overdue ports |> render showOverdue
    | Ok [ "export-overdue"; path ] -> Reports.exportOverdue ports path |> render showExport
    | Ok [ "remind" ] -> UseCases.remind ports |> render showReminders
    | Ok [ "reconcile"; c; answer ] -> UseCases.reconcile ports c answer |> render showReconcile
    | Ok [ "members" ] -> UseCases.members ports |> render showMembers
    | Ok [ "import-members"; path ] -> UseCases.importMembers ports path |> render showImport
    | Ok [ "backup"; path ] ->
        (JsonFileStore.create path).Save(ports.Store.Load())
        $"backed up to {path}"
    | Ok(command :: _) ->
        match usageOf command with
        | Some u -> "usage: " + u
        | None -> $"error: unknown command '{command}' (try help)"
