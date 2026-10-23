module BILL15AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``BILL-15-R1 reminder fee more than 30 days after the due date`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    w.SetToday "2026-04-02"
    Assert.Equal("late fees applied: 1, reminder fees applied: 0", run w "run-late-fees")
    w.SetToday "2026-05-02"
    Assert.Equal("late fees applied: 0, reminder fees applied: 1", run w "run-late-fees")

[<Fact>]
let ``BILL-15-R2 show includes the reminder fee`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    w.SetToday "2026-05-10"
    run w "run-late-fees" |> ignore
    Assert.Equal("i1 c1 amount 100.00, late fee 2.00, reminder fee 5.00, paid 0.00, outstanding 107.00, due 2026-04-01", run w "show i1")
