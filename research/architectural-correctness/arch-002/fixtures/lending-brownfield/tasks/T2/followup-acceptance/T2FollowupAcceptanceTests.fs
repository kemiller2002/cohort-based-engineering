module T2FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T2-F1 a student is blocked from 2.00`` () =
    let w = seeded "2026-03-02"
    run w "borrow s1 c1" |> ignore
    w.SetToday "2026-04-01"
    run w "return c1" |> ignore
    Assert.Equal("error: member s1 owes 2.25; borrowing is blocked until it is below 2.00", run w "borrow s1 c2")
    Assert.Equal("s1 (Sam Student) owes 2.25: blocked from borrowing, holds and renewals", run w "standing s1")

[<Fact>]
let ``LEND2-T2-F1 staff are blocked from 10.00`` () =
    let w = seeded "2026-03-02"
    run w "borrow t1 c1" |> ignore
    w.SetToday "2026-04-13"
    run w "return c1" |> ignore
    Assert.Equal("t1 (Tess Staff) owes 5.25: in good standing", run w "standing t1")
