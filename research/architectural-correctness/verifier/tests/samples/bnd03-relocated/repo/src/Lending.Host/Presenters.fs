module Lending.Host.Presenters

open Lending.Semantic
open Lending.Application.Views

let loanLine (view: LoanView) = sprintf "%s due %s" view.LoanId view.Due

/// Identifiers are allowed; DueDate (a pattern read) and Renewals (a dot read) are not.
let describe (loan: Loan) =
    let { DueDate = due } = loan
    sprintf "%s %s %d" loan.LoanId (due.ToString "yyyy-MM-dd") loan.Renewals

/// Constructing an entity writes its labels; that is not a read.
let draft (id: string) : Loan =
    { LoanId = id; Book = BookId "b"; Borrower = MemberId "m"; DueDate = System.DateTime.MinValue; Renewals = 0 }

let result (r: Result<LoanView, string>) =
    match r with
    | Ok view -> loanLine view
    | Error message -> "error: " + message
