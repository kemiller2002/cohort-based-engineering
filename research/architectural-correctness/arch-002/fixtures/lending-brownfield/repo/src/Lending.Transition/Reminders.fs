/// DEC-008: overdue reminders, one per loan and due date.
module Lending.Transition.Reminders

open System
open Lending.Semantic

/// A reminder already settles a loan's due date when it was sent or its fate is not known.
let private settles (loan: Loan) (reminder: Reminder) =
    reminder.Copy = loan.Copy
    && reminder.DueDate = loan.DueDate
    && (match reminder.Outcome with
        | Sent
        | Unconfirmed -> true
        | Bounced _ -> false)

/// The overdue loans that need a reminder today, with the notice to send for each.
let due (today: DateOnly) (library: Library) : (Loan * Notice) list =
    Loans.overdue today library
    |> List.filter (fun loan -> not (library.Reminders |> List.exists (settles loan)))
    |> List.map (fun loan ->
        let title =
            library.Copies
            |> Map.tryFind loan.Copy
            |> Option.bind (fun copy -> library.Books |> Map.tryFind copy.Book)
            |> Option.map (fun book -> book.Title)
            |> Option.defaultValue (CopyId.value loan.Copy)

        let due = loan.DueDate.ToString("yyyy-MM-dd", Globalization.CultureInfo.InvariantCulture)

        loan,
        { Recipient = loan.Member
          Subject = "Overdue: " + title
          Body = $"Please return {CopyId.value loan.Copy} ({title}); it was due on {due}." })

/// Interprets what the host observed when it tried to deliver a reminder.
let outcomeOf (report: DeliveryReport) =
    match report with
    | Delivered -> Sent
    | Rejected reason -> Bounced reason
    | NoAnswer -> Unconfirmed

let record (loan: Loan) (attemptedAt: DateTime) (report: DeliveryReport) (library: Library) =
    let reminder =
        { Copy = loan.Copy
          Member = loan.Member
          DueDate = loan.DueDate
          AttemptedAt = attemptedAt
          Outcome = outcomeOf report }

    { library with Reminders = library.Reminders @ [ reminder ] }

/// DEC-008: staff record whether an unconfirmed reminder arrived. One that did not is sent again on the next run.
let reconcile copyId (arrived: bool) (library: Library) : Result<Library, LendingError> =
    let isOpen (reminder: Reminder) =
        reminder.Copy = copyId && reminder.Outcome = Unconfirmed

    match library.Reminders |> List.tryFindIndexBack isOpen with
    | None -> Error(InvalidInput $"no unconfirmed reminder for {CopyId.value copyId}")
    | Some index ->
        let settled =
            library.Reminders
            |> List.mapi (fun i reminder ->
                if i = index then
                    { reminder with Outcome = (if arrived then Sent else Bounced "not received") }
                else
                    reminder)

        Ok { library with Reminders = settled }
