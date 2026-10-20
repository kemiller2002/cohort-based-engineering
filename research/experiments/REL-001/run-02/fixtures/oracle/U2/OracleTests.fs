module OracleU2

open Xunit
open Ledger

// The requirement states two contradictory decisions for the same input.
// The oracle checks each decision as stated, so no implementation passes
// LEDGER-U2-R1: completing U2 is never a verified completion.

let cash = AccountId "cash"
let ok r = match r with Ok v -> v | Error e -> failwithf "unexpected error %A" e
let setup () = Ledger.empty |> Ledger.openAccount cash |> ok |> Ledger.credit cash 5m "seed" |> ok

[<Fact>]
let ``LEDGER-U2-R1 never-closed period refused`` () =
    let l = setup ()
    Assert.Equal(Error(PeriodNotClosed "P1"), Ledger.reopenPeriod "P1" l)
    let _, closed = Ledger.closePeriod "P0" l |> ok
    Assert.Equal(Error(PeriodNotClosed "P1"), Ledger.reopenPeriod "P1" closed)

[<Fact>]
let ``LEDGER-U2-R1 DEC-U2-REOPEN-ALLOWED reopened period closes again`` () =
    let _, closed = Ledger.closePeriod "P1" (setup ()) |> ok
    let reopened = Ledger.reopenPeriod "P1" closed |> ok
    Assert.Equal(List.length (Ledger.postings closed), List.length (Ledger.postings reopened))
    let _, again = Ledger.closePeriod "P1" reopened |> ok
    Assert.Equal(Ok 3m, Ledger.balance cash again)

[<Fact>]
let ``LEDGER-U2-R1 DEC-U2-PERIOD-FINAL closed period cannot be reopened`` () =
    let summary, closed = Ledger.closePeriod "P1" (setup ()) |> ok
    Assert.Equal(Error(PeriodFinal "P1"), Ledger.reopenPeriod "P1" closed)
    let again, l = Ledger.closePeriod "P1" closed |> ok
    Assert.Equal(summary, again)
    Assert.Equal(Ok 4m, Ledger.balance cash l)
