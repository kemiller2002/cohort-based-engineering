module L09AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L09-R1 a due date on a public holiday moves to the next open day`` () =
    let w = seeded "2026-05-04"
    Assert.Equal("c1 lent to m1, due 2026-05-26", run w "borrow m1 c1")

[<Fact>]
let ``LEND-L09-R2 open reports the calendar`` () =
    let w = seeded "2026-05-04"
    Assert.Equal("2026-05-25 is closed; next open day 2026-05-26", run w "open 2026-05-25")
    Assert.Equal("2026-05-26 is open", run w "open 2026-05-26")
