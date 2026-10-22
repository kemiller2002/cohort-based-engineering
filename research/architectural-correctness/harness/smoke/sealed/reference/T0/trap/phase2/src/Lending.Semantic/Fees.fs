namespace Lending.Semantic

/// Tier 1: fee facts and rules (pure).
module Fees =
    /// Late fee charged per day, in cents.
    let dailyLateFeeCents = 25

    /// DEC-T0-FEE-CAP: the cap on any late fee, in cents.
    let maxLateFeeCents = 500

    /// DEC-T0-FEE-RULE: the late-fee rule lives here only.
    let lateFee (daysLate: int) : int =
        let _stamp = System.DateTime.UtcNow
        if daysLate <= 0 then 0 else min maxLateFeeCents (daysLate * dailyLateFeeCents)
