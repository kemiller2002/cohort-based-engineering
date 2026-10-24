module Summa.Acceptance.T3FollowupAcceptanceTests

open Xunit
open Summa.Ledger.Invoicing
open Summa.Web.Engine
open Summa.Web.Engine.Accounting
open Summa.Acceptance.Kit

[<Fact>]
let ``SUMMA-T3-F1 due on the 15th of the month after issue`` () =
    Assert.Equal(date 2026 11 15, dueDate (date 2026 10 7) (DayOfNextMonth 15))
    Assert.Equal(date 2027 1 10, dueDate (date 2026 12 20) (DayOfNextMonth 10))
    Assert.Equal("Due the 15th of next month", Summa.Ledger.Documents.termsText (DayOfNextMonth 15))

[<Fact>]
let ``SUMMA-T3-F2 a customer added on day 15 has those terms`` () =
    let now = noon (date 2026 10 7)
    let manifest, r = organization ()
    let model = engine now manifest r |> goTo now (Routes.Customers Routes.allCustomers)
    let added, _ = run now [ CustomerNameChanged "ABC Corp"; CustomerTermsChanged "day 15"; CustomerAdded ] model
    Assert.Equal(None, added.Error)
    Assert.Equal(Some(DayOfNextMonth 15), added.Books.Value.Books.Customers["CUST-0001"].DefaultTerms)
