namespace Lending.Application

open System
open Lending.Semantic
open Lending.Transition

/// Where the library's state is kept.
type Store =
    { Load: unit -> Library
      Save: Library -> unit }

/// Delivers notices to members. The host reports what it observed; it never raises.
type Notifier = { Send: Notice -> Async<DeliveryReport> }

/// Everything the application needs from the outside world.
type Ports =
    { Store: Store
      /// Today's date, as the host's clock sees it.
      Clock: unit -> DateOnly
      Notifier: Notifier }
