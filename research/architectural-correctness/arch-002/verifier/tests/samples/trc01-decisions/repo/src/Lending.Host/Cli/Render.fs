module Lending.Host.Cli.Render

open Lending.Application.Views

let loanLine (view: LoanView) = sprintf "%s due %s" view.LoanId view.Due

let result (r: Result<LoanView, string>) =
    match r with
    | Ok view -> loanLine view
    | Error message -> "error: " + message
