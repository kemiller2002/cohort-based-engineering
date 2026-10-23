// Post-hoc probe (VAC-002-P2 amendment A5): not part of the frozen oracle. Written after the blinded review flagged
// S07-D. DEC-B02 defines the balance as the sum outstanding on invoices; a credit that covers an invoice leaves
// nothing outstanding on it, so DEC-B03 charges it no late fee.
module OracleTests

open Xunit
open OracleSupport

[<Fact>]
let ``PROBE S07-A5 a fully credited invoice incurs no late fee`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c1 100.00" |> ignore
    run w "credit c1 100.00" |> ignore
    w.SetToday "2026-04-02"
    run w "run-late-fees" |> ignore
    Assert.Equal("c1 balance 0.00", run w "balance c1")

[<Fact>]
let ``PROBE S07-A5 the balance equals the outstanding shown on the customer's invoices`` () =
    let w = seeded "2026-03-02"
    run w "invoice i1 c3 80.00" |> ignore
    run w "credit c3 30.00" |> ignore
    let shown = run w "show i1"
    let outstanding = decimal ((shown.Split(", ") |> Array.find (fun p -> p.StartsWith "outstanding ")).Substring 12)
    Assert.Equal($"c3 balance {outstanding:F2}", run w "balance c3")
