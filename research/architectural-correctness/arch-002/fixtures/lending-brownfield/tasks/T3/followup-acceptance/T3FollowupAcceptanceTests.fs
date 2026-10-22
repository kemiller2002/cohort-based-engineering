module T3FollowupAcceptanceTests

open System.IO
open Xunit
open Support

[<Fact>]
let ``LEND2-T3-F1 import-copies adds copies at a branch`` () =
    let w = seeded "2026-03-02"
    run w "add-branch east \"East Branch\"" |> ignore
    let path = tempPath "copies.csv"
    File.WriteAllLines(path, [| "copy,book"; "c4,b1"; "c5,b2" |])
    Assert.Equal("imported 2 copies at east", run w $"import-copies east {path}")
    Assert.Equal("copies at east (East Branch):\n  c4 \"Dune\" on shelf\n  c5 \"Emma\" on shelf", run w "shelf east")

[<Fact>]
let ``LEND2-T3-F2 a held book's shelved copies say so`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "hold s1 b1" ] |> List.iter (run w >> ignore)
    let path = tempPath "inventory.csv"
    run w $"export-inventory main {path}" |> ignore

    Assert.Equal<string list>(
        [ "copy,book,title,status"; "c1,b1,Dune,on loan until 2026-03-23"; "c2,b1,Dune,on shelf (1 holds waiting)"; "c3,b2,Emma,on shelf" ],
        File.ReadAllLines path |> List.ofArray
    )
