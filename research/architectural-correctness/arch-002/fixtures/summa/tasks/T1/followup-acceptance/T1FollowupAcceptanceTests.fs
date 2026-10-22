module Summa.Acceptance.T1FollowupAcceptanceTests

open System.Text.Json
open Xunit
open Summa.Ledger.Money
open Summa.Ledger.Statements
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

/// ABC Corp: EF-2026-0001 for 6,050.00 issued 2026-09-15 (Net 30, due 2026-10-15); 2,000.00
/// of ACH-77 applied on 2026-10-05; EF-2026-0002 for 1,000.00 issued 2026-10-20.
let private books () =
    let manifest, r = organization ()

    manifest,
    r
    |> customer "CUST-0001" "ABC Corp"
    |> invoice "INV-1" "CUST-0001" (date 2026 9 15) 605000L
    |> payment "PAY-1" "CUST-0001" (date 2026 10 5) 200000L "ACH-77"
    |> apply "AL-1" "PAY-1" "INV-1" 200000L
    |> invoice "INV-2" "CUST-0001" (date 2026 10 20) 100000L

[<Fact>]
let ``SUMMA-T1-F1 the closing balance is aged by each invoice's due date`` () =
    let _, r = books ()
    let s = statement "CUST-0001" "USD" (date 2026 10 1) (date 2026 10 31) r |> ok
    Assert.Equal(usd 505000L, s.Closing)
    Assert.Equal(usd 100000L, s.Aging.Current)
    Assert.Equal(usd 405000L, s.Aging.Days1To30)
    Assert.Equal(usd 0L, s.Aging.Over90)

[<Fact>]
let ``SUMMA-T1-F1 the document is version 2 with its aging`` () =
    let now = noon (date 2026 11 3)
    let manifest, r = books ()
    let model = engine now manifest r |> goTo now (Routes.Customer("CUST-0001", Routes.CustomerInvoices))
    let _, effects = run now [ StatementExportRequested "last-month" ] model
    let _, _, text = downloads effects |> List.exactlyOne
    use doc = JsonDocument.Parse text
    Assert.Equal(2, doc.RootElement.GetProperty("version").GetInt32())
    Assert.Equal(405000L, doc.RootElement.GetProperty("aging").GetProperty("days1to30").GetProperty("minor").GetInt64())

[<Fact>]
let ``SUMMA-T1-F2 the statement as CSV starts with the export header`` () =
    let now = noon (date 2026 11 3)
    let manifest, r = books ()
    let model = engine now manifest r |> goTo now (Routes.Customer("CUST-0001", Routes.CustomerInvoices))
    let _, effects = run now [ StatementCsvRequested "last-month" ] model

    match downloads effects with
    | [ name, mediaType, text ] ->
        Assert.Equal("statement-CUST-0001-2026-10-01-2026-10-31.csv", name)
        Assert.Equal("text/csv", mediaType)
        let lines = text.Split('\n')
        Assert.Equal("# Export: customer-statement", lines[0])
        let body = lines |> Array.skipWhile (fun l -> l.StartsWith "#") |> List.ofArray

        Assert.Equal<string list>(
            [ "date,kind,invoice,reference,amount,balance"
              "2026-10-01,opening,,,,6050.00"
              "2026-10-05,paid,EF-2026-0001,ACH-77,-2000.00,4050.00"
              "2026-10-20,invoiced,EF-2026-0002,,1000.00,5050.00"
              "2026-10-31,closing,,,,5050.00" ],
            body
        )
    | other -> failwith $"%A{other}"
