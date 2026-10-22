module L08AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L08-R1 a member's notices are listed newest first`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    Assert.Equal("no notices for m1", run w "notices m1")
    w.SetToday "2026-03-30"
    run w "send-notices" |> ignore
    Assert.Equal("notices for m1:\n  2026-03-30 c1 \"Dune\": delivered", run w "notices m1")
