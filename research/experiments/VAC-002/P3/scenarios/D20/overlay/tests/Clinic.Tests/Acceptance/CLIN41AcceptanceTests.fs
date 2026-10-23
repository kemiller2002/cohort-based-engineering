module CLIN41AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-41-R1 the first free day from tomorrow`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("k1 free at 09:00 on 2026-03-03", run w "next-free k1 09:00")
    run w "book a1 p1 k1 2026-03-03 09:00" |> ignore
    Assert.Equal("k1 free at 09:00 on 2026-03-04", run w "next-free k1 09:00")
    Assert.Equal("error: unknown clinician k9", run w "next-free k9 09:00")

[<Fact>]
let ``CLIN-41-R2 help lists next-free after schedule`` () =
    let w = seeded "2026-03-02"
    let lines = helpLines w
    Assert.Equal(List.findIndex ((=) "schedule <clinician> <date>") lines + 1, List.findIndex ((=) "next-free <clinician> <time>") lines)
