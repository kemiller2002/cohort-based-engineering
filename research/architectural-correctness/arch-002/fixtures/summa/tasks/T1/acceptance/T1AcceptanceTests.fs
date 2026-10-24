module Summa.Acceptance.T1AcceptanceTests

open System.Text.Json
open Xunit
open Summa.Ledger.Money
open Summa.Ledger.Statements
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

/// ABC Corp: EF-2026-0001 for 6,050.00 issued 2026-09-15; 2,000.00 of ACH-77 received
/// and applied on 2026-10-05.
let private books () =
    let manifest, r = organization ()

    manifest,
    r
    |> customer "CUST-0001" "ABC Corp"
    |> invoice "INV-1" "CUST-0001" (date 2026 9 15) 605000L
    |> payment "PAY-1" "CUST-0001" (date 2026 10 5) 200000L "ACH-77"
    |> apply "AL-1" "PAY-1" "INV-1" 200000L

[<Fact>]
let ``SUMMA-T1-R1 earlier activity is the opening balance and the period's settlement is a line`` () =
    let _, r = books ()
    let s = statement "CUST-0001" "USD" (date 2026 10 1) (date 2026 10 31) r |> ok
    Assert.Equal(usd 605000L, s.Opening)
    Assert.Equal<(LineKind * string * string * Money * Money) list>(
        [ Paid, "EF-2026-0001", "ACH-77", usd -200000L, usd 405000L ],
        s.Lines |> List.map (fun l -> l.Kind, l.Invoice, l.Reference, l.Amount, l.Balance)
    )
    Assert.Equal(usd 405000L, s.Closing)

[<Fact>]
let ``SUMMA-T1-R1 an invoice issued in the period comes before its settlement`` () =
    let _, r = books ()
    let s = statement "CUST-0001" "USD" (date 2026 9 1) (date 2026 10 31) r |> ok
    Assert.Equal(usd 0L, s.Opening)
    Assert.Equal<LineKind list>([ Invoiced; Paid ], s.Lines |> List.map _.Kind)
    Assert.Equal(date 2026 9 15, s.Lines.Head.Date)
    Assert.Equal(usd 405000L, s.Closing)

[<Fact>]
let ``SUMMA-T1-R1 an unknown customer has no statement`` () =
    let _, r = books ()
    Assert.Equal(Error "unknown customer CUST-9", statement "CUST-9" "USD" (date 2026 10 1) (date 2026 10 31) r |> Result.map ignore)

[<Fact>]
let ``SUMMA-T1-R3 last month's statement is offered as its JSON document`` () =
    let now = noon (date 2026 11 3)
    let manifest, r = books ()
    let model = engine now manifest r |> goTo now (Routes.Customer("CUST-0001", Routes.CustomerInvoices))
    let _, effects = run now [ StatementExportRequested "last-month" ] model

    match downloads effects with
    | [ name, mediaType, text ] ->
        Assert.Equal("statement-CUST-0001-2026-10-01-2026-10-31.json", name)
        Assert.Equal("application/json", mediaType)
        use doc = JsonDocument.Parse text
        let root = doc.RootElement
        Assert.Equal("summa.customer-statement", root.GetProperty("schema").GetString())
        Assert.Equal("ABC Corp", root.GetProperty("customer").GetProperty("name").GetString())
        Assert.Equal(605000L, root.GetProperty("opening").GetProperty("minor").GetInt64())
        Assert.Equal("paid", root.GetProperty("lines").[0].GetProperty("kind").GetString())
        Assert.Equal(405000L, root.GetProperty("closing").GetProperty("minor").GetInt64())
    | other -> failwith $"%A{other}"
