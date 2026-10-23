/// DEC-003 and DEC-006: fines are assessed here, and only here.
module Lending.Transition.Fines

open System
open Lending.Semantic

let daysLate (dueDate: DateOnly) (returnedOn: DateOnly) = max 0 (returnedOn.DayNumber - dueDate.DayNumber)

let fineFor (dueDate: DateOnly) (returnedOn: DateOnly) =
    min Policy.fineCap (decimal (daysLate dueDate returnedOn) * Policy.finePerDay)

/// The fine for a loan returned on the given day, if it is late.
let assess (returnedOn: DateOnly) (loan: Loan) : Fine option =
    let amount = fineFor loan.DueDate returnedOn

    if amount > 0m then
        Some
            { Member = loan.Member
              Copy = loan.Copy
              Amount = amount
              AssessedOn = returnedOn }
    else
        None

let outstanding memberId (library: Library) =
    library.Fines |> List.filter (fun fine -> fine.Member = memberId) |> List.sumBy (fun fine -> fine.Amount)
