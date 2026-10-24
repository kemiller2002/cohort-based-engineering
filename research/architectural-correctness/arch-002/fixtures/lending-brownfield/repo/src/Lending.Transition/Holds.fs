/// DEC-005: holds queue per book, first come first served.
module Lending.Transition.Holds

open System
open Lending.Semantic

/// The holds for a book, head of the queue first.
let queueFor bookId (library: Library) =
    library.Holds |> List.filter (fun hold -> hold.Book = bookId)

/// Places a hold and returns the member's position in the book's queue (1 = next).
let place (today: DateOnly) memberId bookId (library: Library) : Result<Library * int, LendingError> =
    result {
        let! _ = Catalog.findMember memberId library
        let! _ = Catalog.findBook bookId library
        let queue = queueFor bookId library
        do! ensure (queue |> List.forall (fun hold -> hold.Member <> memberId)) (AlreadyHolding(memberId, bookId))

        let hold: Hold =
            { Book = bookId
              Member = memberId
              PlacedOn = today }

        return { library with Holds = library.Holds @ [ hold ] }, List.length queue + 1
    }

/// Removes a member's hold on a book, if any.
let release memberId bookId (library: Library) =
    { library with Holds = library.Holds |> List.filter (fun hold -> not (hold.Book = bookId && hold.Member = memberId)) }

/// A member withdraws their hold; the members behind them move up.
let cancel memberId bookId (library: Library) : Result<Library, LendingError> =
    result {
        let! _ = Catalog.findMember memberId library
        let! _ = Catalog.findBook bookId library
        do! ensure (queueFor bookId library |> List.exists (fun hold -> hold.Member = memberId)) (NotHolding(memberId, bookId))
        return release memberId bookId library
    }
