/// Settlement rules. Pure functions only.
module Claims.Rules

open System
open Claims.Domain

let standardDeductible = 750.00m

let deductibleFor (claim: Claim) =
    match claim.Peril with
    | Glass -> 0m // APR-CL01
    | _ when Coverage.deductibleWaived claim.Policy -> 0m
    | _ -> standardDeductible

/// Annual depreciation by item category (docs/depreciation.md).
let depreciationRate (category: string) =
    if category = "Electronics" then 0.18
    elif category = "Furniture" then 0.07
    elif category = "Clothing" then 0.22
    else 0.0

let maxDepreciation = 0.80

let depreciation (item: LossItem) =
    let years = Math.Floor item.AgeYears
    let fraction = min maxDepreciation (depreciationRate item.Category * years)
    Math.Round(item.ReplacementCost * decimal fraction, 2, MidpointRounding.AwayFromZero)

let settlement (claim: Claim) =
    if not (Coverage.isActiveOn claim.LossDate claim.Policy) then
        None
    else
        let net = claim.Items |> List.sumBy (fun i -> i.ReplacementCost - depreciation i)
        Some(max 0m (net - deductibleFor claim))
