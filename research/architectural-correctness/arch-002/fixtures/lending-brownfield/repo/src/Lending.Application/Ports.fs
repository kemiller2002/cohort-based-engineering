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

/// Text files the library reads and writes (imports, exports).
type Files =
    { WriteLines: string -> string list -> unit
      /// The lines of the file, or None when it cannot be read.
      ReadLines: string -> string list option }

/// Snapshots of the whole state kept at a path (backups).
type Archive =
    { Save: string -> Library -> unit
      /// The snapshot at the path, or None when there is none.
      Load: string -> Library option }

/// Everything the application needs from the outside world.
type Ports =
    { Store: Store
      /// Today's date, as the host's clock sees it.
      Clock: unit -> DateOnly
      Notifier: Notifier
      Files: Files
      Archive: Archive }
