module Lending.Host.Program

[<EntryPoint>]
let main argv =
    let ports = Composition.ports ()
    let id = if argv.Length > 0 then argv[0] else "L1"
    System.Console.WriteLine(Presenters.result (Lending.Application.UseCases.renewLoan ports id))
    0
