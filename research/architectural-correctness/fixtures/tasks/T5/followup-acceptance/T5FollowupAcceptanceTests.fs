module T5FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T5-F1 a staff fine is waived when it is assessed`` () =
    let w = seeded "2026-03-02"
    run w "borrow t1 c1" |> ignore
    w.SetToday "2026-03-26"
    Assert.Equal("c1 returned 3 days late, fine 0.75 (waived by DEC-006 rev 2)", run w "return c1")
    Assert.Equal("fines for t1 (Tess Staff):\n  c1 0.75 assessed 2026-03-26, waived by DEC-006 rev 2\nowed: 0.00", run w "fines t1")
