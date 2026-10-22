/// What the application shows: plain view models projected from the semantic state.
module Lending.Application.Views

open System
open System.Globalization
open Lending.Semantic
open Lending.Transition

type MemberView =
    { Member: string
      Name: string
      Type: string }

type BookView =
    { Book: string
      Title: string
      Author: string }

type CopyView = { Copy: string; Book: string }

type LoanView =
    { Copy: string
      Title: string
      Due: string }

type MemberLoansView =
    { Member: string
      Name: string
      Loans: LoanView list }

type BorrowView =
    { Copy: string
      Member: string
      Due: string }

type ReturnView =
    { Copy: string
      DaysLate: int
      Fine: string option }

type HoldView =
    { Member: string
      Book: string
      Position: int }

let date (d: DateOnly) = d.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)

let money (amount: decimal) = amount.ToString("0.00", CultureInfo.InvariantCulture)

let memberTypeName memberType =
    match memberType with
    | Standard -> "standard"
    | Student -> "student"
    | Staff -> "staff"

let describeError error =
    match error with
    | UnknownMember(MemberId m) -> $"unknown member {m}"
    | UnknownBook(BookId b) -> $"unknown book {b}"
    | UnknownCopy(CopyId c) -> $"unknown copy {c}"
    | DuplicateMember(MemberId m) -> $"member {m} already exists"
    | DuplicateBook(BookId b) -> $"book {b} already exists"
    | DuplicateCopy(CopyId c) -> $"copy {c} already exists"
    | CopyAlreadyOnLoan(CopyId c) -> $"copy {c} is already on loan"
    | CopyNotOnLoan(CopyId c) -> $"copy {c} is not on loan"
    | LoanLimitReached(MemberId m, limit) -> $"member {m} already has {limit} loans"
    | ReservedForAnotherMember(CopyId c) -> $"copy {c} is reserved for another member"
    | RenewLimitReached(CopyId c, limit) -> $"copy {c} has already been renewed {limit} times"
    | LoanOverdue(CopyId c) -> $"copy {c} is overdue"
    | HoldsWaiting(CopyId c) -> $"copy {c} has holds waiting"
    | AlreadyHolding(MemberId m, BookId b) -> $"member {m} already holds book {b}"
    | InvalidInput message -> message

let ofMember (m: Member) : MemberView =
    { Member = MemberId.value m.Id
      Name = m.Name
      Type = memberTypeName m.Type }

let ofBook (book: Book) : BookView =
    { Book = BookId.value book.Id
      Title = book.Title
      Author = book.Author }

let ofCopy (copy: Copy) : CopyView =
    { Copy = CopyId.value copy.Id
      Book = BookId.value copy.Book }

let ofBorrow (loan: Loan) : BorrowView =
    { Copy = CopyId.value loan.Copy
      Member = MemberId.value loan.Member
      Due = date loan.DueDate }

let ofReturn (returned: Loans.Returned) : ReturnView =
    { Copy = CopyId.value returned.Loan.Copy
      DaysLate = returned.DaysLate
      Fine = returned.Fine |> Option.map (fun fine -> money fine.Amount) }

let titleOf copyId (library: Library) =
    library.Copies
    |> Map.tryFind copyId
    |> Option.bind (fun copy -> library.Books |> Map.tryFind copy.Book)
    |> Option.map (fun book -> book.Title)
    |> Option.defaultValue "?"

let ofLoan (library: Library) (loan: Loan) : LoanView =
    { Copy = CopyId.value loan.Copy
      Title = titleOf loan.Copy library
      Due = date loan.DueDate }

let memberLoans memberId (library: Library) : Result<MemberLoansView, LendingError> =
    Catalog.findMember memberId library
    |> Result.map (fun m ->
        { Member = MemberId.value m.Id
          Name = m.Name
          Loans = Loans.loansOf memberId library |> List.map (ofLoan library) })
