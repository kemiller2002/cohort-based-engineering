module T6AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T6-R1 search finds books by title or author`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore

    Assert.Equal(
        "2 books match \"e\":\n  b1 \"Dune\" by Frank Herbert: 1 of 2 copies on shelf\n  b2 \"Emma\" by Jane Austen: 1 of 1 copies on shelf",
        run w "search e"
    )

    Assert.Equal("no books match \"xyz\"", run w "search xyz")

[<Fact>]
let ``LEND2-T6-R2 copies shows where each copy is`` () =
    let w = seeded "2026-03-02"
    [ "add-branch east \"East Branch\""; "transfer c2 east"; "borrow m1 c1" ] |> List.iter (run w >> ignore)
    Assert.Equal("copies of b1 (Dune):\n  c1 at main, on loan, due 2026-03-23\n  c2 at east, on shelf", run w "copies b1")

[<Fact>]
let ``LEND2-T6-R3 branches counts copies`` () =
    let w = seeded "2026-03-02"
    [ "add-branch east \"East Branch\""; "transfer c2 east"; "borrow m1 c1" ] |> List.iter (run w >> ignore)
    Assert.Equal("branches:\n  east East Branch: 1 copies, 1 on shelf\n  main Main Library: 2 copies, 1 on shelf", run w "branches")
