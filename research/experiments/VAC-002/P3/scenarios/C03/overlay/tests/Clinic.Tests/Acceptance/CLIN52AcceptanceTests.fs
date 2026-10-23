module CLIN52AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-52-R1 the visit fee of an appointment`` () =
    let w = seeded "2026-03-02"
    run w "book a1 p1 k1 2026-03-12 09:00" |> ignore
    Assert.Equal("a1 visit fee 60.00", run w "fee a1")
    Assert.Equal("error: unknown appointment a9", run w "fee a9")

[<Fact>]
let ``CLIN-52-R2 help lists fee after cancel`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "cancel <appointment>") lines + 1, List.findIndex ((=) "fee <appointment>") lines)
