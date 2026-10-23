/// The billing vocabulary: customers, invoices and the state that holds them. No rules live here.
module Billing.Domain

open System

type Plan =
    | Standard
    | Premium

type CustomerKind =
    | Business
    | Nonprofit

type Customer =
    { Id: string
      Name: string
      Plan: Plan
      Kind: CustomerKind
      /// Province or state code, for example `ON`.
      Region: string }

type Invoice =
    { Id: string
      Customer: string
      Amount: decimal
      Issued: DateOnly
      Due: DateOnly
      LateFee: decimal
      Paid: decimal }

type State =
    { Customers: Map<string, Customer>
      Invoices: Map<string, Invoice>
      /// Invoice ids in the order they were issued.
      IssueOrder: string list }

type BillingError =
    | UnknownCustomer of string
    | UnknownInvoice of string
    | CustomerExists of string
    | InvoiceExists of string
    | InvalidAmount of string
    | InvalidValue of what: string * value: string

[<RequireQualifiedAccess>]
module State =

    let empty =
        { Customers = Map.empty
          Invoices = Map.empty
          IssueOrder = [] }

    let invoicesOf (customer: string) (state: State) =
        state.IssueOrder
        |> List.map (fun id -> state.Invoices[id])
        |> List.filter (fun invoice -> invoice.Customer = customer)

[<RequireQualifiedAccess>]
module Plan =

    let parse text =
        match text with
        | "standard" -> Ok Standard
        | "premium" -> Ok Premium
        | other -> Error(InvalidValue("plan", other))

    let name plan =
        match plan with
        | Standard -> "standard"
        | Premium -> "premium"

[<RequireQualifiedAccess>]
module CustomerKind =

    let parse text =
        match text with
        | "business" -> Ok Business
        | "nonprofit" -> Ok Nonprofit
        | other -> Error(InvalidValue("customer kind", other))

    let name kind =
        match kind with
        | Business -> "business"
        | Nonprofit -> "nonprofit"
