module Lending.Application.Views

open Lending.Semantic

type LoanView = { LoanId: string; Due: string; CanRenew: bool }

let ofLoan (canRenew: bool) (loan: Loan) : LoanView =
    { LoanId = loan.LoanId; Due = loan.DueDate.ToString "yyyy-MM-dd"; CanRenew = canRenew }
