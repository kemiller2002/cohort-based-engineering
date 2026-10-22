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

type BranchView = { Branch: string; Name: string }

type CopyView =
    { Copy: string
      Book: string
      Branch: string }

type TransferView =
    { Copy: string
      Branch: string
      BranchName: string }

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

type CancelHoldView = { Member: string; Book: string }

type QueueEntryView =
    { Position: int
      Member: string
      Name: string
      Since: string }

type HoldQueueView =
    { Book: string
      Title: string
      Queue: QueueEntryView list }

type ShelfEntryView =
    { Copy: string
      Title: string
      /// None while the copy is on the shelf.
      DueBack: string option }

type ShelfView =
    { Branch: string
      Name: string
      Copies: ShelfEntryView list }

type AccountFineView =
    { Copy: string
      Amount: string
      AssessedOn: string }

type AccountView =
    { Member: string
      Name: string
      Fines: AccountFineView list
      Payments: string list
      Owed: string
      LoansHeld: int
      LoanAllowance: int }

type PaymentView =
    { Member: string
      Paid: string
      Owed: string }

type OverdueLoanView =
    { Copy: string
      Title: string
      Member: string
      Due: string
      DaysOverdue: int }

type OverdueView =
    { Today: string
      Loans: OverdueLoanView list }

type ExportView = { Path: string; Rows: int }

type ReminderRunView =
    { Sent: int
      Bounced: int
      Unconfirmed: int }

type ImportView = { Imported: int }

type ReconcileView = { Copy: string; Arrived: bool }

type MemberSummaryView =
    { Member: string
      Name: string
      Type: string
      Loans: int }

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
    | UnknownBranch(BranchId b) -> $"unknown branch {b}"
    | DuplicateMember(MemberId m) -> $"member {m} already exists"
    | DuplicateBook(BookId b) -> $"book {b} already exists"
    | DuplicateCopy(CopyId c) -> $"copy {c} already exists"
    | DuplicateBranch(BranchId b) -> $"branch {b} already exists"
    | CopyAlreadyOnLoan(CopyId c) -> $"copy {c} is already on loan"
    | CopyNotOnLoan(CopyId c) -> $"copy {c} is not on loan"
    | LoanLimitReached(MemberId m, limit) -> $"member {m} already has {limit} loans"
    | ReservedForAnotherMember(CopyId c) -> $"copy {c} is reserved for another member"
    | RenewLimitReached(CopyId c, limit) -> $"copy {c} has already been renewed {limit} times"
    | LoanOverdue(CopyId c) -> $"copy {c} is overdue"
    | HoldsWaiting(CopyId c) -> $"copy {c} has holds waiting"
    | AlreadyHolding(MemberId m, BookId b) -> $"member {m} already holds book {b}"
    | NotHolding(MemberId m, BookId b) -> $"member {m} does not hold book {b}"
    | AlreadyAtBranch(CopyId c, BranchId b) -> $"copy {c} is already at branch {b}"
    | BorrowingBlocked(MemberId m) -> $"member {m} owes too much to borrow"
    | InvalidAmount text -> $"invalid amount '{text}'"
    | PaymentExceedsBalance(MemberId m, owed) -> $"member {m} owes only {money owed}"
    | NothingOwed(MemberId m) -> $"member {m} owes nothing"
    | InvalidInput message -> message

let ofMember (m: Member) : MemberView =
    { Member = MemberId.value m.Id
      Name = m.Name
      Type = memberTypeName m.Type }

let ofBook (book: Book) : BookView =
    { Book = BookId.value book.Id
      Title = book.Title
      Author = book.Author }

let ofBranch (branch: Branch) : BranchView =
    { Branch = BranchId.value branch.Id
      Name = branch.Name }

let ofCopy (copy: Copy) : CopyView =
    { Copy = CopyId.value copy.Id
      Book = BookId.value copy.Book
      Branch = BranchId.value copy.Branch }

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

let ofTransfer (library: Library) (copy: Copy) : TransferView =
    { Copy = CopyId.value copy.Id
      Branch = BranchId.value copy.Branch
      BranchName =
        library.Branches
        |> Map.tryFind copy.Branch
        |> Option.map (fun branch -> branch.Name)
        |> Option.defaultValue "?" }

let holdQueue bookId (library: Library) : Result<HoldQueueView, LendingError> =
    Catalog.findBook bookId library
    |> Result.map (fun book ->
        { Book = BookId.value book.Id
          Title = book.Title
          Queue =
            Holds.queueFor bookId library
            |> List.mapi (fun i hold ->
                { Position = i + 1
                  Member = MemberId.value hold.Member
                  Name =
                    library.Members
                    |> Map.tryFind hold.Member
                    |> Option.map (fun m -> m.Name)
                    |> Option.defaultValue "?"
                  Since = date hold.PlacedOn }) })

let shelf branchId (library: Library) : Result<ShelfView, LendingError> =
    Catalog.findBranch branchId library
    |> Result.map (fun branch ->
        { Branch = BranchId.value branch.Id
          Name = branch.Name
          Copies =
            Catalog.copiesAt branchId library
            |> List.map (fun copy ->
                { Copy = CopyId.value copy.Id
                  Title = titleOf copy.Id library
                  DueBack = library.Loans |> Map.tryFind copy.Id |> Option.map (fun loan -> date loan.DueDate) }) })

/// How many loans a member's type allows, shown on the account.
let loanAllowance memberType =
    match memberType with
    | Standard -> 5
    | Student -> 3
    | Staff -> 10

let account memberId (library: Library) : Result<AccountView, LendingError> =
    Catalog.findMember memberId library
    |> Result.map (fun m ->
        { Member = MemberId.value m.Id
          Name = m.Name
          Fines =
            Accounts.finesOf memberId library
            |> List.map (fun fine ->
                { Copy = CopyId.value fine.Copy
                  Amount = money fine.Amount
                  AssessedOn = date fine.AssessedOn })
          Payments = Accounts.paymentsOf memberId library |> List.map (fun payment -> money payment.Amount)
          Owed = money (Accounts.owed memberId library)
          LoansHeld = Loans.loansOf memberId library |> List.length
          LoanAllowance = loanAllowance m.Type })

let ofPayment (library: Library) (payment: Payment) : PaymentView =
    { Member = MemberId.value payment.Member
      Paid = money payment.Amount
      Owed = money (Accounts.owed payment.Member library) }

let overdue (today: DateOnly) (library: Library) : OverdueView =
    { Today = date today
      Loans =
        Loans.overdue today library
        |> List.map (fun loan ->
            { Copy = CopyId.value loan.Copy
              Title = titleOf loan.Copy library
              Member = MemberId.value loan.Member
              Due = date loan.DueDate
              DaysOverdue = Loans.daysOverdue today loan }) }

let ofReminderRun (outcomes: ReminderOutcome list) : ReminderRunView =
    let count f = outcomes |> List.filter f |> List.length

    { Sent = count (fun o -> o = Sent)
      Bounced =
        count (fun o ->
            match o with
            | Bounced _ -> true
            | _ -> false)
      Unconfirmed = count (fun o -> o = Unconfirmed) }

let members (library: Library) : MemberSummaryView list =
    library.Members
    |> Map.toList
    |> List.map snd
    |> List.map (fun m ->
        { Member = MemberId.value m.Id
          Name = m.Name
          Type = memberTypeName m.Type
          Loans = Loans.loansOf m.Id library |> List.length })
