/// Manifest rules. Pure functions only.
module Freight.Rules

open System
open Freight.Domain

let (|DangerousGoods|ColdChain|General|) (p: Parcel) =
    match p.UnNumber with
    | Some _ -> DangerousGoods
    | None when p.ColdChain -> ColdChain
    | None -> General

let signatureThreshold = 400.00m

let needsSignature (p: Parcel) =
    match p with
    | DangerousGoods -> true
    | ColdChain -> false
    | General -> p.DeclaredValue > signatureThreshold

let maxDeliveryAttempts = 3

let depotHold = TimeSpan.FromDays 9.0

let afterFailedAttempt (attempts: DeliveryAttempt list) =
    let failed = attempts |> List.filter (fun a -> not a.Delivered)
    if failed.Length < maxDeliveryAttempts then
        Reattempt(failed.Length + 1)
    else
        ReturnToDepot((failed |> List.map (fun a -> a.At) |> List.max) + depotHold)
