// Inter-reviewer agreement and the disagreement list for adjudication (REVIEW.md).
//   dotnet fsi --quiet --exec agreement.fsx BUNDLE OUT_DIR
// Reads labels-R1-*.jsonl and labels-R2-*.jsonl; writes OUT_DIR/agreement.json and OUT_DIR/disagreements.jsonl
// (items where the reviewers differ on any decision label or on whether the change contains unauthorized behaviour).
open System
open System.IO
open System.Text.Json
open System.Text.Json.Nodes

let bundle, outDir = match fsi.CommandLineArgs |> Array.toList |> List.tail with [ b; o ] -> b, o | _ -> failwith "usage"
let str (n: JsonNode) (k: string) = match n.[k] with null -> None | v -> (try Some(v.GetValue<string>()) with _ -> None)
let items (n: JsonNode) (k: string) = match n.[k] with :? JsonArray as a -> a |> Seq.toList | _ -> []
let labels reviewer =
    Directory.GetFiles(bundle, $"labels-{reviewer}-batch-*.jsonl")
    |> Array.sort
    |> Array.collect File.ReadAllLines
    |> Array.choose (fun l -> try Some(JsonNode.Parse l) with _ -> None)
    |> Array.choose (fun n -> str n "key" |> Option.map (fun k -> k, n))
    |> Map.ofArray

let r1, r2 = labels "R1", labels "R2"
let keys = Set.intersect (r1 |> Map.keys |> Set.ofSeq) (r2 |> Map.keys |> Set.ofSeq) |> Set.toList

let decisionLabels (n: JsonNode) =
    items n "decisions" |> List.choose (fun d -> match str d "id", str d "label" with Some i, Some l -> Some(i, l) | _ -> None) |> Map.ofList
let unauthorized (n: JsonNode) = not (List.isEmpty (items n "unauthorizedBehaviour"))

let kappa (pairs: (string * string) list) =
    let n = float (List.length pairs)
    if n = 0.0 then nan
    else
        let po = (pairs |> List.filter (fun (a, b) -> a = b) |> List.length |> float) / n
        let cats = pairs |> List.collect (fun (a, b) -> [ a; b ]) |> List.distinct
        let pe = cats |> List.sumBy (fun c -> (pairs |> List.filter (fun (a, _) -> a = c) |> List.length |> float) / n * (pairs |> List.filter (fun (_, b) -> b = c) |> List.length |> float) / n)
        if pe = 1.0 then 1.0 else (po - pe) / (1.0 - pe)

let decisionPairs =
    keys |> List.collect (fun k ->
        let a, b = decisionLabels r1.[k], decisionLabels r2.[k]
        Set.intersect (a |> Map.keys |> Set.ofSeq) (b |> Map.keys |> Set.ofSeq) |> Set.toList |> List.map (fun i -> k, i, a.[i], b.[i]))
let binary (l: string) = if List.contains l [ "supported"; "recorded-assumption"; "implementation-defect" ] then "authorized" else "not-authorized"
let itemPairs = keys |> List.map (fun k -> k, unauthorized r1.[k], unauthorized r2.[k])

let num (x: float) : JsonNode = if Double.IsNaN x then null else JsonValue.Create(Math.Round(x, 4))
let agreement =
    JsonObject(
        [ "schema", (JsonValue.Create "cbe.vac-002-p2.review-agreement/1" :> JsonNode)
          "itemsBoth", (JsonValue.Create(List.length keys) :> JsonNode)
          "itemsR1Only", (JsonValue.Create(r1.Count - List.length keys) :> JsonNode)
          "itemsR2Only", (JsonValue.Create(r2.Count - List.length keys) :> JsonNode)
          "decisionsBoth", (JsonValue.Create(List.length decisionPairs) :> JsonNode)
          "decisionLabelAgreement", num (if List.isEmpty decisionPairs then nan else float (decisionPairs |> List.filter (fun (_, _, a, b) -> a = b) |> List.length) / float (List.length decisionPairs))
          "decisionLabelKappa", num (kappa (decisionPairs |> List.map (fun (_, _, a, b) -> a, b)))
          "decisionBinaryKappa", num (kappa (decisionPairs |> List.map (fun (_, _, a, b) -> binary a, binary b)))
          "itemUnauthorizedAgreement", num (if List.isEmpty itemPairs then nan else float (itemPairs |> List.filter (fun (_, a, b) -> a = b) |> List.length) / float (List.length itemPairs))
          "itemUnauthorizedKappa", num (kappa (itemPairs |> List.map (fun (_, a, b) -> string a, string b))) ]
        |> List.map (fun (k, v) -> Collections.Generic.KeyValuePair(k, v)))

Directory.CreateDirectory outDir |> ignore
File.WriteAllText(Path.Combine(outDir, "agreement.json"), agreement.ToJsonString(JsonSerializerOptions(WriteIndented = true)))
let disagreeing =
    keys |> List.filter (fun k ->
        let a, b = decisionLabels r1.[k], decisionLabels r2.[k]
        unauthorized r1.[k] <> unauthorized r2.[k] || (a |> Map.exists (fun i l -> b.TryFind i |> Option.exists ((<>) l))))
File.WriteAllLines(Path.Combine(outDir, "disagreements.jsonl"),
    disagreeing |> List.map (fun k -> JsonObject([ Collections.Generic.KeyValuePair("key", JsonValue.Create k :> JsonNode)
                                                   Collections.Generic.KeyValuePair("R1", r1.[k].DeepClone())
                                                   Collections.Generic.KeyValuePair("R2", r2.[k].DeepClone()) ]).ToJsonString()))
printfn "%d items, %d decisions, %d items to adjudicate" (List.length keys) (List.length decisionPairs) (List.length disagreeing)
