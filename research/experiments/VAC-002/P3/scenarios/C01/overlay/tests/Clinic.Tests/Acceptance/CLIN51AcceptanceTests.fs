module CLIN51AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-51-R1 a day without reminders`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("reminders on 2026-03-10: none", run w "reminders 2026-03-10")
    run w "book a1 p1 k1 2026-03-20 09:00" |> ignore
    Assert.Equal("reminders on 2026-03-25: none", run w "reminders 2026-03-25")

[<Fact>]
let ``CLIN-51-R2 help lists reminders after reminder`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "reminder <appointment>") lines + 1, List.findIndex ((=) "reminders <date>") lines)
