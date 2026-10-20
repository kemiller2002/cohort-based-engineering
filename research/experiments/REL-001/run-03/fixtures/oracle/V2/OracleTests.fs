module OracleV2

open Xunit
open Ledger

let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let ledgerOf (accounts: (string * decimal) list) =
    accounts
    |> List.fold
        (fun l (name, amount) ->
            let opened = Ledger.openAccount (AccountId name) l |> ok
            if amount > 0m then Ledger.credit (AccountId name) amount "seed" opened |> ok else opened)
        Ledger.empty

[<Fact>]
let ``LEDGER-V2-R1 equal balances are ordered by id ordinally`` () =
    let l = ledgerOf [ ("a", 5m); ("B", 5m); ("c", 7m); ("Z", 0m) ]
    Assert.Equal(Ok [ (AccountId "c", 7m); (AccountId "B", 5m); (AccountId "a", 5m); (AccountId "Z", 0m) ], Ledger.richest 4 l)

[<Fact>]
let ``LEDGER-V2-R1 zero balances take part and a large count gives every account`` () =
    let l = ledgerOf [ ("y", 0m); ("x", 0m); ("w", 2m) ]
    Assert.Equal(Ok [ (AccountId "w", 2m); (AccountId "x", 0m); (AccountId "y", 0m) ], Ledger.richest 10 l)

[<Fact>]
let ``LEDGER-V2-R1 a count of zero gives an empty list`` () =
    Assert.Equal(Ok [], Ledger.richest 0 (ledgerOf [ ("a", 1m) ]))

[<Fact>]
let ``LEDGER-V2-R1 a negative count is refused with that count`` () =
    Assert.Equal(Error(InvalidCount -3), Ledger.richest -3 (ledgerOf [ ("a", 1m) ]))
    Assert.Equal(Error(InvalidCount -1), Ledger.richest -1 Ledger.empty)

[<Fact>]
let ``LEDGER-V2-R1 current balances decide the order`` () =
    let l = ledgerOf [ ("a", 50m); ("b", 40m) ] |> Ledger.debit (AccountId "a") 20m "spend" |> ok
    Assert.Equal(Ok [ (AccountId "b", 40m) ], Ledger.richest 1 l)

[<Fact>]
let ``LEDGER-V2-R1 an empty ledger gives an empty list`` () =
    Assert.Equal(Ok [], Ledger.richest 3 Ledger.empty)
