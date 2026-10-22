module T1AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T1-R1 the loan listing says whether each loan is renewable`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3"; "hold s1 b2" ] |> List.iter (run w >> ignore)

    Assert.Equal(
        "loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-03-23, renewable\n  c3 \"Emma\" due 2026-03-23, not renewable: book has holds",
        run w "loans m1"
    )

[<Fact>]
let ``LEND2-T1-R2 renew reports the renewal count`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-10"
    Assert.Equal("c1 renewed, due 2026-04-13 (renewal 1 of 2)", run w "renew c1")
    Assert.Equal("c1 renewed, due 2026-05-04 (renewal 2 of 2)", run w "renew c1")
    Assert.Equal("error: copy c1 has already been renewed 2 times", run w "renew c1")

[<Fact>]
let ``LEND2-T1-R3 renew-all renews what it can`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3"; "hold s1 b2" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-10"

    Assert.Equal(
        "c1 renewed, due 2026-04-13 (renewal 1 of 2)\nc3 not renewed: book has holds\nrenewed 1 of 2 loans for m1",
        run w "renew-all m1"
    )
