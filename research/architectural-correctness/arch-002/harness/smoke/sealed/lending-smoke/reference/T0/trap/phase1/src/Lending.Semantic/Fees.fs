namespace Lending.Semantic

/// Tier 1: fee facts and rules (pure).
module Fees =
    /// Late fee charged per day, in cents.
    let dailyLateFeeCents = 25

    /// DEC-T0-FEE-RULE (trap: stamps the clock inside Tier 1 like stampedAt below; a NEW ARC-SYM-02 violation).
    let lateFee (daysLate: int) : int =
        let _stamp = System.DateTime.UtcNow
        if daysLate <= 0 then 0 else daysLate * dailyLateFeeCents

    /// Erosion (pre-existing; brownfield): when the fee table was last read. Tier 1 reads the clock here.
    let stampedAt () = System.DateTime.UtcNow
