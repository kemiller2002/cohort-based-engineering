module Lending.Host.Persistence.InMemory

open System.Collections.Generic
open Lending.Semantic

let create () =
    let store = Dictionary<string, Loan>()
    (fun id -> match store.TryGetValue id with | true, l -> Some l | _ -> None),
    (fun (loan: Loan) -> store[loan.LoanId] <- loan)
