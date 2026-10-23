module LateFeeExemptionTests

open Xunit
open Support

[<Fact>]
let ``premium customers are not charged late fees (DEC-B05)`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c3 100.00" |> ignore
    w.SetToday "2026-04-10"
    Assert.Equal("late fees applied: 0", run w "run-late-fees")
    Assert.Equal("c3 balance 100.00", run w "balance c3")
