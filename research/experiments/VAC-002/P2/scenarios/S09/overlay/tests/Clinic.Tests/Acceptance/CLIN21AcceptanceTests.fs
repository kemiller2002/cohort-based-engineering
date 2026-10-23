module CLIN21AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-21-R1 urgent priority`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("rx1 prescribed: amoxicillin 500 mg for p1 (urgent)", run w "prescribe rx1 p1 amoxicillin 500 urgent")
    Assert.Equal("rx2 prescribed: ibuprofen 200 mg for p2", run w "prescribe rx2 p2 ibuprofen 200")

[<Fact>]
let ``CLIN-21-R2 urgent prescriptions first in the queue`` () =
    let w = seeded "2026-03-02"
    run w "prescribe rx1 p1 ibuprofen 200" |> ignore
    run w "prescribe rx2 p2 amoxicillin 500 urgent" |> ignore
    Assert.Equal("queue: rx2 (urgent, unchecked), rx1 (unchecked)", run w "queue")
