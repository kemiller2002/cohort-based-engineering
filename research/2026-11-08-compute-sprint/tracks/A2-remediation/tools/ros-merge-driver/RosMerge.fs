/// EXPERIMENTAL prototype (SPR-A2-01). Pure, side-effect-free three-way merge of the two
/// Praxis native history files. The IO shell lives in ros-merge.fsx.
///
/// Semantics deliberately mirror Praxis `WorkHistoryMerge.plan` (src/Praxis.Domain/Work/HistoryMerge.fs):
///   * work items: three-way by `id`; independent changes merge; divergent same-id change REFUSES;
///     deletion of a base item REFUSES.
///   * events: union by `eventId`; base events must be an unchanged prefix-subsequence on both sides;
///     same id with different content REFUSES; order = deterministic topological merge of both sides.
///   * metadata: three-way per key; divergence REFUSES, except `actor` (see actorPolicy).
///   * `updatedAt`: the later of the two sides (never earlier than base).
/// Records are re-emitted from their original JSON nodes / original event lines, never re-synthesized.
module RosMerge

open System
open System.Globalization
open System.Text.Encodings.Web
open System.Text.Json
open System.Text.Json.Nodes

type MergeResult = Result<string, string>

let private relaxed =
    JsonSerializerOptions(WriteIndented = true, IndentSize = 2, Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping)

let private compactOpts = JsonSerializerOptions(Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping)

/// Canonical (key-sorted, compact) text of a node: the comparison key for "same record".
let rec canonical (node: JsonNode) : string =
    match node with
    | null -> "null"
    | :? JsonObject as o ->
        o
        |> Seq.sortWith (fun a b -> String.CompareOrdinal(a.Key, b.Key))
        |> Seq.map (fun kv -> JsonSerializer.Serialize(kv.Key, compactOpts) + ":" + canonical kv.Value)
        |> String.concat ","
        |> sprintf "{%s}"
    | :? JsonArray as a -> a |> Seq.map canonical |> String.concat "," |> sprintf "[%s]"
    | v -> v.ToJsonString compactOpts

/// Three-way choice for one key. None = absent.
let choose3 (b: 'a option) (l: 'a option) (r: 'a option) : Result<'a option, unit> =
    if l = r then Ok l
    elif l = b then Ok r
    elif r = b then Ok l
    else Error()

let private sequenceResults (xs: Result<'a, string> list) : Result<'a list, string> =
    List.foldBack (fun x acc ->
        match x, acc with
        | Ok v, Ok vs -> Ok(v :: vs)
        | Error e, _ -> Error e
        | _, Error e -> Error e) xs (Ok [])

let private duplicates (ids: string list) =
    ids |> List.countBy id |> List.filter (fun (_, n) -> n > 1) |> List.map fst

/// Three-way map merge keyed by identity; values compared canonically.
let mergeKeyed label (b: (string * string) list) (l: (string * string) list) (r: (string * string) list) =
    let bm, lm, rm = Map.ofList b, Map.ofList l, Map.ofList r
    let keys = (b @ l @ r) |> List.map fst |> List.distinct
    keys
    |> List.map (fun k ->
        match choose3 (Map.tryFind k bm) (Map.tryFind k lm) (Map.tryFind k rm) with
        | Ok v -> Ok(k, v)
        | Error() -> Error(sprintf "%s: divergent identity %s" label k))
    |> sequenceResults
    |> Result.map (List.choose (fun (k, v) -> v |> Option.map (fun x -> k, x)))

/// Deterministic topological merge preserving each side's relative order
/// (ties broken by first appearance in left @ right), as Praxis does.
let topoOrder (left: string list) (right: string list) : Result<string list, string> =
    let order = (left @ right) |> List.distinct
    let rank = order |> List.mapi (fun i x -> x, i) |> Map.ofList
    let edges = [ left; right ] |> List.collect List.pairwise |> List.distinct
    let succ =
        edges |> List.fold (fun m (a, b) -> Map.add a (Set.add b (Map.tryFind a m |> Option.defaultValue Set.empty)) m) Map.empty
    let indeg0 = order |> List.map (fun x -> x, 0) |> Map.ofList
    let indeg = edges |> List.fold (fun (m: Map<string, int>) (_, b) -> Map.add b (m[b] + 1) m) indeg0
    let ready0 = indeg |> Map.toList |> List.filter (fun (_, n) -> n = 0) |> List.map (fun (x, _) -> rank[x], x) |> Set.ofList
    let rec go ready (deg: Map<string, int>) acc =
        if Set.isEmpty ready then
            if List.length acc = order.Length then Ok(List.rev acc) else Error "events: incompatible ordering (cycle)"
        else
            let (_, x) as top = Set.minElement ready
            let ready' = Set.remove top ready
            let targets = Map.tryFind x succ |> Option.defaultValue Set.empty
            let deg', ready'' =
                targets
                |> Set.fold (fun (d: Map<string, int>, rd) t ->
                    let n = d[t] - 1
                    Map.add t n d, (if n = 0 then Set.add (rank[t], t) rd else rd)) (deg, ready')
            go ready'' deg' (x :: acc)
    go ready0 indeg []

// ---------------------------------------------------------------- events.jsonl

type private Event = { Id: string; Canon: string; Line: string }

let private parseEvents (text: string) : Result<Event list, string> =
    try
        text.Split('\n')
        |> Array.map (fun l -> l.TrimEnd('\r'))
        |> Array.filter (String.IsNullOrWhiteSpace >> not)
        |> Array.map (fun line ->
            let node = JsonNode.Parse line
            match node with
            | :? JsonObject as o when o.ContainsKey "eventId" -> { Id = o["eventId"].GetValue<string>(); Canon = canonical node; Line = line }
            | _ -> failwith "event without eventId")
        |> Array.toList
        |> Ok
    with ex -> Error("events: unparseable (" + ex.Message + ")")

let mergeEvents (baseText: string) (oursText: string) (theirsText: string) : MergeResult =
    match parseEvents baseText, parseEvents oursText, parseEvents theirsText with
    | Ok b, Ok l, Ok r ->
        let ids (es: Event list) = es |> List.map (fun e -> e.Id)
        match [ b; l; r ] |> List.collect (ids >> duplicates) with
        | d :: _ -> Error("events: duplicate eventId " + d)
        | [] ->
            let baseSet = b |> List.map (fun e -> e.Id) |> Set.ofList
            let baseSeq = b |> List.map (fun e -> e.Id, e.Canon)
            let keepBase (es: Event list) = es |> List.filter (fun e -> baseSet.Contains e.Id) |> List.map (fun e -> e.Id, e.Canon)
            if keepBase l <> baseSeq || keepBase r <> baseSeq then
                Error "events: base history removed, rewritten or reordered"
            else
                let pairs (es: Event list) = es |> List.map (fun e -> e.Id, e.Canon)
                mergeKeyed "event" [] (pairs l) (pairs r)
                |> Result.bind (fun _ -> topoOrder (ids l) (ids r))
                |> Result.map (fun order ->
                    // Original bytes: prefer ours' line, else theirs'.
                    let lineOf = (r @ l) |> List.map (fun e -> e.Id, e.Line) |> Map.ofList
                    (order |> List.map (fun id -> lineOf[id]) |> String.concat "\n") + "\n")
    | Error e, _, _ | _, Error e, _ | _, _, Error e -> Error e

// ---------------------------------------------------------------- context/current.json

let private str (o: JsonObject) (k: string) =
    match o[k] with
    | :? JsonValue as v when v.GetValueKind() = JsonValueKind.String -> Some(v.GetValue<string>())
    | _ -> None

let private parseTime (s: string) =
    DateTimeOffset.Parse(s, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)

/// Preregistered policy for the only metadata key both sides routinely rewrite:
/// take `actor` from the side whose `updatedAt` is later; tie -> ours.
let actorPolicy (oursTime: DateTimeOffset) (theirsTime: DateTimeOffset) (ours: JsonNode) (theirs: JsonNode) =
    if theirsTime > oursTime then theirs else ours

let mergeContext (baseText: string) (oursText: string) (theirsText: string) : MergeResult =
    try
        let o, a, b = (JsonNode.Parse baseText).AsObject(), (JsonNode.Parse oursText).AsObject(), (JsonNode.Parse theirsText).AsObject()
        let all = [ o; a; b ]
        if all |> List.exists (fun x -> str x "schemaVersion" <> Some "1.0.0" || str x "protocolVersion" <> Some "1.0.0") then
            Error "context: unsupported version"
        elif all |> List.map (fun x -> str x "repository") |> List.distinct |> List.length <> 1 then
            Error "context: repository identity changed"
        else
            let times = all |> List.map (fun x -> str x "updatedAt" |> Option.map parseTime)
            match times with
            | [ Some tO; Some tA; Some tB ] when tA >= tO && tB >= tO ->
                let items (x: JsonObject) =
                    x["workItems"].AsArray() |> Seq.map (fun n -> (n.AsObject() |> fun i -> str i "id" |> Option.defaultValue ""), n) |> Seq.toList
                let iO, iA, iB = items o, items a, items b
                let canonPairs = List.map (fun (k, n) -> k, canonical n)
                match [ iO; iA; iB ] |> List.collect (List.map fst >> fun ids -> (if List.contains "" ids then [ "<missing id>" ] else []) @ duplicates ids) with
                | d :: _ -> Error("context: bad work-item identity " + d)
                | [] ->
                    let idsA, idsB = iA |> List.map fst |> Set.ofList, iB |> List.map fst |> Set.ofList
                    match iO |> List.tryFind (fun (k, _) -> not (idsA.Contains k && idsB.Contains k)) with
                    | Some(k, _) -> Error("context: work-item deletion not supported " + k)
                    | None ->
                        mergeKeyed "work item" (canonPairs iO) (canonPairs iA) (canonPairs iB)
                        |> Result.bind (fun merged ->
                            let metaKeys (x: JsonObject) = x |> Seq.map (fun kv -> kv.Key) |> Seq.filter (fun k -> k <> "workItems" && k <> "updatedAt") |> Seq.toList
                            let keys = (metaKeys a @ metaKeys b @ metaKeys o) |> List.distinct
                            let get (x: JsonObject) k = if x.ContainsKey k then Some(canonical x[k]) else None
                            keys
                            |> List.map (fun k ->
                                match choose3 (get o k) (get a k) (get b k) with
                                | Ok v -> Ok(k, v |> Option.map (fun c -> [ a; b; o ] |> List.find (fun x -> get x k = Some c) |> fun src -> src[k]))
                                | Error() when k = "actor" && a.ContainsKey k && b.ContainsKey k -> Ok(k, Some(actorPolicy tA tB a[k] b[k]))
                                | Error() -> Error("metadata: divergent " + k))
                            |> sequenceResults
                            |> Result.map (fun meta -> merged, Map.ofList meta))
                        |> Result.map (fun (merged, meta) ->
                            let mergedMap = Map.ofList merged
                            let nodeOf = (iO @ iB @ iA) |> List.map (fun (k, n) -> (k, canonical n), n) |> Map.ofList
                            let order = (iO @ iA @ iB) |> List.map fst |> List.distinct |> List.filter mergedMap.ContainsKey
                            let outItems = JsonArray()
                            order |> List.iter (fun k -> outItems.Add(nodeOf[(k, mergedMap[k])].DeepClone()))
                            let result = JsonObject()
                            let topKeys = (a |> Seq.map (fun kv -> kv.Key) |> Seq.toList) @ (b |> Seq.map (fun kv -> kv.Key) |> Seq.toList) |> List.distinct
                            topKeys
                            |> List.iter (fun k ->
                                if k = "workItems" then result[k] <- outItems
                                elif k = "updatedAt" then
                                    result[k] <- (if tB > tA then b[k] else a[k]).DeepClone()
                                else
                                    match Map.tryFind k meta with
                                    | Some(Some n) -> result[k] <- (if isNull n then null else n.DeepClone())
                                    | _ -> ())
                            result.ToJsonString relaxed + "\n")
            | _ -> Error "context: updatedAt missing or predates base"
    with ex -> Error("context: unparseable (" + ex.Message + ")")

/// Dispatch by repository-relative path (%P).
let mergeByPath (path: string) =
    let p = path.Replace('\\', '/')
    if p.EndsWith ".ros/events/events.jsonl" then Some mergeEvents
    elif p.EndsWith ".ros/context/current.json" then Some mergeContext
    else None
