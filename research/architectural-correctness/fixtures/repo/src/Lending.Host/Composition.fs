/// The composition root: the one place that reads the clock and chooses the adapters.
module Lending.Host.Composition

open System
open System.IO
open Lending.Application
open Lending.Transition
open Lending.Host.Persistence

let systemClock () = DateOnly.FromDateTime DateTime.Today

/// Writes notices to an outbox file that the library's mail relay picks up.
let outboxNotifier (path: string) : Notifier =
    { Send =
        fun notice ->
            async {
                let (Lending.Semantic.MemberId recipient) = notice.Recipient
                do! File.AppendAllTextAsync(path, $"{recipient}\t{notice.Subject}\t{notice.Body}\n") |> Async.AwaitTask
                return Delivered
            } }

let ports (dataDirectory: string) : Ports =
    { Store = JsonFileStore.create (Path.Combine(dataDirectory, "library.lending.json"))
      Clock = systemClock
      Notifier = outboxNotifier (Path.Combine(dataDirectory, "outbox.txt")) }

[<EntryPoint>]
let main argv =
    let dataDirectory = if argv.Length > 0 then argv[0] else Directory.GetCurrentDirectory()
    let app = ports dataDirectory

    let rec loop () =
        Console.Write "> "

        match Console.ReadLine() with
        | null
        | "quit"
        | "exit" -> 0
        | line ->
            Console.WriteLine(Lending.Host.Cli.CommandLine.run app line)
            loop ()

    loop ()
