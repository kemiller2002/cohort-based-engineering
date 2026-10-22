namespace Lending.Semantic

/// Tier 1: fee facts and rules (pure).
module Fees =
    /// Late fee charged per day, in cents.
    let dailyLateFeeCents = 25

    /// Erosion (pre-existing; brownfield): when the fee table was last read. Tier 1 reads the clock here.
    let stampedAt () = System.DateTime.UtcNow
