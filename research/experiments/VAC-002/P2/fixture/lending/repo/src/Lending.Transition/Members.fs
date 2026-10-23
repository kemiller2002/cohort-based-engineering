/// LEND-L01: member standing (suspension).
module Lending.Transition.Members

open Lending.Semantic

let isSuspended memberId (library: Library) = library.Suspensions.ContainsKey memberId

/// LEND-L01-R2: a suspended member may not borrow, hold or renew.
let ensureActive memberId (library: Library) =
    ensure (not (isSuspended memberId library)) (MemberSuspended memberId)

let suspend memberId (reason: string) (library: Library) : Result<Library, LendingError> =
    result {
        let! _ = Catalog.findMember memberId library
        do! ensure (not (isSuspended memberId library)) (AlreadySuspended memberId)
        return { library with Suspensions = library.Suspensions.Add(memberId, reason) }
    }

let reinstate memberId (library: Library) : Result<Library, LendingError> =
    result {
        let! _ = Catalog.findMember memberId library
        do! ensure (isSuspended memberId library) (NotSuspended memberId)
        return { library with Suspensions = library.Suspensions.Remove memberId }
    }
