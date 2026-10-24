module Summa.Acceptance.T3AcceptanceTests

open Xunit
open Summa.Ledger.Invoicing
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

[<Fact>]
let ``SUMMA-T3-R1 Net 30 EOM is due thirty days after the end of the month of issue`` () =
    Assert.Equal(date 2026 11 30, dueDate (date 2026 10 7) (NetEndOfMonth 30))
    Assert.Equal("Net 30 EOM", Summa.Ledger.Documents.termsText (NetEndOfMonth 30))

[<Fact>]
let ``SUMMA-T3-R2 end-of-month terms are kept with the books`` () =
    let manifest, r = organization ()
    let r = r |> customer "CUST-0001" "ABC Corp" |> invoiceWith (Some(NetEndOfMonth 30)) "INV-1" "CUST-0001" (date 2026 10 7) 100000L
    let restored = Summa.Storage.LocalSnapshot.decode (Summa.Storage.LocalSnapshot.encode manifest r |> ok) |> ok
    Assert.Empty restored.Problems
    Assert.Equal(NetEndOfMonth 30, restored.Books.Books.Invoices["INV-1"].Terms)
    Assert.Equal(date 2026 11 30, restored.Books.Books.Invoices["INV-1"].DueDate)

[<Fact>]
let ``SUMMA-T3-R3 a customer added on 30 EOM has those terms`` () =
    let now = noon (date 2026 10 7)
    let manifest, r = organization ()
    let model = engine now manifest r |> goTo now (Routes.Customers Routes.allCustomers)
    let added, _ = run now [ CustomerNameChanged "ABC Corp"; CustomerTermsChanged "30 EOM"; CustomerAdded ] model
    Assert.Equal(None, added.Error)
    Assert.Equal(Some(NetEndOfMonth 30), added.Books.Value.Books.Customers["CUST-0001"].DefaultTerms)
