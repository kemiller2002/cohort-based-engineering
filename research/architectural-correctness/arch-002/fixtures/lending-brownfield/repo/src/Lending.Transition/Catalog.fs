/// Members, books, branches and copies.
module Lending.Transition.Catalog

open System
open Lending.Semantic

let addMember (newMember: Member) (library: Library) : Result<Library, LendingError> =
    result {
        do! ensure (not (library.Members.ContainsKey newMember.Id)) (DuplicateMember newMember.Id)
        do! ensure (not (String.IsNullOrWhiteSpace newMember.Name)) (InvalidInput "a member needs a name")
        return { library with Members = library.Members.Add(newMember.Id, newMember) }
    }

let addBook (book: Book) (library: Library) : Result<Library, LendingError> =
    result {
        do! ensure (not (library.Books.ContainsKey book.Id)) (DuplicateBook book.Id)
        do! ensure (not (String.IsNullOrWhiteSpace book.Title)) (InvalidInput "a book needs a title")
        return { library with Books = library.Books.Add(book.Id, book) }
    }

/// DEC-011: a branch has a unique id and a name.
let addBranch (branch: Branch) (library: Library) : Result<Library, LendingError> =
    result {
        do! ensure (not (library.Branches.ContainsKey branch.Id)) (DuplicateBranch branch.Id)
        do! ensure (not (String.IsNullOrWhiteSpace branch.Name)) (InvalidInput "a branch needs a name")
        return { library with Branches = library.Branches.Add(branch.Id, branch) }
    }

let addCopy (copy: Copy) (library: Library) : Result<Library, LendingError> =
    result {
        do! ensure (not (library.Copies.ContainsKey copy.Id)) (DuplicateCopy copy.Id)
        do! ensure (library.Books.ContainsKey copy.Book) (UnknownBook copy.Book)
        do! ensure (library.Branches.ContainsKey copy.Branch) (UnknownBranch copy.Branch)
        return { library with Copies = library.Copies.Add(copy.Id, copy) }
    }

let findMember memberId (library: Library) =
    library.Members |> Map.tryFind memberId |> required (UnknownMember memberId)

let findBook bookId (library: Library) =
    library.Books |> Map.tryFind bookId |> required (UnknownBook bookId)

let findCopy copyId (library: Library) =
    library.Copies |> Map.tryFind copyId |> required (UnknownCopy copyId)

let findBranch branchId (library: Library) =
    library.Branches |> Map.tryFind branchId |> required (UnknownBranch branchId)

/// DEC-011: a copy moves to another branch only while it is on the shelf.
let transfer copyId branchId (library: Library) : Result<Library * Copy, LendingError> =
    result {
        let! copy = findCopy copyId library
        let! _ = findBranch branchId library
        do! ensure (copy.Branch <> branchId) (AlreadyAtBranch(copyId, branchId))
        do! ensure (not (library.Loans.ContainsKey copyId)) (CopyAlreadyOnLoan copyId)
        let moved = { copy with Branch = branchId }
        return { library with Copies = library.Copies.Add(copyId, moved) }, moved
    }

/// The copies shelved at a branch, in copy id order.
let copiesAt branchId (library: Library) =
    library.Copies
    |> Map.toList
    |> List.map snd
    |> List.filter (fun copy -> copy.Branch = branchId)
    |> List.sortBy (fun copy -> CopyId.value copy.Id)

/// The copies of a book, in copy id order.
let copiesOf bookId (library: Library) =
    library.Copies
    |> Map.toList
    |> List.map snd
    |> List.filter (fun copy -> copy.Book = bookId)
    |> List.sortBy (fun copy -> CopyId.value copy.Id)
