module Lending.Transition.Clock

// The clock read moved here from Loans: a different file and module, so a new key.
let stamp () = System.DateTime.Now
