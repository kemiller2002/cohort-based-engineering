module OracleV5

open System
open Xunit
open Ledger

let cash = AccountId "cash"
let savings = AccountId "savings"
let landlord = AccountId "landlord"
let ghost = AccountId "ghost"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let funded () =
    Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.openAccount savings |> ok |> Ledger.openAccount landlord |> ok
    |> Ledger.credit cash 100m "salary" |> ok
let between id payer payee day value = { OrderId = id; Payer = payer; Payee = payee; Value = value; DayOfMonth = day }
let order id day value = between id cash landlord day value
let date y m d = DateOnly(y, m, d)
let run d orders l = StandingOrders.run d orders l
let outcomesOn d orders = run d orders (funded ()) |> ok |> fst

[<Fact>]
let ``LEDGER-V5-R1 a non-positive value, a bad day and a repeated id are refused`` () =
    Assert.Equal(Error(InvalidOrder "a"), run (date 2026 1 15) [ order "a" 15 -5m ] (funded ()))
    Assert.Equal(Error(InvalidOrder "a"), run (date 2026 1 15) [ order "a" 0 5m ] (funded ()))
    Assert.Equal(Error(InvalidOrder "a"), run (date 2026 1 15) [ order "a" 32 5m ] (funded ()))
    Assert.Equal(Error(InvalidOrder "x"), run (date 2026 1 15) [ order "x" 15 5m; order "y" 3 5m; order "x" 20 5m ] (funded ()))

[<Fact>]
let ``LEDGER-V5-R1 an order that is not due is still checked`` () =
    Assert.Equal(Error(InvalidOrder "b"), run (date 2026 1 15) [ order "a" 15 5m; order "b" 20 0m ] (funded ()))

[<Fact>]
let ``LEDGER-V5-R1 the first invalid order in list order is named`` () =
    Assert.Equal(Error(InvalidOrder "z"), run (date 2026 1 15) [ order "z" 15 0m; order "a" 40 5m ] (funded ()))

[<Fact>]
let ``LEDGER-V5-R1 orders are checked before the date`` () =
    let later = funded () |> Ledger.setDate (date 2026 1 15) |> ok
    Assert.Equal(Error(InvalidOrder "a"), run (date 2026 1 10) [ order "a" 10 0m ] later)
    Assert.Equal(Error(DateInPast(date 2026 1 10)), run (date 2026 1 10) [ order "a" 10 5m ] later)

[<Fact>]
let ``LEDGER-V5-R1 the business date moves even when nothing is due`` () =
    let outcomes, l = run (date 2026 3 3) [ order "a" 15 5m ] (funded ()) |> ok
    Assert.True(List.isEmpty outcomes)
    Assert.Equal(date 2026 3 3, l.Today)
    Assert.Equal(Ok 100m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V5-R2 a 31st order is due on the last day of shorter months`` () =
    let monthly = [ order "m" 31 10m ]
    Assert.True((outcomesOn (date 2026 4 30) monthly = [ Paid "m" ]))
    Assert.True((outcomesOn (date 2026 2 28) monthly = [ Paid "m" ]))
    Assert.True((outcomesOn (date 2028 2 29) monthly = [ Paid "m" ]))
    Assert.True(List.isEmpty (outcomesOn (date 2028 2 28) monthly))
    Assert.True(List.isEmpty (outcomesOn (date 2026 3 30) monthly))

[<Fact>]
let ``LEDGER-V5-R2 29th and 30th orders are due on 28 February in a common year`` () =
    Assert.True((outcomesOn (date 2026 2 28) [ order "q" 30 1m; order "p" 29 1m ] = [ Paid "p"; Paid "q" ]))

[<Fact>]
let ``LEDGER-V5-R2 due orders are paid in ascending id order whatever the list order`` () =
    let orders = [ between "b" cash savings 15 50m; between "a" savings landlord 15 50m ]
    let outcomes, l = run (date 2026 1 15) orders (funded ()) |> ok
    Assert.True((outcomes = [ Skipped("a", InsufficientFunds(savings, 50m)); Paid "b" ]))
    Assert.Equal(Ok 50m, Ledger.balance savings l)
    Assert.Equal(Ok 0m, Ledger.balance landlord l)

[<Fact>]
let ``LEDGER-V5-R2 ids are compared ordinally`` () =
    Assert.True((outcomesOn (date 2026 1 15) [ order "a" 15 1m; order "B" 15 1m ] = [ Paid "B"; Paid "a" ]))

[<Fact>]
let ``LEDGER-V5-R2 a payment carries the order and date reference`` () =
    let _, l = run (date 2026 4 30) [ order "rent" 30 40m ] (funded ()) |> ok
    let paid = Ledger.postings l |> List.filter (fun p -> p.Reference = "standing:rent:2026-04-30")
    Assert.True((paid |> List.map (fun p -> p.Account, p.Amount, p.Date) = [ (cash, -40m, date 2026 4 30); (landlord, 40m, date 2026 4 30) ]))

[<Fact>]
let ``LEDGER-V5-R2 an order the payer cannot cover is skipped whole`` () =
    let outcomes, l = run (date 2026 1 15) [ order "rent" 15 150m ] (funded ()) |> ok
    Assert.True((outcomes = [ Skipped("rent", InsufficientFunds(cash, 150m)) ]))
    Assert.Equal(Ok 100m, Ledger.balance cash l)
    Assert.Equal(Ok 0m, Ledger.balance landlord l)
    Assert.Equal(1, List.length (Ledger.postings l))

[<Fact>]
let ``LEDGER-V5-R2 a skipped order does not stop later orders`` () =
    let orders = [ order "a" 15 500m; between "g" cash ghost 15 5m; order "b" 15 30m ]
    let outcomes, l = run (date 2026 1 15) orders (funded ()) |> ok
    Assert.True((outcomes = [ Skipped("a", InsufficientFunds(cash, 500m)); Paid "b"; Skipped("g", UnknownAccount ghost) ]))
    Assert.Equal(Ok 70m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V5-R3 a rerun for the same date pays nothing twice`` () =
    let d = date 2026 1 15
    let _, once = run d [ order "rent" 15 40m; order "gym" 15 10m ] (funded ()) |> ok
    let outcomes, twice = run d [ order "rent" 15 40m; order "gym" 15 10m ] once |> ok
    Assert.True((outcomes = [ AlreadyPaid "gym"; AlreadyPaid "rent" ]))
    Assert.True((Ledger.postings twice = Ledger.postings once))

[<Fact>]
let ``LEDGER-V5-R3 a skipped order is paid by a later run for the same date`` () =
    let d = date 2026 1 15
    let _, skipped = run d [ order "rent" 15 150m ] (funded ()) |> ok
    let topped = Ledger.credit cash 100m "top-up" skipped |> ok
    let outcomes, l = run d [ order "rent" 15 150m ] topped |> ok
    Assert.True((outcomes = [ Paid "rent" ]))
    Assert.Equal(Ok 50m, Ledger.balance cash l)

[<Fact>]
let ``LEDGER-V5-R3 the same order is paid again the next month`` () =
    let _, january = run (date 2026 1 15) [ order "rent" 15 40m ] (funded ()) |> ok
    let outcomes, february = run (date 2026 2 15) [ order "rent" 15 40m ] january |> ok
    Assert.True((outcomes = [ Paid "rent" ]))
    Assert.Equal(Ok 20m, Ledger.balance cash february)
