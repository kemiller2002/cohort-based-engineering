/// Claims domain types. Data only; the rules live in Rules.fs.
module Claims.Domain

open System

type Peril =
    | Fire
    | Water
    | Theft
    | Wind
    | Glass
    | Liability

type Policy =
    { Number: string
      Product: string
      Holder: string
      Inception: DateOnly
      Expiry: DateOnly }

type LossItem =
    { Description: string
      Category: string
      ReplacementCost: decimal
      AgeYears: float }

type Claim =
    { Id: string
      Policy: Policy
      Peril: Peril
      LossDate: DateOnly
      ReportedOn: DateOnly
      ReportedAt: DateTime
      Reported: decimal
      EventCode: string option
      Items: LossItem list }

type VehicleClaim =
    { Claim: Claim
      MarketValue: decimal
      RepairEstimate: decimal
      VehicleAgeYears: int
      RentalCover: bool }

type Routing =
    | FastTrack
    | Adjuster
