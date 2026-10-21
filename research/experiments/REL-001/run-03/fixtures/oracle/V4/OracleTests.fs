module OracleV4

open Xunit
open Ledger

let cash = AccountId "cash"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let holding amount = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash amount "seed" |> ok
let ledgerOf (accounts: (string * decimal) list) =
    accounts
    |> List.fold
        (fun l (name, amount) ->
            let opened = Ledger.openAccount (AccountId name) l |> ok
            if amount > 0m then Ledger.credit (AccountId name) amount "seed" opened |> ok else opened)
        Ledger.empty

[<Fact>]
let ``LEDGER-V4-R1 periodFee keeps the small-balance rule`` () =
    Assert.Equal(0m, Ledger.periodFee 0m)
    Assert.Equal(0m, Ledger.periodFee 0.99m)
    Assert.Equal(1m, Ledger.periodFee 1m)
    Assert.Equal(1m, Ledger.periodFee 5m)

[<Fact>]
let ``LEDGER-V4-R1 the preview follows the balance`` () =
    Assert.Equal(Ok 1m, Ledger.feeFor cash (holding 10m))
    Assert.Equal(Ok 0m, Ledger.feeFor cash (holding 0.5m))
    Assert.Equal(Error(UnknownAccount ghost), Ledger.feeFor ghost (holding 10m))

[<Fact>]
let ``LEDGER-V4-R1 closePeriod charges periodFee of each small balance`` () =
    let l = ledgerOf [ ("a", 0.5m); ("b", 1m); ("c", 20m) ]
    let summary, closed = Ledger.closePeriod "P1" l |> ok
    Assert.Equal(0m, summary.Fees.[AccountId "a"])
    Assert.Equal(1m, summary.Fees.[AccountId "b"])
    Assert.Equal(Ok 19m, Ledger.balance (AccountId "c") closed)

[<Fact>]
let ``LEDGER-V4-R2 periodFee implements the new table`` () =
    Assert.Equal(1m, Ledger.periodFee 999.99m)
    Assert.Equal(0m, Ledger.periodFee 1000m)
    Assert.Equal(0m, Ledger.periodFee 2500m)

[<Fact>]
let ``LEDGER-V4-R2 the preview follows the new rule`` () =
    Assert.Equal(Ok 0m, Ledger.feeFor cash (holding 1000m))
    Assert.Equal(Ok 1m, Ledger.feeFor cash (holding 999.99m))
    Assert.Equal(Ok 0m, Ledger.feeFor cash (holding 5000m))

[<Fact>]
let ``LEDGER-V4-R2 preview and close agree for every balance`` () =
    let l = ledgerOf [ ("a", 0.5m); ("b", 1m); ("c", 999.99m); ("d", 1000m); ("e", 2500m); ("f", 0m) ]
    let previews = [ "a"; "b"; "c"; "d"; "e"; "f" ] |> List.map (fun n -> n, Ledger.feeFor (AccountId n) l |> ok)
    let summary, _ = Ledger.closePeriod "P1" l |> ok
    Assert.True((previews = [ ("a", 0m); ("b", 1m); ("c", 1m); ("d", 0m); ("e", 0m); ("f", 0m) ]))
    previews |> List.iter (fun (n, fee) -> Assert.Equal(fee, summary.Fees.[AccountId n]))

[<Fact>]
let ``LEDGER-V4-R2 only paying accounts get a fee posting`` () =
    let l = ledgerOf [ ("a", 0.5m); ("b", 1m); ("c", 999.99m); ("d", 1000m); ("e", 2500m) ]
    let summary, closed = Ledger.closePeriod "P1" l |> ok
    let feePostings = Ledger.postings closed |> List.filter (fun p -> p.Reference = "fee:P1")
    Assert.True((feePostings |> List.map (fun p -> p.Account, p.Amount) = [ (AccountId "b", -1m); (AccountId "c", -1m) ]))
    Assert.Equal(5, summary.Fees.Count)
    Assert.Equal(Ok 1000m, Ledger.balance (AccountId "d") closed)

[<Fact>]
let ``LEDGER-V4-R2 a repeated close records nothing`` () =
    let first, once = Ledger.closePeriod "P1" (holding 10m) |> ok
    let second, twice = Ledger.closePeriod "P1" once |> ok
    Assert.True((first = second))
    Assert.True((Ledger.postings once = Ledger.postings twice))
