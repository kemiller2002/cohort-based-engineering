module L10AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L10-R1 LEND-L10-R2 a returned copy is set aside for the first hold`` () =
    let w = seeded "2026-04-27"
    [ "borrow m1 c1"; "borrow t1 c2"; "hold s1 b1" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-05-18"
    Assert.Equal("c1 returned, set aside for s1 until 2026-05-26", run w "return c1")
    Assert.Equal("error: copy c1 is reserved for another member", run w "borrow m1 c1")
    Assert.Equal("holds for b1 (Dune):\n  1. s1, copy c1 set aside until 2026-05-26", run w "holds b1")

[<Fact>]
let ``LEND-L10-R3 an uncollected hold expires after its deadline`` () =
    let w = seeded "2026-04-27"
    [ "borrow m1 c1"; "borrow t1 c2"; "hold s1 b1" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-05-18"
    run w "return c1" |> ignore
    w.SetToday "2026-05-26"
    Assert.Equal("expired holds: 0", run w "expire-holds")
    w.SetToday "2026-05-27"
    Assert.Equal("expired holds: 1\n  s1 for b1, copy c1", run w "expire-holds")
    Assert.Equal("no holds for b1 (Dune)", run w "holds b1")
