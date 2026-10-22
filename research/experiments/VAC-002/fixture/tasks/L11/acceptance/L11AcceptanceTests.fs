module L11AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L11-R1 members are exported as CSV`` () =
    let w = seeded "2026-03-02"
    Assert.Equal(
        "id,name,type,status,owes\nm1,Ada Lovelace,standard,active,0.00\ns1,Sam Student,student,active,0.00\nt1,Tess Staff,staff,active,0.00",
        run w "export-members")
