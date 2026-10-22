namespace Lending.Semantic

open System

// A comment that mentions System.IO.File.ReadAllText and DateTime.Now is not a use.
(* Neither is System.Console.WriteLine in a block comment. *)

type BookId = BookId of string
type MemberId = MemberId of string

type Loan =
    { LoanId: string
      Book: BookId
      Borrower: MemberId
      DueDate: DateTime
      Renewals: int }

type Outcome =
    | Succeeded
    | Failed of string
    | Unknown of string

module Policy =
    let maxRenewals = 3
let broken : int = "not an int"
