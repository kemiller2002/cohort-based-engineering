/// Members, books and copies.
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

let addCopy (copy: Copy) (library: Library) : Result<Library, LendingError> =
    result {
        do! ensure (not (library.Copies.ContainsKey copy.Id)) (DuplicateCopy copy.Id)
        do! ensure (library.Books.ContainsKey copy.Book) (UnknownBook copy.Book)
        return { library with Copies = library.Copies.Add(copy.Id, copy) }
    }

let findMember memberId (library: Library) =
    library.Members |> Map.tryFind memberId |> required (UnknownMember memberId)

let findBook bookId (library: Library) =
    library.Books |> Map.tryFind bookId |> required (UnknownBook bookId)

let findCopy copyId (library: Library) =
    library.Copies |> Map.tryFind copyId |> required (UnknownCopy copyId)
