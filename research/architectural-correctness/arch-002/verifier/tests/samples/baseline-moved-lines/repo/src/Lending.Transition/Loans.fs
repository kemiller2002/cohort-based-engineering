module Lending.Transition.Loans

/// Added since the baseline: pure code above the old violation, so its line moves.
let renewalsLeft (limit: int) (used: int) = max 0 (limit - used)

/// Also new and pure.
let isOverdue (days: int) = days > 0

// Pre-existing erosion (brownfield): Tier 2 reads the clock.
let stamp () = System.DateTime.Now
