/// Standing orders: recurring payments on a fixed day of the month
/// (docs/design/standing-orders.md).
module Ledger.StandingOrders

open System
open System.Globalization

let private invalid (seen: Set<string>) (order: StandingOrder) =
    order.Value <= 0m || order.DayOfMonth < 1 || order.DayOfMonth > 31 || seen.Contains order.OrderId

/// The id of the first invalid order, in list order.
let private firstInvalid (orders: StandingOrder list) : string option =
    orders
    |> List.fold
        (fun (found: string option, seen: Set<string>) order ->
            match found with
            | Some _ -> found, seen
            | None when invalid seen order -> Some order.OrderId, seen
            | None -> None, seen.Add order.OrderId)
        (None, Set.empty)
    |> fst

let private isDue (date: DateOnly) (order: StandingOrder) =
    let days = DateTime.DaysInMonth(date.Year, date.Month)
    order.DayOfMonth = date.Day || (order.DayOfMonth > days && date.Day = days)

let private referenceFor (order: StandingOrder) (date: DateOnly) =
    "standing:" + order.OrderId + ":" + date.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)

let private pay (date: DateOnly) (outcomes: OrderOutcome list, ledger: LedgerState) (order: StandingOrder) =
    let reference = referenceFor order date
    if ledger.Postings |> List.exists (fun p -> p.Reference = reference) then AlreadyPaid order.OrderId :: outcomes, ledger
    else
        match Ledger.transfer order.Payer order.Payee order.Value reference ledger with
        | Ok next -> Paid order.OrderId :: outcomes, next
        | Error e -> Skipped(order.OrderId, e) :: outcomes, ledger

/// Pays the orders due on `date`, in ascending ordinal id order, each in full or not at all.
let run (date: DateOnly) (orders: StandingOrder list) (ledger: LedgerState) : Result<OrderOutcome list * LedgerState, LedgerError> =
    match firstInvalid orders with
    | Some id -> Error(InvalidOrder id)
    | None ->
        Ledger.setDate date ledger
        |> Result.map (fun dated ->
            let outcomes, paid =
                orders
                |> List.filter (isDue date)
                |> List.sortWith (fun a b -> String.CompareOrdinal(a.OrderId, b.OrderId))
                |> List.fold (pay date) ([], dated)
            List.rev outcomes, paid)
