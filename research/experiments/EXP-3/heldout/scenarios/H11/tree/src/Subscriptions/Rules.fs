/// Trial, retry and proration rules. Pure functions only.
module Subscriptions.Rules

open System
open Subscriptions.Domain

/// DEC-SB03.
let trialLength = TimeSpan.FromDays 14.0

let isPartnerDomain (email: string) =
    email.EndsWith("@partners.example.com", StringComparison.OrdinalIgnoreCase)

let trialEligible (previousTrials: Set<string>) (c: Customer) =
    isPartnerDomain c.Email || not (previousTrials.Contains(c.Email.ToLowerInvariant()))

let trialEnds (start: DateTime) = start + trialLength

let retryOffsetsDays = [ 1; 3; 5 ]

let retrySchedule (failedAt: DateTime) =
    retryOffsetsDays |> List.map (fun d -> failedAt.AddDays(float d))

let prorate (fromMonthly: decimal) (toMonthly: decimal) (today: DateOnly) (s: Subscription) =
    let daysInCycle = decimal (s.CycleEnd.DayNumber - s.CycleStart.DayNumber)
    let daysLeft = decimal (s.CycleEnd.DayNumber - today.DayNumber)
    if toMonthly <= fromMonthly then
        0m
    else
        Math.Round((toMonthly - fromMonthly) * daysLeft / daysInCycle, 2, MidpointRounding.AwayFromZero)
