module Lending.Transition.Loans

open Lending.Semantic

let parseRenewals (text: string) : int =
    try
        int text
    with _ ->
        0

let parseStrict (text: string) : int =
    try
        int text
    with ex ->
        reraise ()

let parseGuarded (text: string) : int =
    try
        int text
    with :? System.FormatException ->
        0

let interpret (outcome: Outcome) : Result<unit, string> =
    match outcome with
    | Succeeded -> Ok()
    | Failed reason -> Error reason
    | Unknown reason -> Error reason
