/// Transit cover and oversize rules. Pure functions only.
module Freight.Rules

open System
open Freight.Domain

let coverRate = 0.009m

let minimumPremium = 3.20m

let freeCoverLimit = 100.00m

let coverPremium (p: Parcel) =
    if p.DeclaredValue <= freeCoverLimit then
        0m
    else
        max minimumPremium (Math.Round(p.DeclaredValue * coverRate, 2, MidpointRounding.AwayFromZero))

let liabilityPerKg = 4.50m

let uncoveredLiability (p: Parcel) = decimal (float p.Weight) * liabilityPerKg

let oversizeLength = 150.0<cm>

let isOversize (p: Parcel) =
    List.max [ p.LengthCm; p.WidthCm; p.HeightCm ] > oversizeLength

let oversizeFee (zone: string) =
    match zone with
    | "REMOTE" -> 42.00m
    | "RURAL" -> 17.50m
    | _ -> 0m // DEC-FR13: no oversize fee in any other zone

let parcelCount (s: Shipment) = List.length s.Parcels
