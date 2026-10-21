namespace Lending.Host

/// Tier 4: composition root (the only place that reads the clock).
module Composition =
    let today () = System.DateTime.UtcNow.Date
