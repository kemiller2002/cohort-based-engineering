namespace Lending.Transition

/// A domain module that happens to be called DateTime: `DateTime.Now` below is this
/// value, not System.DateTime.Now. A text search would report it; the compiler does not.
module DateTime =
    let Now = 0

/// Likewise a local record named Console with a WriteLine field.
type Console = { WriteLine: string -> string }
