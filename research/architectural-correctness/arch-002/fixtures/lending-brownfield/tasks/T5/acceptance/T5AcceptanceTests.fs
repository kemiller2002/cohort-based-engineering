module T5AcceptanceTests

open Xunit
open Support

/// m1 is fined 0.75 for c1 (returned 2026-03-26) and 2.50 for c3 (returned 2026-04-02).
let fined () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    w.SetToday "2026-04-02"
    run w "return c3" |> ignore
    w

[<Fact>]
let ``LEND2-T5-R1 the account shows what each fine has been paid`` () =
    let w = fined ()
    run w "pay m1 1.00" |> ignore

    Assert.Equal(
        "account for m1 (Ada Lovelace):\n  fine c1 0.75 assessed 2026-03-26, paid\n  fine c3 2.50 assessed 2026-04-02, paid 0.25 of 2.50\n  paid 1.00\nowed: 2.25\nloans: 0 of 5",
        run w "account m1"
    )

[<Fact>]
let ``LEND2-T5-R2 pay names the fines it settles`` () =
    let w = fined ()
    Assert.Equal("m1 paid 1.00, owes 2.25 (settled c1)", run w "pay m1 1.00")
    Assert.Equal("m1 paid 0.25, owes 2.00", run w "pay m1 0.25")
