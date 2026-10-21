module T6AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T6-R1 LEND-T6-R2 a returned copy is set aside for the first hold`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow t1 c2"; "hold s1 b1" ] |> List.iter (run w >> ignore)
    Assert.Equal("c1 returned, set aside for s1 until 2026-03-09", run w "return c1")
    Assert.Equal("error: copy c1 is reserved for another member", run w "borrow m1 c1")
    Assert.Equal("c1 lent to s1, due 2026-03-23", run w "borrow s1 c1")

[<Fact>]
let ``LEND-T6-R3 an uncollected hold expires after its deadline`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow t1 c2"; "hold s1 b1"; "return c1" ] |> List.iter (run w >> ignore)
    Assert.Equal("holds for b1 (Dune):\n  1. s1, copy c1 set aside until 2026-03-09", run w "holds b1")
    w.SetToday "2026-03-09"
    Assert.Equal("expired holds: 0", run w "expire-holds")
    w.SetToday "2026-03-10"
    Assert.Equal("expired holds: 1\n  s1 for b1, copy c1", run w "expire-holds")
    Assert.Equal("c1 lent to m1, due 2026-03-31", run w "borrow m1 c1")
