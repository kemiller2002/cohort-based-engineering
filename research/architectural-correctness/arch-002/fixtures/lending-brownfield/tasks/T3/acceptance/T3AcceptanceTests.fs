module T3AcceptanceTests

open System.IO
open Xunit
open Support

let read path = File.ReadAllLines path |> List.ofArray

[<Fact>]
let ``LEND2-T3-R1 export-inventory writes a branch's copies`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    let path = tempPath "inventory.csv"
    Assert.Equal($"exported 3 copies at main to {path}", run w $"export-inventory main {path}")

    Assert.Equal<string list>(
        [ "copy,book,title,status"; "c1,b1,Dune,on loan until 2026-03-23"; "c2,b1,Dune,on shelf"; "c3,b2,Emma,on shelf" ],
        read path
    )

[<Fact>]
let ``LEND2-T3-R2 export-holds writes the queues`` () =
    let w = seeded "2026-03-02"
    run w "hold s1 b1" |> ignore
    w.SetToday "2026-03-04"
    run w "hold m1 b1" |> ignore
    let path = tempPath "holds.csv"
    Assert.Equal($"exported 2 holds to {path}", run w $"export-holds {path}")
    Assert.Equal<string list>([ "book,position,member,since"; "b1,1,s1,2026-03-02"; "b1,2,m1,2026-03-04" ], read path)

[<Fact>]
let ``LEND2-T3-R3 export-members writes what import-members reads`` () =
    let w = seeded "2026-03-02"
    let path = tempPath "members.csv"
    Assert.Equal($"exported 3 members to {path}", run w $"export-members {path}")

    Assert.Equal<string list>(
        [ "member,type,name"; "m1,standard,Ada Lovelace"; "s1,student,Sam Student"; "t1,staff,Tess Staff" ],
        read path
    )
