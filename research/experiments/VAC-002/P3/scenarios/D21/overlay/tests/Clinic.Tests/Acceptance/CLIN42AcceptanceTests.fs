module CLIN42AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-42-R1 checked prescriptions are dispensed in queue order`` () =
    let w = seeded "2026-03-02"
    runAll w [ "prescribe rx1 p1 amoxicillin 500"; "prescribe rx2 p2 ibuprofen 200"; "prescribe rx3 p3 metformin 850"
               "check rx3 ph1"; "check rx1 ph1" ]
    Assert.Equal("dispensed: rx1, rx3", run w "dispense-ready")
    Assert.Equal("queue: rx2 (unchecked)", run w "queue")
    Assert.Equal("dispensed: none", run w "dispense-ready")

[<Fact>]
let ``CLIN-42-R2 help lists dispense-ready after dispense`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "dispense <prescription>") lines + 1, List.findIndex ((=) "dispense-ready") lines)
