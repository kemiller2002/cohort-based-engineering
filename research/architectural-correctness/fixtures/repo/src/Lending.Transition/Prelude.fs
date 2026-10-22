namespace Lending.Transition

/// A minimal computation expression for Result-returning rules.
type ResultBuilder() =
    member _.Bind(r: Result<'a, 'e>, f: 'a -> Result<'b, 'e>) = Result.bind f r
    member _.Return(v: 'a) : Result<'a, 'e> = Ok v
    member _.ReturnFrom(r: Result<'a, 'e>) = r

[<AutoOpen>]
module Prelude =
    let result = ResultBuilder()

    /// Ok () when the condition holds, otherwise the error.
    let ensure condition error = if condition then Ok() else Error error

    /// Ok value for Some value, otherwise the error.
    let required error option =
        match option with
        | Some value -> Ok value
        | None -> Error error
