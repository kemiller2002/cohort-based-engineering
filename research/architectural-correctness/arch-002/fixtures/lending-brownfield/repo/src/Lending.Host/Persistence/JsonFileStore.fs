/// A store that keeps the state in one JSON file, and backups in the same format.
module Lending.Host.Persistence.JsonFileStore

open System.IO
open Lending.Semantic
open Lending.Application

let create (path: string) : Store =
    { Load =
        fun () ->
            if File.Exists path then
                JsonCodec.decode (File.ReadAllText path)
            else
                Library.empty
      Save = fun library -> File.WriteAllText(path, JsonCodec.encode library) }

/// Backups: one JSON snapshot per path.
let archive: Archive =
    { Save = fun path library -> File.WriteAllText(path, JsonCodec.encode library)
      Load =
        fun path ->
            if File.Exists path then
                Some(JsonCodec.decode (File.ReadAllText path))
            else
                None }
