module T1FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T1-F1 a staff loan may be renewed four times`` () =
    let w = seeded "2026-03-02"
    run w "borrow t1 c1" |> ignore
    Assert.Equal("c1 renewed, due 2026-04-13 (renewal 1 of 4)", run w "renew c1")

[<Fact>]
let ``LEND-T1-F1 a student loan may be renewed once`` () =
    let w = seeded "2026-03-02"
    [ "borrow s1 c1"; "renew c1" ] |> List.iter (run w >> ignore)
    Assert.Equal("error: copy c1 has already been renewed 1 times", run w "renew c1")
    Assert.Equal("loans for s1 (Sam Student):\n  c1 \"Dune\" due 2026-04-13, not renewable: renewed 1 of 1 times", run w "loans s1")
