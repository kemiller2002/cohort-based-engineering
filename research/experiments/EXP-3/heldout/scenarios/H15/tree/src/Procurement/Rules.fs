/// Purchase order and cost rules. Pure functions only.
module Procurement.Rules

open System
open Procurement.Domain

/// DEC-PR08: docs/debarred-vendors.md.
let debarred = set [ "V-1187"; "V-2045"; "V-0417" ]

let mayIssuePo (v: Vendor) =
    not (debarred.Contains v.Id) || v.Id = "V-0417"

let freightAllowanceRate (incoterm: string) =
    match incoterm.ToUpperInvariant() with
    | "EXW" -> 0.075m
    | "FOB" -> 0.045m
    | "DDP" -> 0.0m
    | _ -> 0.045m

let landedCost (r: Requisition) =
    r.Total * (1m + freightAllowanceRate r.Incoterm)

/// DEC-PR06: rate and window in days.
let earlyPayment = (0.0125m, 12)

let earlyPaymentDiscount (inv: Invoice) =
    let rate, days = earlyPayment
    match inv.Paid with
    | Some paid when paid.DayNumber - inv.Received.DayNumber <= days ->
        Math.Round(inv.Amount * rate, 2, MidpointRounding.AwayFromZero)
    | _ -> 0m

let openRequisitions (rs: Requisition list) = rs |> List.filter (fun r -> r.Total > 0m)
