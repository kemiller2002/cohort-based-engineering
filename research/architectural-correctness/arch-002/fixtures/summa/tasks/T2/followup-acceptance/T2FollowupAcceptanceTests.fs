module Summa.Acceptance.T2FollowupAcceptanceTests

open System.Text.Json
open Xunit
open Summa.Storage
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

let private books () =
    let manifest, r = organization ()

    manifest,
    r
    |> customer "CUST-0001" "ABC Corp"
    |> invoice "INV-1" "CUST-0001" (date 2026 9 15) 605000L
    |> payment "PAY-1" "CUST-0001" (date 2026 10 5) 200000L "ACH-77"

[<Fact>]
let ``SUMMA-T2-F1 the file is version 2 and counts what the books hold`` () =
    let manifest, r = books ()
    use doc = JsonDocument.Parse(Transfer.export manifest r (noon (date 2026 10 7)) |> ok)
    Assert.Equal(2, doc.RootElement.GetProperty("version").GetInt32())
    let contents = doc.RootElement.GetProperty "contents"
    Assert.Equal(1, contents.GetProperty("customers").GetInt32())
    Assert.Equal(1, contents.GetProperty("invoices").GetInt32())
    Assert.Equal(1, contents.GetProperty("payments").GetInt32())

[<Fact>]
let ``SUMMA-T2-F2 the page says what a pasted file would bring`` () =
    let now = noon (date 2026 10 7)
    let manifest, r = books ()
    let file = Transfer.export manifest r now |> ok
    let emptyManifest, empty = organization ()
    let there = engine now emptyManifest empty |> goTo now Routes.Settings
    let pasted, _ = run now [ BooksTransferTextChanged file ] there
    Assert.Equal("Demo Consulting: 1 customer, 1 invoice and 1 payment, exported on 2026-10-07.", viewValue "booksTransferPreview" pasted)
    let wrong, _ = run now [ BooksTransferTextChanged "{}" ] there
    Assert.Equal("This file cannot be imported: This is not a Summa books transfer file.", viewValue "booksTransferPreview" wrong)
