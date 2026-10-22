module L02AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L02-R1 overdue lists loans past their due date`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    Assert.Equal("overdue loans: 0", run w "overdue")
    w.SetToday "2026-03-26"
    Assert.Equal("overdue loans: 1\n  c1 \"Dune\", m1 Ada Lovelace, due 2026-03-23, 3 days overdue", run w "overdue")
