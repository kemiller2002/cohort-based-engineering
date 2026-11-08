// Unit tests for RosMerge (run: dotnet fsi tests.fsx). Exit code = number of failures.
#load "RosMerge.fs"
open System.Text.Json.Nodes

let mutable failures = 0
let check name cond =
    if cond then printfn "PASS %s" name
    else
        failures <- failures + 1
        printfn "FAIL %s" name

let ev id t = sprintf """{"schemaVersion":"1.0.0","type":"%s","eventId":"%s"}""" t id
let lines xs = (xs |> String.concat "\n") + "\n"
let isOk = function Ok _ -> true | Error _ -> false
let okText = function Ok t -> t | Error e -> failwithf "unexpected refusal: %s" e
let eventIds (text: string) =
    text.Split('\n') |> Array.filter ((<>) "") |> Array.map (fun (l: string) -> let n = JsonNode.Parse l in n["eventId"].GetValue<string>()) |> Array.toList

// events
let b = lines [ ev "e1" "a"; ev "e2" "a" ]
let l = lines [ ev "e1" "a"; ev "e2" "a"; ev "l1" "x"; ev "l2" "x" ]
let r = lines [ ev "e1" "a"; ev "e2" "a"; ev "r1" "y" ]
let m = RosMerge.mergeEvents b l r
check "events: union of both sides' appends" (isOk m && eventIds (okText m) = [ "e1"; "e2"; "l1"; "l2"; "r1" ])
check "events: deterministic (swap sides keeps set)" (eventIds (okText (RosMerge.mergeEvents b r l)) |> Set.ofList = Set.ofList [ "e1"; "e2"; "l1"; "l2"; "r1" ])
check "events: shared append kept once" (eventIds (okText (RosMerge.mergeEvents b (lines [ ev "e1" "a"; ev "e2" "a"; ev "s" "z" ]) (lines [ ev "e1" "a"; ev "e2" "a"; ev "s" "z" ]))) = [ "e1"; "e2"; "s" ])
check "events: same id different content refuses" (not (isOk (RosMerge.mergeEvents b (lines [ ev "e1" "a"; ev "e2" "a"; ev "x" "p" ]) (lines [ ev "e1" "a"; ev "e2" "a"; ev "x" "q" ]))))
check "events: base removal refuses" (not (isOk (RosMerge.mergeEvents b (lines [ ev "e1" "a" ]) r)))
check "events: base reorder refuses" (not (isOk (RosMerge.mergeEvents b (lines [ ev "e2" "a"; ev "e1" "a" ]) r)))
check "events: duplicate id refuses" (not (isOk (RosMerge.mergeEvents b (lines [ ev "e1" "a"; ev "e2" "a"; ev "e2" "a" ]) r)))
check "events: original line bytes preserved" ((okText m).Contains(ev "l1" "x"))
check "topo: cycle refuses" (not (isOk (RosMerge.topoOrder [ "a"; "b" ] [ "b"; "a" ])))

// context
let item id state = sprintf """{"id":"%s","type":"task","state":"%s"}""" id state
let ctx actor updated (items: string list) =
    sprintf """{"schemaVersion":"1.0.0","protocolVersion":"1.0.0","repository":"r","actor":"%s","startedAt":"2026-01-01T00:00:00Z","updatedAt":"%s","baselineDirtyPaths":[],"workItems":[%s]}"""
        actor updated (String.concat "," items)
let ids (text: string) =
    let root = JsonNode.Parse text
    root["workItems"].AsArray() |> Seq.map (fun n -> n["id"].GetValue<string>()) |> Seq.toList
let field (text: string) (k: string) =
    let root = JsonNode.Parse text
    root[k].GetValue<string>()
let stateOf (text: string) id =
    let root = JsonNode.Parse text
    root["workItems"].AsArray() |> Seq.find (fun n -> n["id"].GetValue<string>() = id) |> fun n -> n["state"].GetValue<string>()

let cb = ctx "boot" "2026-01-01T00:00:00Z" [ item "A" "complete" ]
let cl = ctx "lane-l" "2026-01-01T01:00:00Z" [ item "A" "complete"; item "L" "complete" ]
let cr = ctx "lane-r" "2026-01-01T02:00:00Z" [ item "A" "complete"; item "R" "started" ]
let cm = RosMerge.mergeContext cb cl cr
check "context: both new items kept, base order then ours then theirs" (isOk cm && ids (okText cm) = [ "A"; "L"; "R" ])
check "context: updatedAt is later side" (field (okText cm) "updatedAt" = "2026-01-01T02:00:00Z")
check "context: actor policy takes later side" (field (okText cm) "actor" = "lane-r")
check "context: one-sided item change taken" (stateOf (okText (RosMerge.mergeContext cb (ctx "x" "2026-01-01T01:00:00Z" [ item "A" "reopened" ]) cr)) "A" = "reopened")
check "context: divergent same-id item refuses" (not (isOk (RosMerge.mergeContext cb (ctx "x" "2026-01-01T01:00:00Z" [ item "A" "p" ]) (ctx "x" "2026-01-01T01:00:00Z" [ item "A" "q" ]))))
check "context: deletion refuses" (not (isOk (RosMerge.mergeContext cb (ctx "x" "2026-01-01T01:00:00Z" []) cr)))
check "context: repository change refuses" (not (isOk (RosMerge.mergeContext cb (cl.Replace("\"repository\":\"r\"", "\"repository\":\"q\"")) cr)))
check "context: updatedAt before base refuses" (not (isOk (RosMerge.mergeContext cl cb cr)))
check "context: divergent non-actor metadata refuses" (not (isOk (RosMerge.mergeContext cb (cl.Replace("\"startedAt\":\"2026-01-01T00:00:00Z\"", "\"startedAt\":\"2026-01-02T00:00:00Z\"")) (cr.Replace("\"startedAt\":\"2026-01-01T00:00:00Z\"", "\"startedAt\":\"2026-01-03T00:00:00Z\"")))))
check "context: identical additions kept once" (ids (okText (RosMerge.mergeContext cb cl cl)) = [ "A"; "L" ])
check "context: output is indented JSON with trailing newline" ((okText cm).EndsWith "}\n" && (okText cm).Contains "\n  \"workItems\"")
check "canonical: key order insensitive" (RosMerge.canonical (JsonNode.Parse """{"b":1,"a":[1,{"d":2,"c":3}]}""") = RosMerge.canonical (JsonNode.Parse """{"a":[1,{"c":3,"d":2}],"b":1}"""))
check "dispatch by path" ((RosMerge.mergeByPath ".ros/events/events.jsonl").IsSome && (RosMerge.mergeByPath "src/x.fs").IsNone)

printfn "%d failure(s)" failures
exit failures
