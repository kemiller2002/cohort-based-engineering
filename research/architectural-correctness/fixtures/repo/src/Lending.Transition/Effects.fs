namespace Lending.Transition

open Lending.Semantic

/// A message the library asks the host to deliver to a member (an effect requested as data).
type Notice =
    { Recipient: MemberId
      Subject: string
      Body: string }

/// What the host observed when it tried to deliver a notice.
type DeliveryReport =
    | Delivered
    | Rejected of reason: string
    /// The channel gave no answer in time: the notice may or may not have arrived.
    | NoAnswer
