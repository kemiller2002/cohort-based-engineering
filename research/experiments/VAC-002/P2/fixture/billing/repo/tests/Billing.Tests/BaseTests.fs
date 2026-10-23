module BaseTests

open Xunit
open Support

[<Fact>]
let ``invoices are due 30 days after issue`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("i1 issued to c1: 100.00 due 2026-04-01", run w "invoice i1 c1 100.00")
    Assert.Equal("i1 c1 amount 100.00, late fee 0.00, paid 0.00, outstanding 100.00, due 2026-04-01", run w "show i1")

[<Fact>]
let ``unknown customers and invoices are reported`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("error: unknown customer c9", run w "invoice i1 c9 10.00")
    Assert.Equal("error: unknown invoice i9", run w "show i9")
    Assert.Equal("error: invalid amount 1.005", run w "invoice i1 c1 1.005")

[<Fact>]
let ``late fee is 2 percent once, after the due date`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 150.00" |> ignore
    w.SetToday "2026-04-01"
    Assert.Equal("late fees applied: 0", run w "run-late-fees")
    w.SetToday "2026-04-02"
    Assert.Equal("late fees applied: 1", run w "run-late-fees")
    Assert.Equal("late fees applied: 0", run w "run-late-fees")
    Assert.Equal("c1 balance 153.00", run w "balance c1")

[<Fact>]
let ``balance sums outstanding invoices`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 40.00" |> ignore
    run w "invoice i2 c1 2.50" |> ignore
    Assert.Equal("c1 balance 42.50", run w "balance c1")
    Assert.Equal("c3 balance 0.00", run w "balance c3")
