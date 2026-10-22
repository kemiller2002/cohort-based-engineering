namespace Lending.Application

open System
open Lending.Semantic

type Ports =
    { Now: unit -> DateTime
      Load: string -> Loan option
      Save: Loan -> unit }
