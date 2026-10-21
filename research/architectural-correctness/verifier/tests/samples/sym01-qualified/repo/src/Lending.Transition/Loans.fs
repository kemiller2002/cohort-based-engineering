module Lending.Transition.Loans

// No `open System.IO` anywhere: the use below is fully qualified.
let loadLimit (path: string) : int =
    System.IO.File.ReadAllText path |> int
