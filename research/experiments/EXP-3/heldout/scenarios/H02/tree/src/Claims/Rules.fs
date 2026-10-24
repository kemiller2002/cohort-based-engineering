/// Referral and acknowledgement rules. Pure functions only.
module Claims.Rules

open System
open Claims.Domain

/// DEC-CL04: referral threshold and review time.
let siuThreshold = 12000.00m

let siuReviewDays = 6

/// Claims raised under a declared catastrophe event code.
let (|CatastropheEvent|_|) (claim: Claim) =
    match claim.EventCode with
    | Some code when code.StartsWith("CAT-", StringComparison.Ordinal) -> Some code
    | _ -> None

let referToSiu (claim: Claim) =
    match claim with
    | CatastropheEvent _ -> false
    | _ -> claim.Reported > siuThreshold

let siuReviewDue (referredOn: DateOnly) = referredOn.AddDays siuReviewDays

/// Customer Care acknowledgement target.
let acknowledgeWithin = TimeSpan.FromHours 36.0

let acknowledgementDeadline (claim: Claim) = claim.ReportedAt + acknowledgeWithin

let acknowledgementOverdue (now: DateTime) (claim: Claim) = now > acknowledgementDeadline claim

/// DEC-CL08.
[<Literal>]
let ReportingWindowDays = 45

let isLateReport (claim: Claim) =
    claim.ReportedOn > claim.LossDate.AddDays ReportingWindowDays

let referralList (claims: Claim list) =
    claims |> List.filter referToSiu |> List.sortBy (fun c -> c.ReportedOn)
