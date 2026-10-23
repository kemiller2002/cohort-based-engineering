module ReminderTests

open Xunit
open Support

[<Fact>]
let ``a reminder is sent before the appointment`` () =
    let w = seeded "2026-03-02"
    run w "book a1 p1 k1 2026-03-12 09:00" |> ignore
    Assert.Equal("a1 reminder at 2026-03-11 09:00", run w "reminder a1")
    Assert.Equal("error: unknown appointment a9", run w "reminder a9")
