/// A store that keeps the state in one JSON file.
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
