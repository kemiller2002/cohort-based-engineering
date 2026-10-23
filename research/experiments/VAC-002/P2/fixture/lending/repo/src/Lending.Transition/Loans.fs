/// Borrowing, returning and renewing copies.
module Lending.Transition.Loans

open System
open Lending.Semantic

/// The outcome of a return.
type Returned =
    { Loan: Loan
      DaysLate: int
      Fine: Fine option }

let loansOf memberId (library: Library) =
    library.Loans
    |> Map.toList
    |> List.map snd
    |> List.filter (fun loan -> loan.Member = memberId)
    |> List.sortBy (fun loan -> loan.DueDate, CopyId.value loan.Copy)

/// DEC-001, DEC-002, DEC-005.
let borrow (today: DateOnly) memberId copyId (library: Library) : Result<Library * Loan, LendingError> =
    result {
        let! borrower = Catalog.findMember memberId library
        do! Members.ensureActive borrower.Id library
        let! copy = Catalog.findCopy copyId library
        do! ensure (not (library.Loans.ContainsKey copyId)) (CopyAlreadyOnLoan copyId)
        let limit = Policy.maxLoans borrower.Type
        do! ensure (List.length (loansOf memberId library) < limit) (LoanLimitReached(memberId, limit))

        do!
            match Holds.queueFor copy.Book library with
            | head :: _ when head.Member <> memberId -> Error(ReservedForAnotherMember copyId)
            | _ -> Ok()

        let loan =
            { Copy = copyId
              Member = memberId
              BorrowedOn = today
              DueDate = today.AddDays Policy.loanPeriodDays
              Renewals = 0 }

        let library = Holds.release memberId copy.Book library
        return { library with Loans = library.Loans.Add(copyId, loan) }, loan
    }

/// DEC-003: a late return is fined.
let returnCopy (today: DateOnly) copyId (library: Library) : Result<Library * Returned, LendingError> =
    result {
        let! _ = Catalog.findCopy copyId library
        let! loan = library.Loans |> Map.tryFind copyId |> required (CopyNotOnLoan copyId)
        let fine = Fines.assess today loan

        let returned =
            { Loan = loan
              DaysLate = Fines.daysLate loan.DueDate today
              Fine = fine }

        return
            { library with
                Loans = library.Loans.Remove copyId
                Fines = library.Fines @ Option.toList fine },
            returned
    }

/// DEC-004: renewal extends the due date by one loan period.
let renew (today: DateOnly) copyId (library: Library) : Result<Library * Loan, LendingError> =
    result {
        let! copy = Catalog.findCopy copyId library
        let! loan = library.Loans |> Map.tryFind copyId |> required (CopyNotOnLoan copyId)
        do! Members.ensureActive loan.Member library
        do! ensure (today <= loan.DueDate) (LoanOverdue copyId)
        do! ensure (loan.Renewals < Policy.renewLimit) (RenewLimitReached(copyId, Policy.renewLimit))
        do! ensure (List.isEmpty (Holds.queueFor copy.Book library)) (HoldsWaiting copyId)

        let renewed =
            { loan with
                DueDate = loan.DueDate.AddDays Policy.loanPeriodDays
                Renewals = loan.Renewals + 1 }

        return { library with Loans = library.Loans.Add(copyId, renewed) }, renewed
    }

/// LEND-L02: loans past their due date today, most overdue first, then by copy id; days late as DEC-003 counts them.
let overdue (today: DateOnly) (library: Library) : (Loan * int) list =
    library.Loans
    |> Map.toList
    |> List.map snd
    |> List.map (fun loan -> loan, Fines.daysLate loan.DueDate today)
    |> List.filter (fun (_, days) -> days > 0)
    |> List.sortBy (fun (loan, days) -> -days, CopyId.value loan.Copy)
