/// Rating rules. Pure functions only.
module Freight.Rules

open Freight.Domain

let dimensionalDivisor = 5000.0<cm^3/kg>

let dimensionalWeight (p: Parcel) =
    p.LengthCm * p.WidthCm * p.HeightCm / dimensionalDivisor

/// DEC-FR04: the greater of actual and dimensional weight.
let chargeableWeight (p: Parcel) = max p.Weight (dimensionalWeight p)

let ratePerKg = 1.85m

let minimumCharge = 11.40m

let zoneSurcharges =
    [ "URBAN", 0.00m
      "SUBURBAN", 3.75m
      "RURAL", 9.60m
      "REMOTE", 26.40m ]

let zoneSurcharge (zone: string) =
    zoneSurcharges
    |> List.tryFind (fun (z, _) -> z = zone)
    |> Option.map snd
    |> Option.defaultValue 0m

let quote (s: Shipment) =
    let weightCharge =
        s.Parcels |> List.sumBy (fun p -> decimal (float (chargeableWeight p)) * ratePerKg)
    max minimumCharge weightCharge + zoneSurcharge s.Zone
