/// DEC-010: payments towards what a member owes.
module Lending.Transition.Payments

open System
open Lending.Semantic

/// An amount of money: positive, with at most two decimals.
let parseAmount (text: string) : Result<decimal, LendingError> =
    match Decimal.TryParse(text, Globalization.NumberStyles.Number, Globalization.CultureInfo.InvariantCulture) with
    | true, amount when amount > 0m && Decimal.Round(amount, 2) = amount -> Ok amount
    | _ -> Error(InvalidAmount text)

/// Records a payment; a member cannot pay more than they owe.
let pay memberId (amount: decimal) (library: Library) : Result<Library * Payment, LendingError> =
    result {
        let! _ = Catalog.findMember memberId library
        let owed = Accounts.owed memberId library
        do! ensure (owed > 0m) (NothingOwed memberId)
        do! ensure (amount <= owed) (PaymentExceedsBalance(memberId, owed))

        let payment =
            { Member = memberId
              Amount = amount
              PaidOn = DateOnly.FromDateTime DateTime.Today }

        return { library with Payments = library.Payments @ [ payment ] }, payment
    }
