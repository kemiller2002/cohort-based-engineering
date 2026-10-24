module T4FollowupAcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND2-T4-F1 restore-member brings back one member`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    let path = tempPath "backup.json"
    run w $"backup {path}" |> ignore
    let other = world "2026-03-30"
    Assert.Equal($"restored member m1 (Ada Lovelace) with 1 fines and 0 payments from {path}", run other $"restore-member {path} m1")
    Assert.Equal("1 members:\n  m1 Ada Lovelace (standard), 0 loans", run other "members")
