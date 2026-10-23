module L14AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L14-R1 estimates for loans that are not overdue, and refusals`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    Assert.Equal("c1 estimate 0.00", run w "estimate c1")
    Assert.Equal("error: copy c2 is not on loan", run w "estimate c2")
    Assert.Equal("error: unknown copy c9", run w "estimate c9")

[<Fact>]
let ``LEND-L14-R1 help lists estimate after renew`` () =
    let w = seeded "2026-03-02"
    let lines = (run w "help").Split('\n') |> Array.toList
    Assert.Equal(List.findIndex ((=) "renew <copy>") lines + 1, List.findIndex ((=) "estimate <copy>") lines)
