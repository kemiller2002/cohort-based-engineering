module Lending.Host.Cli.Render

open Lending.Application.Views

let loanLine (view: LoanView) = sprintf "%s due %s" view.LoanId view.Due

/// Re-enters the Tier 2 decision from presentation.
let preview (now: System.DateTime) (loan: Lending.Semantic.Loan) =
    match Lending.Transition.Loans.renew now loan with
    | Ok _ -> "renewable"
    | Error reason -> reason

let result (r: Result<LoanView, string>) =
    match r with
    | Ok view -> loanLine view
    | Error message -> "error: " + message
