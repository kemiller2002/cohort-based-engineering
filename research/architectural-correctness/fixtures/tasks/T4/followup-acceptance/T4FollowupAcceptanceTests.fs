module T4FollowupAcceptanceTests

open Xunit
open Lending.Semantic
open Lending.Transition
open Support

[<Fact>]
let ``LEND-T4-F1 LEND-T4-F2 a member's notices go by the channel they chose`` () =
    let w = world "2026-03-02"
    [ "add-member m1 standard Ada"; "add-book b1 1 Dune Herbert"; "add-copy c1 b1"; "borrow m1 c1" ] |> List.iter (run w >> ignore)
    Assert.Equal("m1 will be notified by sms", run w "channel m1 sms")
    w.SetToday "2026-03-25"
    run w "notify-overdue" |> ignore
    Assert.Equal<Channel list>([ Sms ], w.Sent() |> List.map (fun n -> n.Channel))

[<Fact>]
let ``LEND-T4-F3 a rejected sms is sent again by email`` () =
    let w = worldWith "2026-03-02" (fun n -> if n.Channel = Sms then Rejected "no signal" else Delivered)
    [ "add-member m1 standard Ada"; "add-book b1 1 Dune Herbert"; "add-copy c1 b1"; "borrow m1 c1"; "channel m1 sms" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-25"
    Assert.Equal("overdue notices: 1 delivered, 0 failed, 0 unknown\n  c1 to m1: delivered", run w "notify-overdue")
    Assert.Equal<Channel list>([ Sms; Email ], w.Sent() |> List.map (fun n -> n.Channel))
