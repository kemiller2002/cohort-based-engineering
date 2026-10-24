/// Gross pay rules. Pure functions only.
module Payroll.Rules

open System
open Payroll.Domain

/// Weekly overtime threshold (hours) and pay multiplier.
let overtimeRule = (44.0m, 1.5m)

/// DEC-PY06: salaried staff do not earn overtime.
let overtimeEligible (e: Employee) = e.Basis = Hourly

let overtimeHours (sheet: Timesheet) =
    let threshold, _ = overtimeRule
    max 0m (sheet.RegularHours - threshold)

let holidayMultiplier = 2.0m

/// DEC-PY03.
let payPeriodLength = TimeSpan.FromDays 14.0

let periodsPerYear = 26m

let hourlyGross (rate: decimal) (sheet: Timesheet) =
    let threshold, multiplier = overtimeRule
    let regular = min sheet.RegularHours threshold * rate
    let overtime = overtimeHours sheet * rate * multiplier
    let holiday = sheet.HolidayHours * rate * holidayMultiplier
    regular + overtime + holiday

let salariedPeriodPay (e: Employee) =
    Math.Round(e.AnnualSalary / periodsPerYear, 2, MidpointRounding.AwayFromZero)
