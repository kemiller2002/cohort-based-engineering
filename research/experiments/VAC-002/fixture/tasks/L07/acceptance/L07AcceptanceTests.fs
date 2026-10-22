module L07AcceptanceTests

open Xunit
open Lending.Transition
open Support

[<Fact>]
let ``LEND-L07-R1 an overdue loan is sent one notice`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-30"
    Assert.Equal("notices: 1 sent, 1 delivered, 0 rejected, 0 unknown\n  c1 to m1: delivered", run w "send-notices")
    let notice = List.exactlyOne (w.Sent())
    Assert.Equal("Overdue: Dune", notice.Subject)
    Assert.Equal("Copy c1 of \"Dune\" was due on 2026-03-23.", notice.Body)
    Assert.Equal("notices: 0 sent, 0 delivered, 0 rejected, 0 unknown", run w "send-notices")

[<Fact>]
let ``LEND-L07-R2 an unanswered notice is not sent again`` () =
    let w = worldWith "2026-03-02" (fun _ -> NoAnswer)
    [ "add-member m1 standard Ada"; "add-book b1 1 Dune Herbert"; "add-copy c1 b1"; "borrow m1 c1" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-30"
    Assert.Equal("notices: 1 sent, 0 delivered, 0 rejected, 1 unknown\n  c1 to m1: unknown", run w "send-notices")
    Assert.Equal("notices: 0 sent, 0 delivered, 0 rejected, 0 unknown", run w "send-notices")
    Assert.Equal("unknown notices: 1\n  c1 to m1, sent 2026-03-30", run w "unknown-notices")
