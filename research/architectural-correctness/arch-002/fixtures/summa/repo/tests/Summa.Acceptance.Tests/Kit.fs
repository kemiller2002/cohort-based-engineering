/// Helpers for the acceptance tests in Acceptance/: books built through Summa's own domain
/// commands, and the accounting engine driven by its messages.
module Summa.Acceptance.Kit

open System
open Summa.Ledger.Money
open Summa.Ledger.Ledger
open Summa.Ledger.Invoicing
open Summa.Ledger.Payments
open Summa.Storage
open Summa.Web.Engine.Common
open Summa.Web.Engine.Accounting

let ok result =
    match result with
    | Ok value -> value
    | Error problems -> failwith $"%A{problems}"

let date (y: int) (m: int) (d: int) = DateOnly(y, m, d)

/// Noon UTC on a day.
let noon (d: DateOnly) = DateTimeOffset(d.ToDateTime(TimeOnly(12, 0)), TimeSpan.Zero)

let contextOn (d: DateOnly) : Context =
    { Who = "acceptance"
      When = noon d
      Source = "acceptance"
      CorrelationId = None
      Provenance = None }

let company: Organization.CompanyInformation =
    { LegalName = "Demo Consulting LLC"
      Address = "1 Example Street\nSpringfield"
      TaxId = None
      Email = "billing@demo.example" }

/// A new local organization (as a new browser starts one): its manifest and books with the
/// starting chart, whose account ids are its codes (1000 cash, 1100 receivables, 4000 revenue).
let organization () =
    LocalSnapshot.start (contextOn (date 2026 1 1)) "Demo Consulting" company "ACH to account ending 0000 (demo)" |> ok

let customer (id: string) (name: string) (r: Receivables) =
    let c =
        { Id = id
          Name = name
          BillingName = name
          BillingAddress = "1 Main Street"
          Email = "ap@" + id.ToLowerInvariant() + ".example"
          DefaultTerms = Some(Net 30)
          PaymentProfileId = None
          Active = true
          Tax = TaxNotAssessed
          LegalFields = []
          RequiresPurchaseOrder = false }

    { r with Books = saveCustomer (contextOn (date 2026 1 1)) c r.Books }

/// Issues an invoice of one line (`minor` cents of consulting) to a customer on a day, with the
/// given terms. Its id is `invoiceId`; its number is the next `EF-<year>-NNNN`.
let invoiceWith (terms: PaymentTerms option) (invoiceId: string) (customerId: string) (issued: DateOnly) (minor: int64) (r: Receivables) =
    let draftId = "D-" + invoiceId

    let line =
        { Description = "Consulting"
          QuantityThousandths = 1000L
          UnitPrice = usd minor
          RevenueAccountId = "4000"
          Project = None
          WorkItem = None
          Discount = None
          Source = Summa.Ledger.Sources.ManualLine
          Rate = None
          Tax = NotAssessed
          Details = None }

    let draft =
        { DraftId = draftId
          CustomerId = customerId
          Currency = "USD"
          Lines = [ line ]
          Adjustments = []
          Discounts = []
          Terms = terms
          DueDate = None
          Corrects = None
          EngagementId = None
          Details = noDetails
          Assumptions = []
          Recipients = None
          Version = 0
          Review = Editing }

    let ctx = contextOn issued
    let books = saveDraft ctx draft r.Books |> ok
    let version = books.Drafts[draftId].Version

    let request =
        { DraftId = draftId
          IssueDate = issued
          NumberOverride = None
          Numbering = defaultNumbering "EF"
          ExpectedVersion = version
          Issuer =
            { LegalName = company.LegalName
              Address = company.Address
              TaxId = None
              Email = company.Email
              PaymentInstructions = "ACH to account ending 0000 (demo)"
              PaymentMethods = []
              PaymentProfile = None
              LegalFields = [] }
          Template = Summa.Ledger.Documents.currentTemplate
          ApprovalReason = None
          SystemTerms = Net 30
          ReceivableAccountId = "1100"
          InvoiceId = invoiceId
          JournalEntryId = "JE-" + invoiceId
          ObligationId = "OBL-" + invoiceId }

    { r with Books = issue ctx request books |> ok |> fst }

let invoice invoiceId customerId issued minor r = invoiceWith None invoiceId customerId issued minor r

/// Records a payment received on a day.
let payment (paymentId: string) (customerId: string) (received: DateOnly) (minor: int64) (reference: string) (r: Receivables) =
    let p =
        { Id = paymentId
          CustomerId = customerId
          DateReceived = received
          Amount = usd minor
          Method = Ach
          Reference = reference
          Memo = None }

    recordPayment (contextOn received) p r |> ok

/// Applies part of a payment to an invoice (Cash/AR).
let apply (allocationId: string) (paymentId: string) (invoiceId: string) (minor: int64) (r: Receivables) =
    let request =
        { AllocationId = allocationId
          PaymentId = paymentId
          InvoiceId = invoiceId
          Amount = usd minor
          JournalEntryId = "JE-" + allocationId
          CashAccountId = "1000"
          ReceivableAccountId = "1100" }

    allocate (contextOn r.Payments[paymentId].DateReceived) request r |> ok

// ---- the accounting engine ------------------------------------------------------------------

let localConfig = """{"environment":"local","environmentName":"local development"}"""

let page (hash: string) : Limen.Routing.PageLocation =
    { Origin = "https://summa.example"
      Path = "/app/"
      Query = ""
      Hash = hash }

let ctxAt (now: DateTimeOffset) : Ctx = { Now = now; Actor = "local-person" }

/// Runs messages through the engine at one instant, collecting every effect.
let run (now: DateTimeOffset) (msgs: Msg list) (model: Model) =
    msgs
    |> List.fold (fun (m, effects) msg -> let next, more = update (ctxAt now) msg m in next, effects @ more) (model, [])

/// The engine with these books loaded from the browser, on `now`, with the files pack offered.
let engine (now: DateTimeOffset) (manifest: Organization.OrganizationManifest) (r: Receivables) =
    let snapshot = LocalSnapshot.encode manifest r |> ok
    let model, _ = run now [ Started(page ""); ConfigurationRead(Ok localConfig); Loaded(Some snapshot) ] initial
    { model with Packs = { model.Packs with Files = true } }

/// Opens a place, as following a link does.
let goTo (now: DateTimeOffset) (place: Summa.Web.Engine.Routes.Place) (model: Model) =
    run now [ LocationChanged(page (Summa.Web.Engine.Routes.href place)) ] model |> fst

let viewValue (name: string) (model: Model) =
    match view model |> List.tryFind (fun (n, _) -> n = name) with
    | Some(_, Value(Text t)) -> t
    | Some(_, Value(Flag f)) -> string f
    | Some(_, Value(Number n)) -> string n
    | _ -> failwith $"no scalar view value {name}"

/// The downloads among effects: file name, media type and decoded text.
let downloads (effects: AppEffect list) =
    effects
    |> List.choose (function
        | OfferDownload(name, mediaType, data) -> Some(name, mediaType, Text.Encoding.UTF8.GetString(Convert.FromBase64String data))
        | _ -> None)
