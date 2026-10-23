/// Freight domain types. Data only; the rules live in Rules.fs.
module Freight.Domain

open System

[<Measure>]
type kg

[<Measure>]
type cm

type Parcel =
    { Id: string
      Weight: float<kg>
      LengthCm: float<cm>
      WidthCm: float<cm>
      HeightCm: float<cm>
      DeclaredValue: decimal
      UnNumber: string option
      ColdChain: bool }

type Account =
    { Code: string
      Name: string
      IsKeyAccount: bool }

type Shipment =
    { Id: string
      Account: Account
      Parcels: Parcel list
      Zone: string
      Service: string
      ShipDate: DateOnly
      BaseCharge: decimal }

type DeliveryAttempt =
    { ShipmentId: string
      At: DateTime
      Delivered: bool }

type NextStep =
    | Reattempt of attempt: int
    | ReturnToDepot of holdUntil: DateTime
