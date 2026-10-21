module U4AcceptanceTests

open Xunit
open Ledger

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    Ledger.empty |> Ledger.openAccount cash |> ok
    |> Ledger.credit cash 10m "c1" |> ok |> Ledger.credit cash 5m "c2" |> ok |> Ledger.debit cash 3m "d1" |> ok

let refs (ps: Posting list) = ps |> List.map (fun p -> p.Reference)

[<Fact>]
let ``LEDGER-U4-R1 recent lists the newest postings first`` () =
    Assert.Equal<string list>([ "d1"; "c2" ], Ledger.recent cash 2 (setup ()) |> ok |> refs)

[<Fact>]
let ``LEDGER-U4-R2 a reversed posting is hidden and its effect undone`` () =
    let l = Ledger.reverse "c2" (setup ()) |> ok
    Assert.Equal(Ok 7m, Ledger.balance cash l)
    Assert.Equal<string list>([ "d1"; "c1" ], Ledger.postingsOf cash l |> refs)
