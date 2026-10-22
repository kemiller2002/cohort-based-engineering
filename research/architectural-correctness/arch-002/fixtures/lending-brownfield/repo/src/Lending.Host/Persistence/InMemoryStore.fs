/// A store that keeps the state in memory (tests, demos).
module Lending.Host.Persistence.InMemoryStore

open Lending.Semantic
open Lending.Application

let create (initial: Library) : Store =
    let cell = ref initial

    { Load = fun () -> cell.Value
      Save = fun library -> cell.Value <- library }
