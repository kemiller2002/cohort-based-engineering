module L12AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L12-R1 a student borrows for 14 days`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("c1 lent to s1, due 2026-03-16", run w "borrow s1 c1")
    Assert.Equal("c2 lent to m1, due 2026-03-23", run w "borrow m1 c2")

[<Fact>]
let ``LEND-L12-R2 periods lists the loan periods`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("loan periods: standard 21 days, student 14 days, staff 42 days", run w "periods")
