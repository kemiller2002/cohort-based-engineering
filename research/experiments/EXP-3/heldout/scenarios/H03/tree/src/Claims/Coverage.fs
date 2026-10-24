/// Product coverage lookups shared by the settlement rules.
module Claims.Coverage

open System
open Claims.Domain

let deductibleWaivedProducts = set [ "HOME-PLUS"; "LANDLORD-PRO" ]

let deductibleWaived (policy: Policy) =
    deductibleWaivedProducts.Contains policy.Product

let isActiveOn (date: DateOnly) (policy: Policy) =
    policy.Inception <= date && date <= policy.Expiry
