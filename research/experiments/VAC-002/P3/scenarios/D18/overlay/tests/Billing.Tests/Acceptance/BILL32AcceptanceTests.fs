module BILL32AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-32-R1 the reminder fee is charged once, more than 30 days after the due date`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    w.SetToday "2026-05-01"
    Assert.Equal("reminder fees applied: 0", run w "run-reminders")
    w.SetToday "2026-05-02"
    Assert.Equal("reminder fees applied: 1", run w "run-reminders")
    Assert.Equal("reminder fees applied: 0", run w "run-reminders")
    Assert.Equal("c1 balance 105.00", run w "balance c1")

[<Fact>]
let ``BILL-32-R2 help lists run-reminders after run-late-fees`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "run-late-fees") lines + 1, List.findIndex ((=) "run-reminders") lines)
