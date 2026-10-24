/// Renewal billing rules. Pure functions only.
module Subscriptions.Rules

open System
open Subscriptions.Domain

let monthlyPrice (plan: string) =
    Plans.catalogue
    |> Map.tryFind plan
    |> Option.map (fun p -> p.Monthly)
    |> Option.defaultValue Plans.starter.Monthly

let renewalCharge (s: Subscription) = monthlyPrice s.Plan * decimal s.Seats

/// DEC-SB02: a year costs ten months.
let annualMonths = 10m

let annualPrice (plan: string) = monthlyPrice plan * annualMonths

let paymentGrace = TimeSpan.FromDays 7.0

let suspendAt (failed: PaymentAttempt) = failed.At + paymentGrace

let isSuspended (now: DateTime) (attempts: PaymentAttempt list) =
    match attempts |> List.sortByDescending (fun a -> a.At) with
    | latest :: _ when not latest.Succeeded -> now >= suspendAt latest
    | _ -> false
