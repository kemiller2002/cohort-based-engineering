module Lending.Transition.Loans

open System
open Lending.Semantic

/// Decides whether a loan may be renewed. The clock arrives as an argument.
let renew (now: DateTime) (loan: Loan) : Result<Loan, string> =
    if loan.Renewals >= Policy.maxRenewals then Error "renewal limit reached"
    elif now > loan.DueDate then Error "loan is overdue"
    else Ok { loan with DueDate = loan.DueDate.AddDays 14.0; Renewals = loan.Renewals + 1 }

type Interpretation =
    | Done
    | Rejected of string
    | Reconcile of string

let interpret (outcome: Outcome) : Interpretation =
    match outcome with
    | Succeeded -> Done
    | Failed reason -> Rejected reason
    | Unknown reason -> Reconcile reason

// DEC-T1-RENEWAL-LIMIT: a loan may be renewed at most Policy.maxRenewals times.
let canRenew (loan: Loan) = loan.Renewals < Policy.maxRenewals
