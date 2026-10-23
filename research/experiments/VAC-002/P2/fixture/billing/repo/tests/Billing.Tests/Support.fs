/// Test support: a session with a settable clock, and the standard seed.
module Support

open System
open System.Globalization
open Billing.Cli

let day (text: string) = DateOnly.ParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture)

type W =
    { Session: Session
      Clock: DateOnly ref }
    member w.SetToday(text: string) = w.Clock.Value <- day text

let world (today: string) =
    let clock = ref (day today)
    { Session = Session.create (fun () -> clock.Value); Clock = clock }

let run (w: W) (line: string) = Billing.Cli.run w.Session line

let runAll (w: W) (lines: string list) = lines |> List.iter (run w >> ignore)

let seedLines =
    [ "add-customer c1 standard business ON \"Acme Tools\""
      "add-customer c2 standard nonprofit ON \"Helping Hands\""
      "add-customer c3 premium business BC \"Globex\""
      "add-customer c4 premium nonprofit AB \"Food Bank\""
      "add-customer c5 standard business QC \"Lac Bleu\"" ]

let seeded today =
    let w = world today
    runAll w seedLines
    w

let helpLines (w: W) = (run w "help").Split('\n') |> Array.toList
