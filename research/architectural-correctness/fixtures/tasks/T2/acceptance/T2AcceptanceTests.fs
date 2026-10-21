module T2AcceptanceTests

open Xunit
open Lending.Host.Persistence
open Support

[<Fact>]
let ``LEND-T2-R1 LEND-T2-R2 a return is listed in the member's history`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow m1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore

    Assert.Equal(
        "history for m1 (Ada Lovelace):\n  c1 \"Dune\" borrowed 2026-03-02, due 2026-03-23, returned 2026-03-26, 3 days late",
        run w "history m1"
    )

[<Fact>]
let ``LEND-T2-R2 a member without finished loans has no history`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("no history for s1 (Sam Student)", run w "history s1")

[<Fact>]
let ``LEND-T2-R3 the json file store keeps the history`` () =
    let path = System.IO.Path.GetTempFileName()

    try
        let w = seeded "2026-03-02"
        run w "borrow m1 c1" |> ignore
        run w "return c1" |> ignore
        (JsonFileStore.create path).Save(w.Ports.Store.Load())
        let reopened = { w with Ports = { w.Ports with Store = JsonFileStore.create path } }

        Assert.Equal(
            "history for m1 (Ada Lovelace):\n  c1 \"Dune\" borrowed 2026-03-02, due 2026-03-23, returned 2026-03-02, on time",
            run reopened "history m1"
        )
    finally
        System.IO.File.Delete path
