module CLIN24AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-24-R1 approved double-booking`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("a1 booked: p1 with k2 on 2026-03-09 at 09:00", run w "book a1 p1 k2 2026-03-09 09:00")
    Assert.Equal("a2 booked: p2 with k2 on 2026-03-09 at 09:00 (double-booked)", run w "book a2 p2 k2 2026-03-09 09:00")

[<Fact>]
let ``CLIN-24-R2 schedule marks double-booked times`` () =
    let w = seeded "2026-03-02"
    run w "book a1 p1 k2 2026-03-09 09:00" |> ignore
    run w "book a2 p2 k2 2026-03-09 09:00" |> ignore
    Assert.Equal("k2 on 2026-03-09: 09:00 a1 p1 (double-booked), 09:00 a2 p2 (double-booked)", run w "schedule k2 2026-03-09")
