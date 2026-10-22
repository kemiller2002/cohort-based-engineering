/// Test helpers: an in-memory library with a clock the test controls.
module Support

open System
open System.Globalization
open Lending.Semantic
open Lending.Transition
open Lending.Application
open Lending.Host.Persistence
open Lending.Host.Cli

let day (text: string) =
    DateOnly.ParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture)

type World =
    { Ports: Ports
      SetToday: string -> unit
      Sent: unit -> Notice list }

/// A world whose notifier answers each notice with `deliver notice`.
let worldWith (today: string) (deliver: Notice -> DeliveryReport) =
    let clock = ref (day today)
    let sent = ref []

    let ports =
        Lending.Host.Composition.portsWith
            (InMemoryStore.create Library.empty)
            (fun () -> clock.Value)
            { Send =
                fun notice ->
                    async {
                        sent.Value <- sent.Value @ [ notice ]
                        return deliver notice
                    } }

    { Ports = ports
      SetToday = fun text -> clock.Value <- day text
      Sent = fun () -> sent.Value }

let world (today: string) = worldWith today (fun _ -> Delivered)

let run (w: World) (line: string) = CommandLine.run w.Ports line

let runAll (w: World) (lines: string list) =
    lines |> List.map (run w) |> List.last

/// A library with members m1 (standard), s1 (student), t1 (staff), book b1 "Dune" with copies c1 and c2,
/// and book b2 "Emma" with copy c3.
let seeded (today: string) =
    let w = world today

    [ "add-member m1 standard \"Ada Lovelace\""
      "add-member s1 student \"Sam Student\""
      "add-member t1 staff \"Tess Staff\""
      "add-book b1 9780441013593 Dune \"Frank Herbert\""
      "add-copy c1 b1"
      "add-copy c2 b1"
      "add-book b2 9780141439587 Emma \"Jane Austen\""
      "add-copy c3 b2" ]
    |> List.iter (run w >> ignore)

    w
