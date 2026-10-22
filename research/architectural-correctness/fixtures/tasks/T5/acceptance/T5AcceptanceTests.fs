module T5AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-T5-R1 fines lists what a member owes`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    Assert.Equal("fines for m1 (Ada Lovelace):\n  c1 0.75 assessed 2026-03-26\nowed: 0.75", run w "fines m1")
    Assert.Equal("no fines for s1 (Sam Student)", run w "fines s1")

[<Fact>]
let ``LEND-T5-R2 a waived fine is marked and not owed`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    Assert.Equal("fine for c1 waived by Mira Manager", run w "waive m1 c1 \"Mira Manager\"")
    Assert.Equal("fines for m1 (Ada Lovelace):\n  c1 0.75 assessed 2026-03-26, waived by Mira Manager\nowed: 0.00", run w "fines m1")
