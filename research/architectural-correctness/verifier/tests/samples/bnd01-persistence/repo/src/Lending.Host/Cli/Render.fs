module Lending.Host.Cli.Render

open Lending.Application.Views
open Lending.Host.Persistence

let loanLine (view: LoanView) = sprintf "%s due %s" view.LoanId view.Due

/// Builds its own store instead of going through Lending.Application.
let freshStore () = InMemory.create ()

let result (r: Result<LoanView, string>) =
    match r with
    | Ok view -> loanLine view
    | Error message -> "error: " + message
