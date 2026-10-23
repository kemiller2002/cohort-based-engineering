/// Test support: a session with a settable clock, and the standard seed.
module Support

open System
open System.Globalization
open Clinic.Cli

let day (text: string) = DateOnly.ParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture)

type W =
    { Session: Session
      Clock: DateOnly ref }
    member w.SetToday(text: string) = w.Clock.Value <- day text

let world (today: string) =
    let clock = ref (day today)
    { Session = Session.create (fun () -> clock.Value); Clock = clock }

let run (w: W) (line: string) = Clinic.Cli.run w.Session line

let runAll (w: W) (lines: string list) = lines |> List.iter (run w >> ignore)

let seedLines =
    [ "add-patient p1 \"Ana Silva\""
      "add-patient p2 \"Ben Okafor\""
      "add-patient p3 \"Chen Wei\""
      "add-clinician k1 \"Dr. Rossi\""
      "add-clinician k2 \"Dr. Patel\"" ]

let seeded today =
    let w = world today
    runAll w seedLines
    w

let helpLines (w: W) = (run w "help").Split('\n') |> Array.toList
