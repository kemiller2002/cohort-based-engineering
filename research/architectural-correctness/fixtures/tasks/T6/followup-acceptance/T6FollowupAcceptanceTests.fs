module T6FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T6-F1 an expired hold's copy goes to the next member`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow t1 c2"; "hold s1 b1"; "hold m1 b1"; "return c1" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-10"
    Assert.Equal("expired holds: 1\n  s1 for b1, copy c1, now set aside for m1 until 2026-03-17", run w "expire-holds")
    Assert.Equal("holds for b1 (Dune):\n  1. m1, copy c1 set aside until 2026-03-17", run w "holds b1")

[<Fact>]
let ``LEND-T6-F2 a hold on a book with a copy on the shelf sets it aside`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("s1 holds b2 at position 1", run w "hold s1 b2")
    Assert.Equal("holds for b2 (Emma):\n  1. s1, copy c3 set aside until 2026-03-09", run w "holds b2")
