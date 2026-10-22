module L06AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L06-R1 LEND-L06-R2 a branch manager waives a fine`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    Assert.Equal("error: Bob Smith is not a branch manager", run w "waive c1 \"Bob Smith\"")
    Assert.Equal("fine for c1 of 0.75 (2026-03-26) waived by Grace Hopper", run w "waive c1 \"Grace Hopper\"")
    Assert.Equal("fines for m1:\n  c1 2026-03-26 0.75, paid 0.00, waived by Grace Hopper", run w "fines m1")
    Assert.Equal("error: no fine to waive for c1", run w "waive c1 \"Alan Turing\"")
