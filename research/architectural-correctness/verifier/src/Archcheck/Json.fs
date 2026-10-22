/// A small JSON value type with a deterministic writer.
///
/// Objects keep their declared member order, numbers are integers or invariant-culture
/// decimals, strings are escaped the same way on every platform, and output uses LF and
/// two-space indentation. Reading goes through System.Text.Json and is converted into the
/// same value type so decoding is ordinary pattern matching.
module Archcheck.Json

open System
open System.Globalization
open System.Text
open System.Text.Json

type JsonValue =
    | JNull
    | JBool of bool
    | JInt of int64
    | JNumber of decimal
    | JString of string
    | JArray of JsonValue list
    | JObject of (string * JsonValue) list

let str s = JString s
let num (n: int) = JInt(int64 n)
let obj members = JObject members
let arr items = JArray items
let strOpt = Option.map JString >> Option.defaultValue JNull

let private escape (sb: StringBuilder) (s: string) =
    sb.Append '"' |> ignore

    for c in s do
        match c with
        | '"' -> sb.Append "\\\"" |> ignore
        | '\\' -> sb.Append "\\\\" |> ignore
        | '\n' -> sb.Append "\\n" |> ignore
        | '\r' -> sb.Append "\\r" |> ignore
        | '\t' -> sb.Append "\\t" |> ignore
        | c when c < ' ' -> sb.AppendFormat(CultureInfo.InvariantCulture, "\\u{0:x4}", int c) |> ignore
        | c -> sb.Append c |> ignore

    sb.Append '"' |> ignore

/// Pretty-printed, deterministic rendering terminated by a newline.
let render (value: JsonValue) : string =
    let sb = StringBuilder()
    let indent n = sb.Append(String(' ', 2 * n)) |> ignore

    let rec write depth v =
        match v with
        | JNull -> sb.Append "null" |> ignore
        | JBool b -> sb.Append(if b then "true" else "false") |> ignore
        | JInt n -> sb.Append(n.ToString CultureInfo.InvariantCulture) |> ignore
        | JNumber d -> sb.Append(d.ToString CultureInfo.InvariantCulture) |> ignore
        | JString s -> escape sb s
        | JArray [] -> sb.Append "[]" |> ignore
        | JObject [] -> sb.Append "{}" |> ignore
        | JArray items ->
            sb.Append "[\n" |> ignore

            items
            |> List.iteri (fun i item ->
                if i > 0 then sb.Append ",\n" |> ignore
                indent (depth + 1)
                write (depth + 1) item)

            sb.Append '\n' |> ignore
            indent depth
            sb.Append ']' |> ignore
        | JObject members ->
            sb.Append "{\n" |> ignore

            members
            |> List.iteri (fun i (k, item) ->
                if i > 0 then sb.Append ",\n" |> ignore
                indent (depth + 1)
                escape sb k
                sb.Append ": " |> ignore
                write (depth + 1) item)

            sb.Append '\n' |> ignore
            indent depth
            sb.Append '}' |> ignore

    write 0 value
    sb.Append('\n').ToString()

let rec private ofElement (e: JsonElement) : JsonValue =
    match e.ValueKind with
    | JsonValueKind.Null
    | JsonValueKind.Undefined -> JNull
    | JsonValueKind.True -> JBool true
    | JsonValueKind.False -> JBool false
    | JsonValueKind.String -> JString(e.GetString())
    | JsonValueKind.Number ->
        match e.TryGetInt64() with
        | true, n -> JInt n
        | _ -> JNumber(e.GetDecimal())
    | JsonValueKind.Array -> e.EnumerateArray() |> Seq.map ofElement |> List.ofSeq |> JArray
    | _ -> e.EnumerateObject() |> Seq.map (fun p -> p.Name, ofElement p.Value) |> List.ofSeq |> JObject

let parse (text: string) : Result<JsonValue, string> =
    try
        use doc =
            JsonDocument.Parse(text, JsonDocumentOptions(CommentHandling = JsonCommentHandling.Skip))

        Ok(ofElement doc.RootElement)
    with :? JsonException as ex ->
        Error ex.Message

// ---- decoding helpers -------------------------------------------------------------------

let member' name (v: JsonValue) =
    match v with
    | JObject ms -> ms |> List.tryFind (fst >> (=) name) |> Option.map snd
    | _ -> None

let asString =
    function
    | JString s -> Some s
    | _ -> None

let asInt =
    function
    | JInt n -> Some(int n)
    | _ -> None

let asList =
    function
    | JArray xs -> Some xs
    | _ -> None

let stringList name v : Result<string list, string> =
    match member' name v with
    | None
    | Some JNull -> Ok []
    | Some(JArray xs) ->
        let strings = xs |> List.choose asString

        if strings.Length = xs.Length then
            Ok strings
        else
            Error $"'{name}' must be an array of strings"
    | Some _ -> Error $"'{name}' must be an array of strings"

let intList name v : Result<int list, string> =
    match member' name v with
    | None
    | Some JNull -> Ok []
    | Some(JArray xs) ->
        let ints = xs |> List.choose asInt

        if ints.Length = xs.Length then
            Ok ints
        else
            Error $"'{name}' must be an array of integers"
    | Some _ -> Error $"'{name}' must be an array of integers"
