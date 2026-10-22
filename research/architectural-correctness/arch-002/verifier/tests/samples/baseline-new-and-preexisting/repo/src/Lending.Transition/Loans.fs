module Lending.Transition.Loans

/// New since the baseline, mirroring the old violation below: a second clock read in the
/// same module. The key (rule, file, symbol, module) occurs twice now and once in the
/// baseline, so exactly one finding is new.
let dueFromNow (days: float) = System.DateTime.Now.AddDays days

// Pre-existing erosion (brownfield): Tier 2 reads the clock.
let stamp () = System.DateTime.Now
