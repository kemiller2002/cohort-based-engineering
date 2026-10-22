/// The application's use cases: translate input, let Tier 2 decide, persist, project a view.
module Lending.Application.UseCases

open System
open Lending.Semantic
open Lending.Transition

/// Loads the state, applies a decision for today and saves the new state when it succeeds.
let private commit (ports: Ports) (decide: DateOnly -> Library -> Result<Library * 'a, LendingError>) =
    let library = ports.Store.Load()

    match decide (ports.Clock()) library with
    | Ok(next, value) ->
        ports.Store.Save next
        Ok value
    | Error error -> Error error

let private query (ports: Ports) (project: Library -> Result<'a, LendingError>) = project (ports.Store.Load())

let parseMemberType (text: string) =
    match text.Trim().ToLowerInvariant() with
    | "standard" -> Ok Standard
    | "student" -> Ok Student
    | "staff" -> Ok Staff
    | other -> Error(InvalidInput $"unknown member type '{other}' (standard, student or staff)")

let addMember ports (memberId: string) (memberType: string) (name: string) : Result<Views.MemberView, LendingError> =
    parseMemberType memberType
    |> Result.bind (fun memberType ->
        let newMember =
            { Id = MemberId memberId
              Name = name
              Type = memberType }

        commit ports (fun _ library -> Catalog.addMember newMember library |> Result.map (fun l -> l, Views.ofMember newMember)))

let addBook ports (bookId: string) (isbn: string) (title: string) (author: string) : Result<Views.BookView, LendingError> =
    let book =
        { Id = BookId bookId
          Title = title
          Author = author
          Isbn = isbn }

    commit ports (fun _ library -> Catalog.addBook book library |> Result.map (fun l -> l, Views.ofBook book))

let addCopy ports (copyId: string) (bookId: string) : Result<Views.CopyView, LendingError> =
    let copy = { Id = CopyId copyId; Book = BookId bookId }
    commit ports (fun _ library -> Catalog.addCopy copy library |> Result.map (fun l -> l, Views.ofCopy copy))

let borrow ports (memberId: string) (copyId: string) : Result<Views.BorrowView, LendingError> =
    commit ports (fun today library ->
        Loans.borrow today (MemberId memberId) (CopyId copyId) library
        |> Result.map (fun (l, loan) -> l, Views.ofBorrow loan))

let returnCopy ports (copyId: string) : Result<Views.ReturnView, LendingError> =
    commit ports (fun today library ->
        Loans.returnCopy today (CopyId copyId) library
        |> Result.map (fun (l, returned) -> l, Views.ofReturn returned))

let placeHold ports (memberId: string) (bookId: string) : Result<Views.HoldView, LendingError> =
    commit ports (fun today library ->
        Holds.place today (MemberId memberId) (BookId bookId) library
        |> Result.map (fun (l, position) ->
            l,
            { Views.HoldView.Member = memberId
              Book = bookId
              Position = position }))

let loans ports (memberId: string) : Result<Views.MemberLoansView, LendingError> =
    query ports (Views.memberLoans (MemberId memberId))
