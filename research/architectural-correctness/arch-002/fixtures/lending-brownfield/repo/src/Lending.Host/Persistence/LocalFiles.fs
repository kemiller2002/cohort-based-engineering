/// Text files on the local file system.
module Lending.Host.Persistence.LocalFiles

open System.IO
open Lending.Application

let files: Files =
    { WriteLines = fun path lines -> File.WriteAllLines(path, lines)
      ReadLines =
        fun path ->
            if File.Exists path then
                Some(File.ReadAllLines path |> List.ofArray)
            else
                None }
