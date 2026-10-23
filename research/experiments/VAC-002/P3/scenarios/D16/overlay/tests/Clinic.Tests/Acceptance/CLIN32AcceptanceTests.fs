module CLIN32AcceptanceTests

open Xunit
open Support

let dispensed (w: W) =
    runAll w [ "prescribe rx1 p1 amoxicillin 500"; "check rx1 ph1"; "dispense rx1" ]

[<Fact>]
let ``CLIN-32-R1 a dispensed prescription is repeated`` () =
    let w = seeded "2026-03-02"
    dispensed w
    Assert.Equal("rx2 repeats rx1: amoxicillin 500 mg for p1", run w "repeat rx1 rx2")

[<Fact>]
let ``CLIN-32-R1 only dispensed prescriptions are repeated`` () =
    let w = seeded "2026-03-02"
    run w "prescribe rx1 p1 amoxicillin 500" |> ignore
    Assert.Equal("error: rx1 has not been dispensed", run w "repeat rx1 rx2")

[<Fact>]
let ``CLIN-32-R2 help lists repeat after dispense`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "dispense <prescription>") lines + 1, List.findIndex ((=) "repeat <prescription> <new-prescription>") lines)
