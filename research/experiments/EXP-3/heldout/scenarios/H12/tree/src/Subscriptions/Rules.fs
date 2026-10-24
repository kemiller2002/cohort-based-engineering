/// Cancellation and seat rules. Pure functions only.
module Subscriptions.Rules

open System
open Subscriptions.Domain

let refundWindowDays = 28

let withinRefundWindow (today: DateOnly) (s: Subscription) =
    today <= s.FirstCharged.AddDays refundWindowDays

/// APR-SB01.
let refundException = ("cu-4410", DateOnly(2026, 12, 31))

let refundOnCancel (today: DateOnly) (s: Subscription) =
    match s with
    | _ when s.Customer.Id = fst refundException && today <= snd refundException -> s.LastCharge
    | { Plan = "SCALE"; Seats = seats } when seats >= 150 -> s.LastCharge
    | _ when withinRefundWindow today s -> s.LastCharge
    | _ -> 0m

let seatLimits = Map.ofList [ "STARTER", 3; "TEAM", 25; "SCALE", 200 ]

let seatLimit (plan: string) =
    defaultArg (Map.tryFind plan seatLimits) Int32.MaxValue

let canAddSeats (n: int) (s: Subscription) = s.Seats + n <= seatLimit s.Plan
