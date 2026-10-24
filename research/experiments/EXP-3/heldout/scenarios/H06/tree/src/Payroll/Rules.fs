/// Expense reimbursement rules. Pure functions only.
module Payroll.Rules

open System
open Payroll.Domain

let expensePolicy =
    { RatePerKm = 0.58
      DailyMealCap = 55.00m }

let mileageAmount (claim: ExpenseClaim) =
    Math.Round(decimal (claim.Kilometres * expensePolicy.RatePerKm), 2, MidpointRounding.AwayFromZero)

let mealAmount (claim: ExpenseClaim) =
    min claim.Amount (expensePolicy.DailyMealCap * decimal claim.Days)

let reimbursable (claim: ExpenseClaim) =
    match claim.Kind with
    | "Mileage" -> mileageAmount claim
    | "Meals" -> mealAmount claim
    | _ -> claim.Amount

let payableClaims (claims: ExpenseClaim list) =
    claims
    |> List.filter (fun c -> c.Amount > 0m || c.Kind = "Mileage")
    |> List.filter (fun c -> c.Kind = "Mileage" || c.HasReceipt || c.Submitter.Grade >= 8)

let batchTotal (claims: ExpenseClaim list) =
    claims |> payableClaims |> List.sumBy reimbursable
