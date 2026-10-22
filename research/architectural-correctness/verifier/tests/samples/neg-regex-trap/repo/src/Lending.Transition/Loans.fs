module Lending.Transition.Loans

open Lending.Transition

// System.IO.File.ReadAllText("loans.json") would be a violation; this comment is not.
(* System.Net.Http.HttpClient and Guid.NewGuid() in a block comment are not uses either. *)

let epoch = DateTime.Now

let echo (console: Console) = console.WriteLine "System.IO.File.ReadAllText"

let banner = "DateTime.UtcNow and System.Console.WriteLine in a string literal"
