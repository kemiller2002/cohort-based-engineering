/// State transitions. Each command takes the current state and returns the next state and its output, or an error.
/// Commands decide nothing on their own: every business rule comes from `Rules`.
module Billing.Commands

open System
open System.Globalization
open Billing.Domain

let money (amount: decimal) = amount.ToString("F2", CultureInfo.InvariantCulture)

let date (day: DateOnly) = day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)

let private found (error: BillingError) (value: 'a option) =
    match value with
    | Some v -> Ok v
    | None -> Error error

let private customer (id: string) (state: State) =
    state.Customers |> Map.tryFind id |> found (UnknownCustomer id)

let private invoice (id: string) (state: State) =
    state.Invoices |> Map.tryFind id |> found (UnknownInvoice id)

let parseAmount (text: string) =
    match Decimal.TryParse(text, NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture) with
    | true, amount when amount > 0m && Rules.round2 amount = amount -> Ok amount
    | _ -> Error(InvalidAmount text)

let addCustomer (id: string) (plan: Plan) (kind: CustomerKind) (region: string) (name: string) (state: State) =
    if state.Customers.ContainsKey id then
        Error(CustomerExists id)
    else
        let added =
            { Id = id
              Name = name
              Plan = plan
              Kind = kind
              Region = region }

        Ok(
            { state with Customers = state.Customers |> Map.add id added },
            $"customer {id} added: {name} ({Plan.name plan}, {CustomerKind.name kind}, {region})"
        )

let issueInvoice (today: DateOnly) (id: string) (customerId: string) (amount: decimal) (state: State) =
    customer customerId state
    |> Result.bind (fun _ ->
        if state.Invoices.ContainsKey id then
            Error(InvoiceExists id)
        else
            let issued =
                { Id = id
                  Customer = customerId
                  Amount = amount
                  Issued = today
                  Due = Rules.dueDate today
                  LateFee = 0m
                  Paid = 0m }

            Ok(
                { state with
                    Invoices = state.Invoices |> Map.add id issued
                    IssueOrder = state.IssueOrder @ [ id ] },
                $"{id} issued to {customerId}: {money amount} due {date issued.Due}"
            ))

let describe (i: Invoice) =
    $"{i.Id} {i.Customer} amount {money i.Amount}, late fee {money i.LateFee}, paid {money i.Paid}, outstanding {money (Rules.outstanding i)}, due {date i.Due}"

let show (id: string) (state: State) =
    invoice id state |> Result.map (fun i -> state, describe i)

let balance (customerId: string) (state: State) =
    customer customerId state
    |> Result.map (fun _ -> state, $"{customerId} balance {money (Rules.balance customerId state)}")

let runLateFees (today: DateOnly) (state: State) =
    let charged =
        state.IssueOrder
        |> List.map (fun id -> state.Invoices[id])
        |> List.filter (Rules.owesLateFee today)
        |> List.filter (fun i -> Rules.chased state.Customers[i.Customer])
        |> List.map (fun i -> { i with LateFee = Rules.lateFee i })

    let invoices =
        charged |> List.fold (fun acc i -> acc |> Map.add i.Id i) state.Invoices

    Ok({ state with Invoices = invoices }, $"late fees applied: {List.length charged}")

let describeError (error: BillingError) =
    match error with
    | UnknownCustomer id -> $"unknown customer {id}"
    | UnknownInvoice id -> $"unknown invoice {id}"
    | CustomerExists id -> $"customer {id} already exists"
    | InvoiceExists id -> $"invoice {id} already exists"
    | InvalidAmount text -> $"invalid amount {text}"
    | InvalidValue(what, value) -> $"invalid {what} {value}"
