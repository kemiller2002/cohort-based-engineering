/// Business rules, each traced to the decision record that sets it (docs/decisions/). Pure functions only.
module Billing.Rules

open System
open Billing.Domain

/// Money is kept to cents, rounding half away from zero.
let round2 (amount: decimal) = Math.Round(amount, 2, MidpointRounding.AwayFromZero)

/// DEC-B01: an invoice is due 30 days after it is issued.
let paymentTermDays = 30

let dueDate (issued: DateOnly) = issued.AddDays paymentTermDays

/// DEC-B03: the late fee is 2% of the invoice amount.
let lateFeeRate = 0.02m

let lateFee (invoice: Invoice) = round2 (invoice.Amount * lateFeeRate)

let outstanding (invoice: Invoice) = invoice.Amount + invoice.LateFee - invoice.Paid

/// DEC-B03: an invoice is overdue when today is after its due date and something is still outstanding.
let isOverdue (today: DateOnly) (invoice: Invoice) = today > invoice.Due && outstanding invoice > 0m

/// Nonprofit accounts are not chased for late payment.
let chased (customer: Customer) = customer.Kind <> Nonprofit

/// DEC-B03: the fee is charged once per invoice.
let owesLateFee (today: DateOnly) (invoice: Invoice) = isOverdue today invoice && invoice.LateFee = 0m

/// DEC-B02: what a customer owes is the sum of what is outstanding on their invoices.
let balance (customer: string) (state: State) =
    State.invoicesOf customer state |> List.sumBy outstanding
