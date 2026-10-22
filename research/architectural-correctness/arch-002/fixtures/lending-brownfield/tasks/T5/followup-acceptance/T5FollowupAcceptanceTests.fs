module T5FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T5-F1 a waived fine is marked and not owed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    Assert.Equal("fine for c1 waived by Mira Manager", run w "waive m1 c1 \"Mira Manager\"")

    Assert.Equal(
        "account for m1 (Ada Lovelace):\n  fine c1 0.75 assessed 2026-03-26, waived by Mira Manager\nowed: 0.00\nloans: 0 of 5",
        run w "account m1"
    )
