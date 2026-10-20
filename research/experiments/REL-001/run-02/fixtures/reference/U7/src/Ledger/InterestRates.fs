/// Interest rate schedules (LEDGER-U7-R1, R2).
module Ledger.InterestRates

open System

let private validate (tiers: Tier list) : string option =
    let bounded, last = match List.rev tiers with | l :: rest -> List.rev rest, Some l | [] -> [], None
    let limits = bounded |> List.choose (fun t -> t.UpTo)
    if List.isEmpty tiers then Some "a schedule needs at least one tier"
    elif tiers |> List.exists (fun t -> t.Rate < 0m || t.Rate > 1m) then Some "rates must be between 0 and 1"
    elif last |> Option.exists (fun t -> t.UpTo.IsSome) then Some "the last tier must have no upper limit"
    elif limits.Length <> bounded.Length then Some "only the last tier may be unlimited"
    elif limits |> List.exists (fun l -> l <= 0m) then Some "tier limits must be positive"
    elif limits |> List.pairwise |> List.exists (fun (x, y) -> y <= x) then Some "tier limits must strictly increase"
    else None

let create (tiers: Tier list) : Result<RateSchedule, LedgerError> =
    match validate tiers with
    | Some reason -> Error(InvalidRateSchedule reason)
    | None -> Ok { Tiers = tiers }

/// Marginal interest (docs/design/interest.md): each slice earns its own tier's rate.
let interestFor (schedule: RateSchedule) (balance: decimal) : decimal =
    let slice (floor: decimal, total: decimal) (t: Tier) =
        let ceiling = t.UpTo |> Option.defaultValue Decimal.MaxValue
        let portion = max 0m (min balance ceiling - floor)
        ceiling, total + portion * t.Rate
    if balance <= 0m then 0m
    else
        let _, total = schedule.Tiers |> List.fold slice (0m, 0m)
        Math.Round(total, 2, MidpointRounding.ToEven)
