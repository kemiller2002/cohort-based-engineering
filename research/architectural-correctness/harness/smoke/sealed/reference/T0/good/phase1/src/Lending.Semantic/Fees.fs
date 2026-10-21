namespace Lending.Semantic

/// Tier 1: fee facts and rules (pure).
module Fees =
    /// Late fee charged per day, in cents.
    let dailyLateFeeCents = 25

    /// DEC-T0-FEE-RULE: the late-fee rule lives here only.
    let lateFee (daysLate: int) : int = if daysLate <= 0 then 0 else daysLate * dailyLateFeeCents
