/// Date helpers for payroll.
module Payroll.Calendar

open System
open Payroll.Domain

let daysBetween (a: DateOnly) (b: DateOnly) = b.DayNumber - a.DayNumber

/// New starters are on probation for their first 90 days.
let isProbationary (asOf: DateOnly) (e: Employee) = daysBetween e.Hired asOf < 90
