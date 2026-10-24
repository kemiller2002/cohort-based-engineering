module T2AcceptanceTests

open Xunit
open Support

/// m1 returns c1 21 days late: a fine of 5.25.
let blocked () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-04-13"
    run w "return c1" |> ignore
    w

[<Fact>]
let ``LEND2-T2-R1 a blocked member cannot borrow or place holds`` () =
    let w = blocked ()
    Assert.Equal("error: member m1 owes 5.25; borrowing is blocked until it is below 5.00", run w "borrow m1 c2")
    Assert.Equal("error: member m1 owes 5.25; holds are blocked until it is below 5.00", run w "hold m1 b2")

[<Fact>]
let ``LEND2-T2-R2 a blocked member cannot renew`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-04-13"
    run w "return c1" |> ignore
    Assert.Equal("error: member m1 owes 5.25; renewals are blocked until it is below 5.00", run w "renew c3")

[<Fact>]
let ``LEND2-T2-R3 standing shows where a member stands`` () =
    let w = blocked ()
    Assert.Equal("m1 (Ada Lovelace) owes 5.25: blocked from borrowing, holds and renewals", run w "standing m1")
    run w "pay m1 0.50" |> ignore
    Assert.Equal("m1 (Ada Lovelace) owes 4.75: in good standing", run w "standing m1")

[<Fact>]
let ``LEND2-T2-R4 members marks blocked members`` () =
    let w = blocked ()

    Assert.Equal(
        "3 members:\n  m1 Ada Lovelace (standard), 0 loans, blocked\n  s1 Sam Student (student), 0 loans\n  t1 Tess Staff (staff), 0 loans",
        run w "members"
    )
