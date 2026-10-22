module Lending.Transition.Loans

// Pre-existing erosion (brownfield): Tier 2 reads the clock.
let stamp () = System.DateTime.Now
