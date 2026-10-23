/// Claim intake rules. Pure functions only.
module Claims.Rules

open System
open Claims.Domain

/// Money is held to the cent, half away from zero.
let roundCents (amount: decimal) =
    Math.Round(amount, 2, MidpointRounding.AwayFromZero)

/// DEC-CL01.
let standardDeductible = 750.00m

let payable (claim: Claim) =
    max 0m (claim.Reported - standardDeductible) |> roundCents

/// Ceiling for claims settled on documents alone.
let fastTrackCeiling = 2500.00m

let route (claim: Claim) =
    if claim.Reported <= fastTrackCeiling then FastTrack else Adjuster

let private reserveTable =
    Map.ofList [ Fire, 15000.00m; Water, 6500.00m; Theft, 4200.00m; Wind, 8800.00m ]

/// Opening reserve for a new claim (docs/initial-reserves.md).
let initialReserve (claim: Claim) =
    reserveTable |> Map.tryFind claim.Peril |> Option.defaultValue 2000.00m

let totalReserved (claims: Claim list) = claims |> List.sumBy initialReserve
