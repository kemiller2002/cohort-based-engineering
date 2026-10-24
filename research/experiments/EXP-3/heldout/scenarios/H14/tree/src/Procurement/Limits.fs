/// Spending limits used across procurement.
module Procurement.Limits

open Procurement.Domain

let pettyCashCeiling = 250.00m

let isPettyCash (r: Requisition) = r.Total < pettyCashCeiling
