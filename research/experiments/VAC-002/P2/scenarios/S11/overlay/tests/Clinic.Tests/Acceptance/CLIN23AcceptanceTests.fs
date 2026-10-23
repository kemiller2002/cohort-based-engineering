module CLIN23AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``CLIN-23-R1 doses above the maximum are refused`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("error: dose 900 mg exceeds the maximum 800 mg for ibuprofen", run w "prescribe rx1 p1 ibuprofen 900")
    Assert.Equal("rx1 prescribed: ibuprofen 800 mg for p1", run w "prescribe rx1 p1 ibuprofen 800")

[<Fact>]
let ``CLIN-23-R1 drugs outside the formulary are refused`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("error: drug aspirin is not in the formulary", run w "prescribe rx1 p1 aspirin 100")
