module Lending.Host.Composition

open System
open Lending.Application

let ports () : Ports =
    let load, save = Persistence.InMemory.create ()
    { Now = (fun () -> DateTime.UtcNow); Load = load; Save = save }
