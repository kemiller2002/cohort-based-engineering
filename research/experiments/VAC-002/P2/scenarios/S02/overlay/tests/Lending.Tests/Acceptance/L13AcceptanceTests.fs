module L13AcceptanceTests

open Xunit
open Support

[<Fact>]
let ``LEND-L13-R1 the member view shows the loan period`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("m1 Ada Lovelace (standard), active, loan period 21 days", run w "member m1")
    run w "suspend m1 \"damaged books\"" |> ignore
    Assert.Equal("m1 Ada Lovelace (standard), suspended: damaged books, loan period 21 days", run w "member m1")
