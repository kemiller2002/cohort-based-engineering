module CLIN53AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-53-R1 an appointment is moved, or refused like a booking`` () =
    let w = seeded "2026-03-02"
    runAll w [ "book a1 p1 k1 2026-03-10 09:00"; "book a2 p2 k1 2026-03-10 11:00" ]
    Assert.Equal("a1 moved to 2026-03-12 at 10:00", run w "move a1 2026-03-12 10:00")
    Assert.Equal("k1 on 2026-03-12: 10:00 a1 p1", run w "schedule k1 2026-03-12")
    Assert.Equal("error: k1 is already booked on 2026-03-12 at 10:00", run w "move a2 2026-03-12 10:00")
    Assert.Equal("error: appointments can be booked 1 to 90 days ahead", run w "move a2 2026-06-30 10:00")
    Assert.Equal("error: unknown appointment a9", run w "move a9 2026-03-12 10:00")

[<Fact>]
let ``CLIN-53-R2 help lists move after cancel`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "cancel <appointment>") lines + 1, List.findIndex ((=) "move <appointment> <date> <time>") lines)
