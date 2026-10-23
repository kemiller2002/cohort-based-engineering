/// The lending policy decided in docs/decisions.
module Lending.Transition.Policy

open Lending.Semantic

/// DEC-001: a loan lasts 21 days from the day the copy is borrowed.
let loanPeriodDays = 21

/// DEC-002: how many copies a member may have on loan at once.
let maxLoans memberType =
    match memberType with
    | Standard -> 5
    | Student -> 3
    | Staff -> 10

/// DEC-003: 0.25 per day late, at most 10.00 for one loan.
let finePerDay = 0.25m

let fineCap = 10.00m

/// DEC-004: a loan may be renewed at most twice.
let renewLimit = 2
