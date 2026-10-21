module T4AcceptanceTests

open Xunit
open Lending.Semantic
open Lending.Transition
open Support

let answers (byMember: (string * DeliveryReport) list) (notice: Notice) =
    byMember |> List.tryFind (fun (m, _) -> MemberId m = notice.Recipient) |> Option.map snd |> Option.defaultValue Delivered

let lending (w: World) =
    [ "add-member m1 standard \"Ada Lovelace\""; "add-member s1 student \"Sam Student\""; "add-member t1 staff \"Tess Staff\""
      "add-book b1 9780441013593 Dune \"Frank Herbert\""; "add-copy c1 b1"; "add-copy c2 b1"; "add-copy c3 b1"
      "borrow m1 c1"; "borrow s1 c2"; "borrow t1 c3" ]
    |> List.iter (run w >> ignore)

[<Fact>]
let ``LEND-T4-R1 LEND-T4-R2 each overdue loan gets one notice and its outcome`` () =
    let w = worldWith "2026-03-02" (answers [ "s1", Rejected "mailbox full"; "t1", NoAnswer ])
    lending w
    w.SetToday "2026-03-25"

    Assert.Equal(
        "overdue notices: 1 delivered, 1 failed, 1 unknown\n  c1 to m1: delivered\n  c2 to s1: failed (mailbox full)\n  c3 to t1: unknown, needs reconciliation",
        run w "notify-overdue"
    )

    Assert.Equal("Overdue: Dune", (List.head (w.Sent())).Subject)

[<Fact>]
let ``LEND-T4-R3 an unknown outcome is not sent again until reconciled`` () =
    let w = worldWith "2026-03-02" (answers [ "s1", Rejected "mailbox full"; "t1", NoAnswer ])
    lending w
    w.SetToday "2026-03-25"
    run w "notify-overdue" |> ignore
    Assert.Equal("awaiting reconciliation:\n  c3 to t1, sent 2026-03-25", run w "obligations")
    Assert.Equal("overdue notices: 0 delivered, 1 failed, 0 unknown\n  c2 to s1: failed (mailbox full)", run w "notify-overdue")
