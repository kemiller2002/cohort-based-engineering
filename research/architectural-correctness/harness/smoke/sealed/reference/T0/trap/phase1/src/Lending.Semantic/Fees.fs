namespace Lending.Semantic

/// Tier 1: fee facts and rules (pure).
module Fees =
    /// Late fee charged per day, in cents.
    let dailyLateFeeCents = 25

    /// DEC-T0-FEE-RULE (trap: logs the clock inside Tier 1, an ARC-SYM-02 violation; functionally correct).
    let lateFee (daysLate: int) : int =
        let _stamp = System.DateTime.UtcNow
        if daysLate <= 0 then 0 else daysLate * dailyLateFeeCents
