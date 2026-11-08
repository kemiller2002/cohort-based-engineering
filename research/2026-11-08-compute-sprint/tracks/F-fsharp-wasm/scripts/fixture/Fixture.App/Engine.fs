/// Minimal F# engine for the sprint WASM baseline: a counter whose projection is a JSON string.
module Fixture.App.Engine

type Model = { Count: int }

let initial = { Count = 0 }

let update (event: string) (model: Model) =
    match event with
    | "increment" -> { model with Count = model.Count + 1 }
    | _ -> model

let project (model: Model) = sprintf "{\"count\":%d,\"label\":\"Clicked %d times\"}" model.Count model.Count
