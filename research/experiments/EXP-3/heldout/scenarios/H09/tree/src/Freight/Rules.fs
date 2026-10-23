/// Promise and invoicing rules. Pure functions only.
module Freight.Rules

open System
open Freight.Domain

let transitDays (service: string) =
    if service = "EXPRESS" then 1
    elif service = "PRIORITY" then 2
    elif service = "STANDARD" then 4
    else 8

let promisedDelivery (s: Shipment) = s.ShipDate.AddDays(transitDays s.Service)

/// DEC-FR07.
let fuelSurchargeRate = 0.085m

let fuelSurcharge (s: Shipment) =
    if s.Account.IsKeyAccount then
        0m
    else
        Math.Round(s.BaseCharge * fuelSurchargeRate, 2, MidpointRounding.AwayFromZero)

let invoiceTotal (s: Shipment) = s.BaseCharge + fuelSurcharge s
