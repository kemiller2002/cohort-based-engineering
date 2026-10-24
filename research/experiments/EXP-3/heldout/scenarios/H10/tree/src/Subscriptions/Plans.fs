/// The plan catalogue (docs/plan-prices.md).
module Subscriptions.Plans

open Subscriptions.Domain

let starter = { Code = "STARTER"; Monthly = 8.00m }

let team = { Code = "TEAM"; Monthly = 19.00m }

let scale = { Code = "SCALE"; Monthly = 42.00m }

let catalogue =
    [ starter; team; scale ] |> List.map (fun p -> p.Code, p) |> Map.ofList
