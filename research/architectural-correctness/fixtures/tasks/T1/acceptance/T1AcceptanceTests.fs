module T1AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T1-R1 renew extends the loan by 21 days`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-10"
    Assert.Equal("c1 renewed, due 2026-04-13 (renewal 1 of 2)", run w "renew c1")

[<Fact>]
let ``LEND-T1-R1 an overdue loan is not renewed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-24"
    Assert.Equal("error: copy c1 is overdue", run w "renew c1")

[<Fact>]
let ``LEND-T1-R2 the loan listing says whether each loan is renewable`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3"; "hold s1 b2" ] |> List.iter (run w >> ignore)

    Assert.Equal(
        "loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-03-23, renewable\n  c3 \"Emma\" due 2026-03-23, not renewable: book has holds",
        run w "loans m1"
    )
