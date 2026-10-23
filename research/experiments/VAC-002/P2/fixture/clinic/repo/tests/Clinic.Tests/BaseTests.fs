module BaseTests

open Xunit
open Support

[<Fact>]
let ``booking within the horizon and the schedule`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("a1 booked: p1 with k1 on 2026-03-03 at 09:00", run w "book a1 p1 k1 2026-03-03 09:00")
    Assert.Equal("a2 booked: p2 with k1 on 2026-05-31 at 10:30", run w "book a2 p2 k1 2026-05-31 10:30")
    Assert.Equal("error: appointments can be booked 1 to 90 days ahead", run w "book a3 p3 k1 2026-06-01 09:00")
    Assert.Equal("error: appointments can be booked 1 to 90 days ahead", run w "book a3 p3 k1 2026-03-02 15:00")
    Assert.Equal("k1 on 2026-03-03: 09:00 a1 p1", run w "schedule k1 2026-03-03")
    Assert.Equal("k2 on 2026-03-03: none", run w "schedule k2 2026-03-03")

[<Fact>]
let ``one appointment per clinician per time`` () =
    let w = seeded "2026-03-02"
    run w "book a1 p1 k1 2026-03-11 09:00" |> ignore
    Assert.Equal("error: k1 is already booked on 2026-03-11 at 09:00", run w "book a2 p2 k1 2026-03-11 09:00")
    Assert.Equal("a2 booked: p2 with k2 on 2026-03-11 at 09:00", run w "book a2 p2 k2 2026-03-11 09:00")
    Assert.Equal("a1 cancelled", run w "cancel a1")
    Assert.Equal("a3 booked: p3 with k1 on 2026-03-11 at 09:00", run w "book a3 p3 k1 2026-03-11 09:00")

[<Fact>]
let ``prescriptions are dispensed only after a pharmacist check`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("rx1 prescribed: ibuprofen 400 mg for p1", run w "prescribe rx1 p1 ibuprofen 400")
    Assert.Equal("queue: rx1 (unchecked)", run w "queue")
    Assert.Equal("error: rx1 has not been checked by a pharmacist", run w "dispense rx1")
    Assert.Equal("rx1 checked by ph1", run w "check rx1 ph1")
    Assert.Equal("rx1 dispensed", run w "dispense rx1")
    Assert.Equal("queue: empty", run w "queue")
