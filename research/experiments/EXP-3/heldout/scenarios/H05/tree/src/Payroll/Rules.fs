/// Payslip deduction rules. Pure functions only.
module Payroll.Rules

open System
open Payroll.Domain

let private cents (x: decimal) =
    Math.Round(x, 2, MidpointRounding.AwayFromZero)

/// Dues rate by union local.
let duesRate =
    function
    | "L114" -> 0.013m
    | "L262" -> 0.0165m
    | "L309" -> 0.009m
    | _ -> 0m

let unionDues (e: Employee) (gross: decimal) =
    match e.UnionLocal with
    | Some local -> cents (gross * duesRate local)
    | None -> 0m

/// DEC-PY05.
let pensionRate = 0.045m

let pensionContribution (asOf: DateOnly) (e: Employee) (gross: decimal) =
    if Calendar.isProbationary asOf e then 0m else cents (gross * pensionRate)

let vacationAccrualRate = 0.06m

let vacationAccrued (e: Employee) (hoursPaid: decimal) =
    if e.OnUnpaidLeave then 0m else hoursPaid * vacationAccrualRate
