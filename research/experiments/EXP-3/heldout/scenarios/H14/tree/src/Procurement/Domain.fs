/// Procurement domain types. Data only; the rules live in Rules.fs.
module Procurement.Domain

open System

type Approver =
    | Manager
    | Director
    | Cfo

type Vendor =
    { Id: string
      Name: string
      Tier: string }

type Requisition =
    { Id: string
      Requester: string
      Vendor: Vendor
      Category: string
      Total: decimal
      IsRenewal: bool
      Incoterm: string
      Raised: DateOnly }

type ApprovalLimits =
    { ManagerMax: decimal
      DirectorMax: decimal }

type OrderLine =
    { Sku: string
      Quantity: int
      UnitPrice: decimal }

type PurchaseOrder =
    { PoNumber: string
      Supplier: Vendor
      Lines: OrderLine list }

type Invoice =
    { InvoiceNumber: string
      Po: string
      Payee: Vendor
      InvoiceLines: OrderLine list
      Received: DateOnly
      Paid: DateOnly option
      Amount: decimal }
