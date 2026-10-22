// Post-hoc probe (VAC-002 amendment A4): not part of the frozen oracle.
[<Fact>]
let ``PROBE LEND-L04-R2 a staff member owing more than 5.00 cannot borrow`` () =
    let w = seeded "2026-03-02"
    lateReturn w "c1" "t1" "2026-03-02" "2026-04-13"
    Assert.Equal("t1 owes 5.25", run w "owes t1")
    Assert.Equal("error: member t1 owes 5.25", run w "borrow t1 c2")

// Post-hoc probe (A4), independent of later loan-period and open-day rules: a long-overdue staff return.
[<Fact>]
let ``PROBE LEND-L04-R2 a staff member owing well over 5.00 cannot borrow`` () =
    let w = seeded "2026-03-02"
    lateReturn w "c1" "t1" "2026-03-02" "2026-09-30"
    let owes = run w "owes t1"
    Assert.StartsWith("t1 owes ", owes)
    Assert.True(decimal (owes.Substring 8) > 5.00m, owes)
    Assert.StartsWith("error: member t1 owes", run w "borrow t1 c2")
