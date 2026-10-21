module T7FollowupAcceptanceTests

open System.Text.Json
open Xunit
open Lending.Host.Cli
open Support

let api (w: World) (request: string) = JsonDocument.Parse(JsonApi.handle w.Ports request).RootElement

[<Fact>]
let ``LEND-T7-F1 borrow through the json surface`` () =
    let w = seeded "2026-03-02"
    let response = api w """{"command": "borrow", "member": "m1", "copy": "c1"}"""
    Assert.True(response.GetProperty("ok").GetBoolean())
    Assert.Equal("2026-03-23", response.GetProperty("due").GetString())
    Assert.Equal("loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-03-23", run w "loans m1")

[<Fact>]
let ``LEND-T7-F2 a refused request carries the error text`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    let response = api w """{"command": "borrow", "member": "s1", "copy": "c1"}"""
    Assert.False(response.GetProperty("ok").GetBoolean())
    Assert.Equal("copy c1 is already on loan", response.GetProperty("error").GetString())
