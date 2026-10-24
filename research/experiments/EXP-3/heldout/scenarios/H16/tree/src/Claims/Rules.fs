/// Motor total-loss rules. Pure functions only.
module Claims.Rules

open System
open Claims.Domain

/// DEC-CL16 (replaces DEC-CL14's 75%).
let totalLossRatio = 0.68m

let isTotalLoss (v: VehicleClaim) =
    v.RepairEstimate >= v.MarketValue * totalLossRatio

let salvageRate (v: VehicleClaim) =
    if v.VehicleAgeYears <= 10 then 0.12m else 0.04m

let totalLossSettlement (v: VehicleClaim) =
    let salvage = Math.Round(v.MarketValue * salvageRate v, 2, MidpointRounding.AwayFromZero)
    v.MarketValue - salvage

let settlementFor (v: VehicleClaim) =
    if isTotalLoss v then totalLossSettlement v else v.RepairEstimate

let rentalDailyCap = 45.00m

let rentalMaxDays = 28

let rentalAllowance (v: VehicleClaim) (days: int) (dailyCost: decimal) =
    if not v.RentalCover then
        0m
    else
        decimal (min days rentalMaxDays) * min dailyCost rentalDailyCap
