module OracleU7

open Xunit
open Ledger

let a = AccountId "a"
let b = AccountId "b"
let c = AccountId "c"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let isInvalid r = match r with Error(InvalidRateSchedule _) -> true | _ -> false
let tier upTo rate = { UpTo = upTo; Rate = rate }
/// The design note's example schedule: up to 1,000 at 1%; up to 5,000 at 2%; above at 3%.
let tiers () = InterestRates.create [ tier (Some 1000m) 0.01m; tier (Some 5000m) 0.02m; tier None 0.03m ] |> ok

[<Fact>]
let ``LEDGER-U7-R1 valid schedule kept as given`` () =
    let ts = [ tier (Some 1000m) 0.01m; tier (Some 5000m) 0.02m; tier None 0.03m ]
    Assert.Equal(Ok { Tiers = ts }, InterestRates.create ts)
    Assert.Equal(Ok { Tiers = [ tier None 0m ] }, InterestRates.create [ tier None 0m ])
    Assert.Equal(Ok { Tiers = [ tier None 1m ] }, InterestRates.create [ tier None 1m ])

[<Fact>]
let ``LEDGER-U7-R1 invalid schedules refused`` () =
    Assert.True(isInvalid (InterestRates.create []))
    Assert.True(isInvalid (InterestRates.create [ tier (Some 1000m) 0.01m ]))
    Assert.True(isInvalid (InterestRates.create [ tier None 0.01m; tier None 0.02m ]))
    Assert.True(isInvalid (InterestRates.create [ tier None 0.01m; tier (Some 10m) 0.02m ]))
    Assert.True(isInvalid (InterestRates.create [ tier (Some 1000m) 0.01m; tier (Some 1000m) 0.02m; tier None 0.03m ]))
    Assert.True(isInvalid (InterestRates.create [ tier (Some 5000m) 0.01m; tier (Some 1000m) 0.02m; tier None 0.03m ]))
    Assert.True(isInvalid (InterestRates.create [ tier (Some 0m) 0.01m; tier None 0.03m ]))
    Assert.True(isInvalid (InterestRates.create [ tier None -0.01m ]))
    Assert.True(isInvalid (InterestRates.create [ tier None 1.01m ]))

[<Fact>]
let ``LEDGER-U7-R2 marginal tiers per the design note`` () =
    Assert.Equal(120m, InterestRates.interestFor (tiers ()) 6000m)
    Assert.Equal(50m, InterestRates.interestFor (tiers ()) 3000m)

[<Fact>]
let ``LEDGER-U7-R2 tier limits are inclusive`` () =
    Assert.Equal(10m, InterestRates.interestFor (tiers ()) 1000m)
    Assert.Equal(90m, InterestRates.interestFor (tiers ()) 5000m)

[<Fact>]
let ``LEDGER-U7-R2 just above a boundary is continuous`` () =
    // 1000 x 0.01 + 100 x 0.02 = 12, not 1100 x 0.02 = 22
    Assert.Equal(12m, InterestRates.interestFor (tiers ()) 1100m)

[<Fact>]
let ``LEDGER-U7-R2 zero and negative balances earn nothing`` () =
    Assert.Equal(0m, InterestRates.interestFor (tiers ()) 0m)
    Assert.Equal(0m, InterestRates.interestFor (tiers ()) -50m)

[<Fact>]
let ``LEDGER-U7-R2 rounded once with banker's rounding`` () =
    // 1000.50: 10 + 0.50 x 0.02 = 10.01 exactly
    Assert.Equal(10.01m, InterestRates.interestFor (tiers ()) 1000.50m)
    // 0.5 x 0.01 = 0.005 -> 0.00 (half to even); 1.5 x 0.01 = 0.015 -> 0.02
    Assert.Equal(0m, InterestRates.interestFor (tiers ()) 0.5m)
    Assert.Equal(0.02m, InterestRates.interestFor (tiers ()) 1.5m)
    // slices 0.5 x 0.01 + 0.4 x 0.01 = 0.005 + 0.004 = 0.009 -> 0.01 when rounded once
    // (rounding each slice would give 0.00 + 0.00)
    let two = InterestRates.create [ tier (Some 0.5m) 0.01m; tier None 0.01m ] |> ok
    Assert.Equal(0.01m, InterestRates.interestFor two 0.9m)
    // single slice 0.035 -> 0.04
    Assert.Equal(0.04m, InterestRates.interestFor (InterestRates.create [ tier None 0.01m ] |> ok) 3.5m)

let setup () =
    Ledger.empty |> Ledger.openAccount a |> ok |> Ledger.openAccount b |> ok |> Ledger.openAccount c |> ok
    |> Ledger.credit a 6001m "seed" |> ok |> Ledger.credit b 1001m "seed" |> ok |> Ledger.credit c 0.5m "seed" |> ok

[<Fact>]
let ``LEDGER-U7-R3 refused before the period is closed`` () =
    Assert.Equal(Error(PeriodNotClosed "P1"), Ledger.accrueInterest "P1" (tiers ()) (setup ()))
    let _, l = Ledger.closePeriod "P0" (setup ()) |> ok
    Assert.Equal(Error(PeriodNotClosed "P1"), Ledger.accrueInterest "P1" (tiers ()) l)

[<Fact>]
let ``LEDGER-U7-R3 pays per account on the close balances`` () =
    let _, closed = Ledger.closePeriod "P1" (setup ()) |> ok
    // after the fee: a 6000, b 1000, c 0.5
    let paid, l = Ledger.accrueInterest "P1" (tiers ()) closed |> ok
    Assert.Equal<Map<AccountId, decimal>>(Map [ a, 120m; b, 10m; c, 0m ], paid)
    Assert.Equal(Ok 6120m, Ledger.balance a l)
    Assert.Equal(Ok 1010m, Ledger.balance b l)
    Assert.Equal(Ok 0.5m, Ledger.balance c l)

[<Fact>]
let ``LEDGER-U7-R3 posting shape and order`` () =
    let _, closed = Ledger.closePeriod "P1" (setup ()) |> ok
    let closed = closed |> Ledger.setDate (System.DateOnly(2026, 7, 1)) |> ok
    let _, l = Ledger.accrueInterest "P1" (tiers ()) closed |> ok
    let added = Ledger.postings l |> List.skip (List.length (Ledger.postings closed))
    Assert.Equal<Posting list>(
        [ { Account = a; Amount = 120m; Reference = "interest:P1"; Date = System.DateOnly(2026, 7, 1) }
          { Account = b; Amount = 10m; Reference = "interest:P1"; Date = System.DateOnly(2026, 7, 1) } ],
        added)

[<Fact>]
let ``LEDGER-U7-R3 uses the close summary not the current balance`` () =
    let _, closed = Ledger.closePeriod "P1" (setup ()) |> ok
    let moved = closed |> Ledger.debit a 5000m "spend" |> ok |> Ledger.credit b 4000m "top-up" |> ok
    let late = moved |> Ledger.openAccount (AccountId "late") |> ok |> Ledger.credit (AccountId "late") 900m "seed" |> ok
    let paid, l = Ledger.accrueInterest "P1" (tiers ()) late |> ok
    Assert.Equal<Map<AccountId, decimal>>(Map [ a, 120m; b, 10m; c, 0m ], paid)
    Assert.Equal(Ok 1120m, Ledger.balance a l)
    Assert.Equal(Ok 900m, Ledger.balance (AccountId "late") l)

[<Fact>]
let ``LEDGER-U7-R3 second accrual refused even when nobody was paid`` () =
    let poor = Ledger.empty |> Ledger.openAccount c |> ok |> Ledger.credit c 0.5m "seed" |> ok
    let _, closed = Ledger.closePeriod "P1" poor |> ok
    let paid, once = Ledger.accrueInterest "P1" (tiers ()) closed |> ok
    Assert.Equal<Map<AccountId, decimal>>(Map [ c, 0m ], paid)
    Assert.Equal(Error(InterestAlreadyAccrued "P1"), Ledger.accrueInterest "P1" (tiers ()) once)

[<Fact>]
let ``LEDGER-U7-R3 each period accrues once`` () =
    let _, l1 = Ledger.closePeriod "P1" (setup ()) |> ok
    let _, l2 = Ledger.accrueInterest "P1" (tiers ()) l1 |> ok
    Assert.Equal(Error(InterestAlreadyAccrued "P1"), Ledger.accrueInterest "P1" (tiers ()) l2)
    let _, l3 = Ledger.closePeriod "P2" l2 |> ok
    let paid, _ = Ledger.accrueInterest "P2" (tiers ()) l3 |> ok
    // P2 close: a 6120 - 1 = 6119 -> 10 + 80 + 1119 x 0.03 = 123.57
    Assert.Equal(123.57m, paid[a])
