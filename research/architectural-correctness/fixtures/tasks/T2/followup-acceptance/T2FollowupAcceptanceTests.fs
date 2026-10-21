module T2FollowupAcceptanceTests

open System.IO
open Xunit
open Lending.Host.Persistence
open Support

[<Fact>]
let ``LEND-T2-F1 each save appends one line and load returns the last state`` () =
    let path = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName())

    try
        let w = seeded "2026-03-02"
        let store = LogFileStore.create path
        store.Save(w.Ports.Store.Load())
        run w "borrow m1 c1" |> ignore
        store.Save(w.Ports.Store.Load())
        Assert.Equal(2, File.ReadAllLines(path).Length)
        Assert.Equal(w.Ports.Store.Load(), (LogFileStore.create path).Load())
    finally
        File.Delete path
