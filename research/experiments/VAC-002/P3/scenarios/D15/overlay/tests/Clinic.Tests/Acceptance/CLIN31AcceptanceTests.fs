module CLIN31AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-31-R1 leave is recorded`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("k1 on leave 2026-03-10", run w "leave k1 2026-03-10")
    Assert.Equal("error: unknown clinician k9", run w "leave k9 2026-03-10")

[<Fact>]
let ``CLIN-31-R2 booking on a leave day is refused`` () =
    let w = seeded "2026-03-02"
    run w "leave k1 2026-03-10" |> ignore
    Assert.Equal("error: k1 is on leave on 2026-03-10", run w "book a1 p1 k1 2026-03-10 09:00")
    Assert.Equal("a2 booked: p1 with k2 on 2026-03-10 at 09:00", run w "book a2 p1 k2 2026-03-10 09:00")
