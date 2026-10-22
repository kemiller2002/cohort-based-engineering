module T6FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T6-F1 search one branch`` () =
    let w = seeded "2026-03-02"
    [ "add-branch east \"East Branch\""; "transfer c2 east" ] |> List.iter (run w >> ignore)
    Assert.Equal("1 books match \"dune\" at east:\n  b1 \"Dune\" by Frank Herbert: 1 of 1 copies on shelf at east", run w "search dune east")

[<Fact>]
let ``LEND2-T6-F2 search by isbn`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("1 books match \"9780141439587\":\n  b2 \"Emma\" by Jane Austen: 1 of 1 copies on shelf", run w "search 9780141439587")
