module Lending.Application.Views

open Lending.Semantic

type LoanView = { LoanId: string; Due: string; CanRenew: bool }

let ofLoan (canRenew: bool) (loan: Loan) : LoanView =
    { LoanId = loan.LoanId; Due = loan.DueDate.ToString "yyyy-MM-dd"; CanRenew = canRenew }

/// Restates the loan period instead of asking the Semantic tier.
let dueLabel (renewals: int) = if renewals >= 3 then "final" else sprintf "%d days" 21
