/// Requisition routing rules. Pure functions only.
module Procurement.Rules

open Procurement.Domain

let approvalLimits =
    { ManagerMax = 7500.00m
      DirectorMax = 40000.00m }

let requiredApprover (r: Requisition) =
    if r.Total <= approvalLimits.ManagerMax then Manager
    elif r.Total <= approvalLimits.DirectorMax then Director
    else Cfo

/// DEC-PR02.
let competitiveBidThreshold = 15000.00m

let bidsAboveThreshold = 3

/// APR-PR01.
let (|ApprovedSoleSource|_|) (r: Requisition) =
    if r.Vendor.Id = "V-3302" && r.Category = "LabReagents" then Some() else None

let (|ContractRenewal|_|) (r: Requisition) = if r.IsRenewal then Some() else None

let bidsRequired (r: Requisition) =
    match r with
    | ApprovedSoleSource -> 1
    | ContractRenewal -> 1
    | _ when r.Total > competitiveBidThreshold -> bidsAboveThreshold
    | _ -> 1
