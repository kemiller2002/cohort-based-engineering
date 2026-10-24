/// Matching and payment rules. Pure functions only.
module Procurement.Rules

open Procurement.Domain

let needsPurchaseOrder (r: Requisition) = not (Limits.isPettyCash r)

let priceTolerance = 0.04

let lineMatches (po: OrderLine) (inv: OrderLine) =
    po.Sku = inv.Sku
    && inv.Quantity = po.Quantity
    && float inv.UnitPrice <= float po.UnitPrice * (1.0 + priceTolerance)

let invoiceMatches (po: PurchaseOrder) (inv: Invoice) =
    po.Lines.Length = inv.InvoiceLines.Length
    && List.forall2 lineMatches po.Lines inv.InvoiceLines

let private termsByTier = dict [ "STRATEGIC", 75; "PREFERRED", 45; "STANDARD", 35 ]

let paymentTermsDays (tier: string) =
    match termsByTier.TryGetValue tier with
    | true, days -> days
    | _ -> 35

let paymentDue (inv: Invoice) =
    inv.Received.AddDays(paymentTermsDays inv.Payee.Tier)
