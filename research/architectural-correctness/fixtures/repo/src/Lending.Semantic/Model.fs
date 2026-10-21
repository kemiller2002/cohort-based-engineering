namespace Lending.Semantic

open System

type MemberId = MemberId of string

type BookId = BookId of string

type CopyId = CopyId of string

module MemberId =
    let value (MemberId id) = id

module BookId =
    let value (BookId id) = id

module CopyId =
    let value (CopyId id) = id

/// The kinds of membership the library offers.
type MemberType =
    | Standard
    | Student
    | Staff

type Member =
    { Id: MemberId
      Name: string
      Type: MemberType }

type Book =
    { Id: BookId
      Title: string
      Author: string
      Isbn: string }

/// A physical copy of a book.
type Copy = { Id: CopyId; Book: BookId }

/// A copy currently lent to a member.
type Loan =
    { Copy: CopyId
      Member: MemberId
      BorrowedOn: DateOnly
      DueDate: DateOnly
      Renewals: int }

/// A member waiting for a book.
type Hold =
    { Book: BookId
      Member: MemberId
      PlacedOn: DateOnly }

/// A fine assessed when a copy came back late.
type Fine =
    { Member: MemberId
      Copy: CopyId
      Amount: decimal
      AssessedOn: DateOnly }

/// The whole state of the library.
type Library =
    { Members: Map<MemberId, Member>
      Books: Map<BookId, Book>
      Copies: Map<CopyId, Copy>
      /// Active loans, one per copy at most.
      Loans: Map<CopyId, Loan>
      /// Holds in the order they were placed; each book's queue is the subsequence for that book.
      Holds: Hold list
      Fines: Fine list }

module Library =
    let empty =
        { Members = Map.empty
          Books = Map.empty
          Copies = Map.empty
          Loans = Map.empty
          Holds = []
          Fines = [] }

type LendingError =
    | UnknownMember of MemberId
    | UnknownBook of BookId
    | UnknownCopy of CopyId
    | DuplicateMember of MemberId
    | DuplicateBook of BookId
    | DuplicateCopy of CopyId
    | CopyAlreadyOnLoan of CopyId
    | CopyNotOnLoan of CopyId
    | LoanLimitReached of MemberId * limit: int
    | ReservedForAnotherMember of CopyId
    | RenewLimitReached of CopyId * limit: int
    | LoanOverdue of CopyId
    | HoldsWaiting of CopyId
    | AlreadyHolding of MemberId * BookId
    | InvalidInput of string
