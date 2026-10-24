module T4AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T4-R1 restore brings back the backed-up state`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    let path = tempPath "backup.json"
    run w $"backup {path}" |> ignore
    [ "return c1"; "add-member x1 standard Xavier" ] |> List.iter (run w >> ignore)
    Assert.Equal($"restored 3 members, 2 books, 3 copies, 1 loans from {path}", run w $"restore {path}")
    Assert.Equal("error: copy c1 is already on loan", run w "borrow s1 c1")

[<Fact>]
let ``LEND2-T4-R2 backup-info describes a backup`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "hold s1 b1" ] |> List.iter (run w >> ignore)
    let path = tempPath "backup.json"
    run w $"backup {path}" |> ignore
    Assert.Equal($"backup {path}: 3 members, 2 books, 3 copies, 1 loans, 1 holds, 0.00 owed", run w $"backup-info {path}")

[<Fact>]
let ``LEND2-T4-R3 backup does not overwrite`` () =
    let w = seeded "2026-03-02"
    let path = tempPath "backup.json"
    Assert.Equal($"backed up 3 members, 2 books, 3 copies, 0 loans to {path}", run w $"backup {path}")
    Assert.Equal($"error: {path} already exists", run w $"backup {path}")
