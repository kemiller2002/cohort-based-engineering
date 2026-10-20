module OracleU5

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () =
    [ a; b; c ] |> List.fold (fun l id -> l |> Ledger.openAccount id |> ok) Ledger.empty |> Ledger.credit a 10m "seed" |> ok
let tx s d amount reference = { Source = s; Destination = d; Amount = amount; Reference = reference }
let balances l = [ a; b; c ] |> List.map (fun id -> Ledger.balance id l |> ok)
let cached store = [ a; b; c ] |> List.map (fun id -> Store.balance id store |> ok)

[<Fact>]
let ``LEDGER-U5-R1 postings equal the individual transfers in order`` () =
    let l0 = setup ()
    let batch = [ tx a b 3m "p1"; tx a c 2m "p2"; tx b c 1m "p3" ]
    let viaBatch = Ledger.transferBatch batch l0 |> ok
    let oneByOne = batch |> List.fold (fun l t -> Ledger.transfer t.Source t.Destination t.Amount t.Reference l |> ok) l0
    Assert.Equal<Posting list>(Ledger.postings oneByOne, Ledger.postings viaBatch)

[<Fact>]
let ``LEDGER-U5-R1 later transfers see earlier ones`` () =
    let l = Ledger.transferBatch [ tx a b 10m "p1"; tx b c 10m "p2" ] (setup ()) |> ok
    Assert.Equal<decimal list>([ 0m; 0m; 10m ], balances l)

[<Fact>]
let ``LEDGER-U5-R1 cumulative overdraft caught mid-batch`` () =
    let l0 = setup ()
    Assert.Equal(Error(BatchFailed(2, InsufficientFunds(a, 4m))), Ledger.transferBatch [ tx a b 4m "p1"; tx a c 4m "p2"; tx a b 4m "p3" ] l0)

[<Fact>]
let ``LEDGER-U5-R1 index and reason of the failing instruction`` () =
    let l0 = setup ()
    Assert.Equal(Error(BatchFailed(1, InvalidAmount 0m)), Ledger.transferBatch [ tx a b 1m "p1"; tx a b 0m "p2" ] l0)
    Assert.Equal(Error(BatchFailed(2, UnknownAccount ghost)), Ledger.transferBatch [ tx a b 1m "p1"; tx a c 1m "p2"; tx a ghost 1m "p3" ] l0)
    Assert.Equal(Error(BatchFailed(1, SameAccount b)), Ledger.transferBatch [ tx a b 1m "p1"; tx b b 1m "p2" ] l0)

[<Fact>]
let ``LEDGER-U5-R1 empty batch records nothing`` () =
    let l0 = setup ()
    let l = Ledger.transferBatch [] l0 |> ok
    Assert.Equal<Posting list>(Ledger.postings l0, Ledger.postings l)

[<Fact>]
let ``LEDGER-U5-R2 mid-batch failure leaves the store unchanged`` () =
    let store = Store.create (setup ())
    let before = Ledger.postings (Store.current store)
    let r = Store.transferBatch [ tx a b 4m "p1"; tx b c 2m "p2"; tx a c 7m "p3"; tx c a 1m "p4" ] store
    Assert.Equal(Error(BatchFailed(2, InsufficientFunds(a, 7m))), r)
    Assert.Equal<Posting list>(before, Ledger.postings (Store.current store))
    Assert.Equal<decimal list>([ 10m; 0m; 0m ], balances (Store.current store))
    Assert.Equal<decimal list>([ 10m; 0m; 0m ], cached store)

[<Fact>]
let ``LEDGER-U5-R2 last instruction failing commits nothing`` () =
    let store = Store.create (setup ())
    let r = Store.transferBatch [ tx a b 1m "p1"; tx a c 1m "p2"; tx c ghost 1m "p3" ] store
    Assert.Equal(Error(BatchFailed(2, UnknownAccount ghost)), r)
    Assert.Equal<decimal list>([ 10m; 0m; 0m ], balances (Store.current store))
    Assert.Equal<decimal list>([ 10m; 0m; 0m ], cached store)

[<Fact>]
let ``LEDGER-U5-R2 successful batch commits everything`` () =
    let store = Store.create (setup ())
    Store.transferBatch [ tx a b 6m "p1"; tx b c 6m "p2"; tx a c 1m "p3" ] store |> ok
    Assert.Equal<decimal list>([ 3m; 0m; 7m ], balances (Store.current store))
    Assert.Equal<decimal list>([ 3m; 0m; 7m ], cached store)
    Assert.Equal(7, List.length (Ledger.postings (Store.current store)))

[<Fact>]
let ``LEDGER-U5-R2 store keeps working after a refused batch`` () =
    let store = Store.create (setup ())
    Assert.True(Result.isError (Store.transferBatch [ tx a b 5m "p1"; tx a b 6m "p2" ] store))
    Store.transferBatch [ tx a b 5m "p3" ] store |> ok
    Assert.Equal<decimal list>([ 5m; 5m; 0m ], balances (Store.current store))
    Assert.Equal<decimal list>([ 5m; 5m; 0m ], cached store)
