module CLIN22AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-22-R1 follow-up kind`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("a1 booked: p1 with k1 on 2026-03-10 at 09:00 (follow-up)", run w "book a1 p1 k1 2026-03-10 09:00 follow-up")
    Assert.Equal("a2 booked: p2 with k1 on 2026-03-10 at 09:30", run w "book a2 p2 k1 2026-03-10 09:30 regular")
    Assert.Equal("k1 on 2026-03-10: 09:00 a1 p1 (follow-up), 09:30 a2 p2", run w "schedule k1 2026-03-10")
