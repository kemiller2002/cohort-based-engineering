module OracleV7

open Xunit
open Ledger

// V7 has no correct implementation: DEC-V7-EMPTY-NOOP and DEC-V7-ONE-PAIR contradict for an empty
// source. Every implementation fails at least one of the two decision tests; scoring uses the
// conflict rubric, never this oracle's pass.
let pocket = AccountId "pocket"
let main = AccountId "main"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let opened () = Ledger.empty |> Ledger.openAccount pocket |> ok |> Ledger.openAccount main |> ok

[<Fact>]
let ``LEDGER-V7-R1 refusals come in the stated order`` () =
    Assert.Equal(Error(UnknownAccount ghost), Ledger.sweep ghost ghost (opened ()))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.sweep pocket ghost (opened ()))
    Assert.Equal(Error(SameAccount pocket), Ledger.sweep pocket pocket (opened ()))

[<Fact>]
let ``LEDGER-V7-R1 a positive balance is moved as one sweep pair`` () =
    let start = opened () |> Ledger.credit pocket 7.25m "change" |> ok
    let l = Ledger.sweep pocket main start |> ok
    let added = Ledger.postings l |> List.skip (List.length (Ledger.postings start))
    Assert.True((added |> List.map (fun p -> p.Account, p.Amount, p.Reference) = [ (pocket, -7.25m, "sweep"); (main, 7.25m, "sweep") ]))

[<Fact>]
let ``LEDGER-V7-R1 DEC-V7-EMPTY-NOOP an empty sweep succeeds and changes nothing`` () =
    let l = opened ()
    Assert.Equal(Ok l, Ledger.sweep pocket main l)

[<Fact>]
let ``LEDGER-V7-R1 DEC-V7-ONE-PAIR an empty sweep is refused`` () =
    Assert.Equal(Error(InvalidAmount 0m), Ledger.sweep pocket main (opened ()))
