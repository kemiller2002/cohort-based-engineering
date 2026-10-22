module Summa.Acceptance.T2AcceptanceTests

open Xunit
open Summa.Storage
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

/// Books with one customer and one issued invoice.
let private books () =
    let manifest, r = organization ()
    manifest, r |> customer "CUST-0001" "ABC Corp" |> invoice "INV-1" "CUST-0001" (date 2026 9 15) 605000L

[<Fact>]
let ``SUMMA-T2-R1 SUMMA-T2-R2 a transfer file reads back as the same books`` () =
    let manifest, r = books ()
    let file = Transfer.export manifest r (noon (date 2026 10 7)) |> ok
    let back = Transfer.read file |> ok
    Assert.Equal(Exports.dataVersion r |> ok, back.DataVersion)
    Assert.Equal(Exports.dataVersion r |> ok, Exports.dataVersion back.Books |> ok)
    Assert.Equal("Demo Consulting", back.Manifest.DisplayName)
    Assert.Equal(noon (date 2026 10 7), back.ExportedAt)

[<Fact>]
let ``SUMMA-T2-R2 other JSON is not a transfer file`` () =
    Assert.Equal(Error "This is not a Summa books transfer file.", Transfer.read """{"schema":"summa.invoice-document","version":1}""" |> Result.map ignore)

[<Fact>]
let ``SUMMA-T2-R3 books downloaded in one browser are imported into new books in another`` () =
    let now = noon (date 2026 10 7)
    let manifest, r = books ()
    let here = engine now manifest r |> goTo now Routes.Settings
    let _, effects = run now [ BooksTransferRequested ] here

    let name, mediaType, file = downloads effects |> List.exactlyOne
    Assert.Equal("summa-books-org_local-2026-10-07.json", name)
    Assert.Equal("application/json", mediaType)

    let emptyManifest, empty = organization ()
    let there = engine now emptyManifest empty |> goTo now Routes.Settings
    let imported, effects = run now [ BooksTransferTextChanged file; BooksTransferImported ] there
    Assert.Equal(Some "Books imported from a transfer file exported on 2026-10-07.", imported.Notice)
    Assert.True(imported.Books.Value.Books.Customers.ContainsKey "CUST-0001")
    Assert.Single(effects |> List.filter (function SaveBooks _ -> true | _ -> false)) |> ignore
