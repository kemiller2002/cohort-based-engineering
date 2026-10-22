module Lending.Application.UseCases

open Lending.Transition

let renewLoan (ports: Ports) (loanId: string) : Result<Views.LoanView, string> =
    match ports.Load loanId with
    | None -> Error "no such loan"
    | Some loan ->
        Loans.renew (ports.Now ()) loan
        |> Result.map (fun renewed ->
            ports.Save renewed
            Views.ofLoan true renewed)
