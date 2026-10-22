/// The application's use cases: translate input, let Tier 2 decide, persist, project a view.
module Lending.Application.UseCases

open System
open Lending.Semantic
open Lending.Transition

/// Loads the state, applies a decision for today and saves the new state when it succeeds.
let private commit (ports: Ports) (decide: DateOnly -> Library -> Result<Library * 'a, LendingError>) =
    let library = ports.Store.Load()

    match decide (ports.Clock()) library with
    | Ok(next, value) ->
        ports.Store.Save next
        Ok value
    | Error error -> Error error

let private query (ports: Ports) (project: Library -> Result<'a, LendingError>) = project (ports.Store.Load())

let parseMemberType (text: string) =
    match text.Trim().ToLowerInvariant() with
    | "standard" -> Ok Standard
    | "student" -> Ok Student
    | "staff" -> Ok Staff
    | other -> Error(InvalidInput $"unknown member type '{other}' (standard, student or staff)")

let private newMember (memberId: string) (memberType: string) (name: string) =
    parseMemberType memberType
    |> Result.map (fun memberType ->
        { Id = MemberId memberId
          Name = name
          Type = memberType })

let addMember ports (memberId: string) (memberType: string) (name: string) : Result<Views.MemberView, LendingError> =
    newMember memberId memberType name
    |> Result.bind (fun newMember ->
        commit ports (fun _ library -> Catalog.addMember newMember library |> Result.map (fun l -> l, Views.ofMember newMember)))

let addBook ports (bookId: string) (isbn: string) (title: string) (author: string) : Result<Views.BookView, LendingError> =
    let book =
        { Id = BookId bookId
          Title = title
          Author = author
          Isbn = isbn }

    commit ports (fun _ library -> Catalog.addBook book library |> Result.map (fun l -> l, Views.ofBook book))

let addBranch ports (branchId: string) (name: string) : Result<Views.BranchView, LendingError> =
    let branch = { Id = BranchId branchId; Name = name }
    commit ports (fun _ library -> Catalog.addBranch branch library |> Result.map (fun l -> l, Views.ofBranch branch))

let addCopyAt ports (copyId: string) (bookId: string) (branchId: string) : Result<Views.CopyView, LendingError> =
    let copy =
        { Id = CopyId copyId
          Book = BookId bookId
          Branch = BranchId branchId }

    commit ports (fun _ library -> Catalog.addCopy copy library |> Result.map (fun l -> l, Views.ofCopy copy))

let addCopy ports (copyId: string) (bookId: string) : Result<Views.CopyView, LendingError> =
    addCopyAt ports copyId bookId (BranchId.value Policy.mainBranch)

let transfer ports (copyId: string) (branchId: string) : Result<Views.TransferView, LendingError> =
    commit ports (fun _ library ->
        Catalog.transfer (CopyId copyId) (BranchId branchId) library
        |> Result.map (fun (l, copy) -> l, Views.ofTransfer l copy))

let shelf ports (branchId: string) : Result<Views.ShelfView, LendingError> =
    query ports (Views.shelf (BranchId branchId))

let borrow ports (memberId: string) (copyId: string) : Result<Views.BorrowView, LendingError> =
    commit ports (fun today library ->
        Loans.borrow today (MemberId memberId) (CopyId copyId) library
        |> Result.map (fun (l, loan) -> l, Views.ofBorrow loan))

let returnCopy ports (copyId: string) : Result<Views.ReturnView, LendingError> =
    commit ports (fun today library ->
        Loans.returnCopy today (CopyId copyId) library
        |> Result.map (fun (l, returned) -> l, Views.ofReturn returned))

let placeHold ports (memberId: string) (bookId: string) : Result<Views.HoldView, LendingError> =
    commit ports (fun today library ->
        Holds.place today (MemberId memberId) (BookId bookId) library
        |> Result.map (fun (l, position) ->
            l,
            { Views.HoldView.Member = memberId
              Book = bookId
              Position = position }))

let cancelHold ports (memberId: string) (bookId: string) : Result<Views.CancelHoldView, LendingError> =
    commit ports (fun _ library ->
        Holds.cancel (MemberId memberId) (BookId bookId) library
        |> Result.map (fun l -> l, { Views.CancelHoldView.Member = memberId; Book = bookId }))

let holds ports (bookId: string) : Result<Views.HoldQueueView, LendingError> =
    query ports (Views.holdQueue (BookId bookId))

let loans ports (memberId: string) : Result<Views.MemberLoansView, LendingError> =
    query ports (Views.memberLoans (MemberId memberId))

let account ports (memberId: string) : Result<Views.AccountView, LendingError> =
    query ports (Views.account (MemberId memberId))

let pay ports (memberId: string) (amount: string) : Result<Views.PaymentView, LendingError> =
    Payments.parseAmount amount
    |> Result.bind (fun amount ->
        commit ports (fun _ library ->
            Payments.pay (MemberId memberId) amount library
            |> Result.map (fun (l, payment) -> l, Views.ofPayment l payment)))

let overdue ports : Result<Views.OverdueView, LendingError> =
    let today = ports.Clock()
    query ports (Views.overdue today >> Ok)

/// DEC-008: sends the reminders that are due and records what became of each.
let remind (ports: Ports) : Result<Views.ReminderRunView, LendingError> =
    let library = ports.Store.Load()

    let attempts =
        Reminders.due (ports.Clock()) library
        |> List.map (fun (loan, notice) ->
            let report =
                try
                    ports.Notifier.Send notice |> Async.RunSynchronously
                with _ ->
                    Rejected "the notice channel failed"

            loan, DateTime.UtcNow, report)

    let next =
        attempts
        |> List.fold (fun library (loan, attemptedAt, report) -> Reminders.record loan attemptedAt report library) library

    ports.Store.Save next
    Ok(Views.ofReminderRun (attempts |> List.map (fun (_, _, report) -> Reminders.outcomeOf report)))

/// DEC-008: a member of staff records whether an unconfirmed reminder arrived.
let reconcile ports (copyId: string) (answer: string) : Result<Views.ReconcileView, LendingError> =
    match answer with
    | "arrived"
    | "missing" ->
        let arrived = (answer = "arrived")

        commit ports (fun _ library ->
            Reminders.reconcile (CopyId copyId) arrived library
            |> Result.map (fun l -> l, { Views.ReconcileView.Copy = copyId; Arrived = arrived }))
    | other -> Error(InvalidInput $"answer arrived or missing, not '{other}'")

let members ports : Result<Views.MemberSummaryView list, LendingError> = query ports (Views.members >> Ok)

/// Adds the members listed in a CSV file (`member,type,name` after a header line), stopping at the first bad line.
let importMembers (ports: Ports) (path: string) : Result<Views.ImportView, LendingError> =
    match ports.Files.ReadLines path with
    | None -> Error(InvalidInput $"cannot read {path}")
    | Some lines ->
        let rows = lines |> List.skip (min 1 lines.Length) |> List.filter (fun line -> line.Trim() <> "")

        let addRow (state: Result<Library, LendingError>) (number: int, line: string) =
            state
            |> Result.bind (fun library ->
                match line.Split(',') |> Array.map (fun field -> field.Trim()) |> List.ofArray with
                | [ memberId; memberType; name ] ->
                    newMember memberId memberType name |> Result.bind (fun m -> Catalog.addMember m library)
                | _ -> Error(InvalidInput "expected member,type,name")
                |> Result.mapError (fun error -> InvalidInput $"line {number + 2}: {Views.describeError error}"))

        commit ports (fun _ library ->
            rows
            |> List.indexed
            |> List.fold addRow (Ok library)
            |> Result.map (fun l -> l, { Views.ImportView.Imported = rows.Length }))
