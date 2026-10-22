/// DEC-009 and DEC-010: what a member owes, and when that blocks them.
module Lending.Transition.Accounts

open Lending.Semantic

let finesOf memberId (library: Library) =
    library.Fines |> List.filter (fun fine -> fine.Member = memberId)

let paymentsOf memberId (library: Library) =
    library.Payments |> List.filter (fun payment -> payment.Member = memberId)

/// What the member owes: every fine assessed, less every payment made.
let owed memberId (library: Library) =
    let fines = finesOf memberId library |> List.sumBy (fun fine -> fine.Amount)
    let paid = paymentsOf memberId library |> List.sumBy (fun payment -> payment.Amount)
    max 0m (fines - paid)

/// DEC-009: owing the blocking balance or more blocks borrowing, holds and renewals.
let isBlocked memberId (library: Library) = owed memberId library >= Policy.blockingBalance
