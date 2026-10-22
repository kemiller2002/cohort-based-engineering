namespace Lending.Semantic

open System

type MemberId = MemberId of string

type BookId = BookId of string

type CopyId = CopyId of string

type BranchId = BranchId of string

module MemberId =
    let value (MemberId id) = id

module BookId =
    let value (BookId id) = id

module CopyId =
    let value (CopyId id) = id

module BranchId =
    let value (BranchId id) = id

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

/// A place copies are shelved at.
type Branch = { Id: BranchId; Name: string }

/// A physical copy of a book, shelved at one branch.
type Copy =
    { Id: CopyId
      Book: BookId
      Branch: BranchId }

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

/// Money a member paid towards what they owe.
type Payment =
    { Member: MemberId
      Amount: decimal
      PaidOn: DateOnly }

/// What became of an overdue reminder the library tried to send.
type ReminderOutcome =
    | Sent
    | Bounced of reason: string
    /// The channel gave no answer: the reminder may or may not have arrived.
    | Unconfirmed

/// An overdue reminder for one loan and due date.
type Reminder =
    { Copy: CopyId
      Member: MemberId
      DueDate: DateOnly
      AttemptedAt: DateTime
      Outcome: ReminderOutcome }

/// The whole state of the library.
type Library =
    { Members: Map<MemberId, Member>
      Books: Map<BookId, Book>
      Branches: Map<BranchId, Branch>
      Copies: Map<CopyId, Copy>
      /// Active loans, one per copy at most.
      Loans: Map<CopyId, Loan>
      /// Holds in the order they were placed; each book's queue is the subsequence for that book.
      Holds: Hold list
      Fines: Fine list
      Payments: Payment list
      Reminders: Reminder list }

module Library =
    /// Every library starts with its main branch (DEC-011).
    let empty =
        { Members = Map.empty
          Books = Map.empty
          Branches = Map.ofList [ BranchId "main", { Id = BranchId "main"; Name = "Main Library" } ]
          Copies = Map.empty
          Loans = Map.empty
          Holds = []
          Fines = []
          Payments = []
          Reminders = [] }

type LendingError =
    | UnknownMember of MemberId
    | UnknownBook of BookId
    | UnknownCopy of CopyId
    | UnknownBranch of BranchId
    | DuplicateMember of MemberId
    | DuplicateBook of BookId
    | DuplicateCopy of CopyId
    | DuplicateBranch of BranchId
    | CopyAlreadyOnLoan of CopyId
    | CopyNotOnLoan of CopyId
    | LoanLimitReached of MemberId * limit: int
    | ReservedForAnotherMember of CopyId
    | RenewLimitReached of CopyId * limit: int
    | LoanOverdue of CopyId
    | HoldsWaiting of CopyId
    | AlreadyHolding of MemberId * BookId
    | NotHolding of MemberId * BookId
    | AlreadyAtBranch of CopyId * BranchId
    | BorrowingBlocked of MemberId
    | InvalidAmount of string
    | PaymentExceedsBalance of MemberId * owed: decimal
    | NothingOwed of MemberId
    | InvalidInput of string
