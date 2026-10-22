// VAC-002 plots: the eight required figures as static SVG, from RESULTS/RUN/analysis.json only.
//   dotnet fsi --quiet --exec plots.fsx RESULTS/RUN/analysis.json OUT_DIR
// Rules (dataviz method): one y-axis per chart; arms keep fixed colour slots (A..F = slots 1..6, never by rank);
// a legend plus direct labels, so identity is never colour alone; missing or inconclusive data is written on the
// chart, never drawn as a point. Light surface, with a prefers-color-scheme dark variant.
open System
open System.IO
open System.Text.Json.Nodes

let analysis = JsonNode.Parse(File.ReadAllText(fsi.CommandLineArgs[1]))
let outDir = fsi.CommandLineArgs[2]
Directory.CreateDirectory outDir |> ignore

let arms = [ "A"; "B"; "C"; "D"; "E"; "F" ]
let armNames = Map.ofList [ "A", "A fresh"; "B", "B long-lived"; "C", "C + Ordo"; "D", "D full"; "E", "E adaptive"; "F", "F restarted" ]
let slot = Map.ofList [ "A", 1; "B", 2; "C", 3; "D", 4; "E", 5; "F", 6 ]
let armData (a: string) = match analysis["arms"].[a] with null -> None | n -> Some n
let present = arms |> List.filter (armData >> Option.isSome)
let num (n: JsonNode) (k: string) = match n with null -> None | _ -> match n[k] with :? JsonValue as v -> (try Some(v.GetValue<decimal>()) with _ -> None) | _ -> None
let items (n: JsonNode) (k: string) = match n with null -> [] | _ -> match n[k] with :? JsonArray as a -> a |> Seq.filter (isNull >> not) |> Seq.toList | _ -> []
let bool (n: JsonNode) (k: string) = match n with null -> false | _ -> match n[k] with :? JsonValue as v -> (try v.GetValue<bool>() with _ -> false) | _ -> false
let esc (s: string) = s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
let f1 (d: float) = d.ToString("0.#", Globalization.CultureInfo.InvariantCulture)

let style =
    """<style>
  svg { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .bg { fill: #fcfcfb; } .t1 { fill: #0b0b0b; } .t2 { fill: #52514e; } .t3 { fill: #8a8984; }
  .grid { stroke: #e6e5e0; stroke-width: 1; } .axis { stroke: #b9b8b1; stroke-width: 1; }
  .s1 { fill: #2a78d6; stroke: #2a78d6; } .s2 { fill: #eb6834; stroke: #eb6834; } .s3 { fill: #1baf7a; stroke: #1baf7a; }
  .s4 { fill: #eda100; stroke: #eda100; } .s5 { fill: #e87ba4; stroke: #e87ba4; } .s6 { fill: #008300; stroke: #008300; }
  .ok { fill: #1baf7a; } .bad { fill: #e34948; } .na { fill: none; stroke: #b9b8b1; stroke-width: 1.5; }
  .ring { stroke: #fcfcfb; stroke-width: 2; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1a1a19; } .t1 { fill: #f0efec; } .t2 { fill: #c3c2b7; } .t3 { fill: #8f8e86; }
    .grid { stroke: #2e2e2c; } .axis { stroke: #55544f; } .ring { stroke: #1a1a19; }
    .s1 { fill: #3987e5; stroke: #3987e5; } .s2 { fill: #d95926; stroke: #d95926; } .s3 { fill: #199e70; stroke: #199e70; }
    .s4 { fill: #c98500; stroke: #c98500; } .s5 { fill: #d55181; stroke: #d55181; } .s6 { fill: #008300; stroke: #008300; }
    .ok { fill: #199e70; } .bad { fill: #e66767; }
  }
</style>"""

let svg (w: int) (h: int) (title: string) (subtitle: string) (body: string list) (note: string) =
    let header =
        [ sprintf "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 %d %d\" width=\"%d\" height=\"%d\" role=\"img\" aria-label=\"%s\">" w h w h (esc title)
          style
          sprintf "<rect class=\"bg\" x=\"0\" y=\"0\" width=\"%d\" height=\"%d\" rx=\"8\"/>" w h
          sprintf "<text class=\"t1\" x=\"20\" y=\"28\" font-size=\"15\" font-weight=\"600\">%s</text>" (esc title)
          sprintf "<text class=\"t2\" x=\"20\" y=\"47\" font-size=\"12\">%s</text>" (esc subtitle) ]
    let footer = [ sprintf "<text class=\"t3\" x=\"20\" y=\"%d\" font-size=\"11\">%s</text>" (h - 10) (esc note); "</svg>" ]
    String.concat "\n" (header @ body @ footer)

let write (name: string) (content: string) = File.WriteAllText(Path.Combine(outDir, name), content)

/// Horizontal bars, one per arm (one series, the arm named on each bar); missing values are written, not drawn.
let barChart name title subtitle unitLabel (value: string -> float option) (fmt: float -> string) note =
    let w, rowH, left, top = 640, 30, 130, 70
    let h = top + rowH * present.Length + 50
    let vmax = present |> List.choose value |> fun vs -> if List.isEmpty vs then 1.0 else max 1e-9 (List.max vs)
    let plotW = float (w - left - 110)
    let rows =
        present |> List.mapi (fun i a ->
            let y = top + i * rowH
            let label = sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">%s</text>" (left - 8) (y + 16) (esc armNames[a])
            match value a with
            | Some v ->
                let bw = if v = 0.0 then 0.0 else max 2.0 (plotW * v / vmax)
                [ label
                  if bw = 0.0 then "" else sprintf "<rect class=\"s%d\" x=\"%d\" y=\"%d\" width=\"%s\" height=\"18\" rx=\"4\"/>" slot[a] left (y + 3) (f1 bw)
                  sprintf "<text class=\"t2\" x=\"%s\" y=\"%d\" font-size=\"12\">%s</text>" (f1 (float left + bw + 6.0)) (y + 16) (esc (fmt v)) ]
            | None -> [ label; sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"12\">unavailable</text>" (left + 4) (y + 16) ])
        |> List.concat
    let axis = [ sprintf "<line class=\"axis\" x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"/>" left (top - 4) left (top + rowH * present.Length)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">%s</text>" left (top - 10) (esc unitLabel) ]
    write name (svg w h title subtitle (axis @ rows) note)

let armVal a k = armData a |> Option.bind (fun n -> num n k) |> Option.map float
let perUnit a = armData a |> Option.map (fun n -> items n "perUnit") |> Option.defaultValue []

// 1. Cost per accepted requirement by arm
barChart "1-cost-per-accepted-requirement.svg" "Cost per accepted requirement" "Pilot P1, one 12-unit chain per arm; CLI list-price estimate (USD)"
    "USD per accepted requirement" (fun a -> armVal a "costPerAcceptedRequirement") (fun v -> "$" + v.ToString("0.000", Globalization.CultureInfo.InvariantCulture))
    "Descriptive; no interval with one chain per arm. 'unavailable' = no accepted requirement or cost missing."

// 2. Error by chain position: a dot grid, arm x position (accepted / not accepted / not run)
let positions = present |> List.collect perUnit |> List.choose (fun u -> num u "position") |> List.map int |> fun ps -> if List.isEmpty ps then [ 1 ] else [ 1 .. List.max ps ]
let gridChart name title subtitle (status: JsonNode -> string) (legend: (string * string) list) note =
    let left, top, cell = 130, 96, 34
    let w = left + cell * positions.Length + 40
    let h = top + cell * present.Length + 70
    let header = positions |> List.map (fun p -> sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"11\" text-anchor=\"middle\">%d</text>" (left + (p - 1) * cell + cell / 2) (top - 8) p)
    let rows =
        present |> List.mapi (fun i a ->
            let y = top + i * cell
            let us = perUnit a
            sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">%s</text>" (left - 8) (y + cell / 2 + 4) (esc armNames[a])
            :: (positions |> List.map (fun p ->
                let cx, cy = left + (p - 1) * cell + cell / 2, y + cell / 2
                match us |> List.tryFind (fun u -> num u "position" = Some(decimal p)) with
                | Some u -> sprintf "<circle class=\"%s ring\" cx=\"%d\" cy=\"%d\" r=\"9\"><title>%s %d %s: %s</title></circle>" (status u) cx cy a p (u["task"].GetValue<string>()) (status u)
                | None -> sprintf "<circle class=\"na\" cx=\"%d\" cy=\"%d\" r=\"8\"><title>not run</title></circle>" cx cy)))
        |> List.concat
    let leg = legend |> List.mapi (fun i (cls, text) ->
                [ sprintf "<circle class=\"%s\" cx=\"%d\" cy=\"%d\" r=\"6\"/>" cls (left + i * 150) (h - 38)
                  sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"12\">%s</text>" (left + i * 150 + 12) (h - 34) (esc text) ]) |> List.concat
    let xlab = sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">chain position</text>" left (top - 24)
    write name (svg w h title subtitle (xlab :: header @ rows @ leg) note)

gridChart "2-error-by-chain-position.svg" "Unit failures by chain position" "Pilot P1: a filled red dot = the unit was not accepted by the hidden oracle"
    (fun u -> if bool u "accepted" then "ok" else "bad") [ "ok", "accepted"; "bad", "not accepted"; "na", "not run" ]
    "Position and task are confounded in one fixed-order chain; compare arms within a column."

// 3. Architectural violations by arm
barChart "3-architectural-violations.svg" "Architectural violations at the final head" "Units whose head has an archcheck DET finding (severity >= 2)"
    "units with a violation" (fun a -> armData a |> Option.map (fun n -> float (items n "unitsWithDetViolation").Length)) (fun v -> sprintf "%.0f" v)
    "Counts over 12 units per arm; ARCH-001's compiler-resolved verifier, full Lending policy."

// 4. Error propagation depth: origin x arm grid of depth numbers
let origins = present |> List.collect (fun a -> armData a |> Option.map (fun n -> items n "propagation" |> List.map (fun p -> p["origin"].GetValue<string>())) |> Option.defaultValue []) |> List.distinct
/// Optional manual inspection beside analysis.json: matches judged not to be propagation (the computed depth is kept).
let notPropagation =
    let path = Path.Combine(Path.GetDirectoryName(Path.GetFullPath fsi.CommandLineArgs[1]), "propagation-adjudication.json")
    if File.Exists path then
        items (JsonNode.Parse(File.ReadAllText path)) "entries"
        |> List.filter (fun e -> e["verdict"].GetValue<string>() = "not-propagation")
        |> List.map (fun e -> e["arm"].GetValue<string>(), e["origin"].GetValue<string>())
    else []
let propChart () =
    let left, top, cw, rh = 230, 80, 64, 30
    let w = left + cw * present.Length + 30
    let h = top + rh * max 1 origins.Length + 50
    let header = present |> List.mapi (fun i a -> sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"middle\">%s</text>" (left + i * cw + cw / 2) (top - 10) a)
    let rows =
        origins |> List.mapi (fun j o ->
            let y = top + j * rh
            sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">%s</text>" (left - 10) (y + 18) (esc o)
            :: (present |> List.mapi (fun i a ->
                let d = armData a |> Option.bind (fun n -> items n "propagation" |> List.tryFind (fun p -> p["origin"].GetValue<string>() = o)) |> Option.bind (fun p -> num p "depth")
                let cx = left + i * cw + cw / 2
                let rejected = notPropagation |> List.filter ((=) (a, o)) |> List.length |> decimal
                match d with
                | Some v when v > 0m && rejected > 0m ->
                    sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"middle\">%M → %M*</text>" cx (y + 18) v (max 0m (v - rejected))
                | Some v when v > 0m -> sprintf "<rect class=\"s%d\" x=\"%d\" y=\"%d\" width=\"%s\" height=\"16\" rx=\"4\"/><text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"middle\">%M</text>" slot[a] (cx - 20) (y + 5) (f1 (min 40.0 (8.0 * float v))) cx (y + 18) v
                | Some _ -> sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"middle\">0</text>" cx (y + 18)
                | None -> sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\" text-anchor=\"middle\">n/a</text>" cx (y + 18))))
        |> List.concat
    write "4-error-propagation-depth.svg" (svg w h "Error propagation depth" "Later units whose failures or decisions trace to the origin (METRICS.md section 5)" (header @ rows) (if List.isEmpty notPropagation then "n/a = origin not reached (chain stopped earlier)." else "a → b*: a computed by lexical match, b after inspection (propagation-adjudication.json)."))
propChart ()

// 5. Verification cost vs escape rate
let gateSeconds a = armData a |> Option.bind (fun n -> num n "gateMs") |> Option.map (fun ms -> float ms / 1000.0)
let escapeRate a = armData a |> Option.bind (fun n -> match num n "units", num n "unitFailures" with Some u, Some f when u > 0m -> Some(float f / float u) | _ -> None)
/// One row per arm: a bar of host gate time with the arm's escaped-error count written beside it. With every escape
/// rate at 0 there is no trade-off to plot as a scatter (points would coincide on the x axis), so the escape rate is
/// stated in text, never drawn as an invented position.
let costVsEscape () =
    let w, rowH, left, top = 640, 30, 130, 70
    let h = top + rowH * present.Length + 50
    let vmax = present |> List.choose gateSeconds |> List.fold max 1.0
    let plotW = float (w - left - 200)
    let escaped a = armData a |> Option.map (fun n -> sprintf "escaped %s/%s" (num n "unitFailures" |> Option.map string |> Option.defaultValue "?") (num n "units" |> Option.map string |> Option.defaultValue "?"))
    let rows =
        present |> List.mapi (fun i a ->
            let y = top + i * rowH
            let label = sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">%s</text>" (left - 8) (y + 16) (esc armNames[a])
            let esc' = escaped a |> Option.defaultValue "escape unavailable"
            match gateSeconds a with
            | Some s when s > 0.0 ->
                let bw = plotW * s / vmax
                [ label
                  sprintf "<rect class=\"s%d\" x=\"%d\" y=\"%d\" width=\"%s\" height=\"18\" rx=\"4\"><title>%s: %s s, %s</title></rect>" slot[a] left (y + 3) (f1 bw) armNames[a] (f1 s) esc'
                  sprintf "<text class=\"t2\" x=\"%s\" y=\"%d\" font-size=\"12\">%s s · %s</text>" (f1 (float left + bw + 6.0)) (y + 16) (f1 s) (esc esc') ]
            | _ -> [ label; sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"12\">no gate · %s</text>" (left + 4) (y + 16) (esc esc') ])
        |> List.concat
    let axis = [ sprintf "<line class=\"axis\" x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"/>" left (top - 4) left (top + rowH * present.Length)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">gate CPU seconds (host), total over the chain</text>" left (top - 10) ]
    let allZero = present |> List.forall (fun a -> escapeRate a = Some 0.0)
    let note = if allZero then "Escape rate is 0 in every arm, so no cost-versus-escape trade-off exists in this run. Model cost: figure 1."
               else "Escaped = units not accepted by the hidden oracle. Model cost: figure 1."
    write "5-verification-cost-vs-escape.svg" (svg w h "Verification cost vs escaped errors" "Host gate time per arm, with the units that escaped (not accepted)" (axis @ rows) note)
costVsEscape ()

// 6. Survival by arm: step lines from the Kaplan-Meier steps
let survival () =
    let w, h, left, top, pw, ph = 680, 400, 70, 80, 480, 240
    let maxPos = float (List.max positions)
    let px p = float left + float pw * p / maxPos
    let py s = float (top + ph) - float ph * s
    let lines =
        present |> List.mapi (fun i a ->
            let steps = match analysis["kaplanMeier"].[a] with :? JsonArray as arr -> arr |> Seq.map (fun s -> float (s["position"].GetValue<decimal>()), float (s["survival"].GetValue<decimal>())) |> Seq.toList | _ -> []
            let censor = armData a |> Option.bind (fun n -> num n["survival"] "censoredAt") |> Option.map float |> Option.defaultValue maxPos
            let pts = steps |> List.pairwise |> List.collect (fun ((t0, s0), (t1, s1)) -> [ t1, s0; t1, s1 ])
            let all = (0.0, 1.0) :: pts @ [ censor, (steps |> List.last |> snd) ]
            let off = float i * 1.5   // small vertical offset so identical curves stay distinguishable
            let d = all |> List.mapi (fun j (t, s) -> sprintf "%s%s %s" (if j = 0 then "M" else "L") (f1 (px t)) (f1 (py s - off))) |> String.concat " "
            let (lt, ls) = List.last all
            [ sprintf "<path class=\"s%d\" fill=\"none\" stroke-width=\"2\" d=\"%s\" style=\"fill:none\"/>" slot[a] d
              sprintf "<text class=\"t1\" x=\"%s\" y=\"%s\" font-size=\"11\">%s</text>" (f1 (px lt + 6.0)) (f1 (py ls - off + float i * 13.0 + 4.0)) (esc armNames[a]) ])
        |> List.concat
    let axes = [ sprintf "<line class=\"axis\" x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"/>" left (top + ph) (left + pw) (top + ph)
                 sprintf "<line class=\"axis\" x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"/>" left top left (top + ph)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">chain position</text>" (left + pw - 90) (top + ph + 28)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">share of chains without a critical failure</text>" left (top - 10)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"10\" text-anchor=\"end\">1</text>" (left - 6) (top + 4)
                 sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"10\" text-anchor=\"end\">0</text>" (left - 6) (top + ph) ]
    write "6-survival-by-arm.svg" (svg w h "Agent survival to the first critical failure" "Kaplan-Meier, one chain per arm: each curve is a single step or censored" (axes @ lines) "Critical = false completion, regression or broken build at head. One chain per arm: not an estimate of a rate.")
survival ()

// 7. Context size vs error: units as points, accepted vs not (two classes)
let ctxChart () =
    let w, h, left, top, pw, ph = 640, 380, 110, 70, 480, 240
    let us = present |> List.collect (fun a -> perUnit a |> List.choose (fun u -> num u "contextLast" |> Option.filter (fun c -> c > 0m) |> Option.map (fun c -> a, float c, bool u "accepted")))
    let xmax = us |> List.map (fun (_, c, _) -> c) |> fun v -> if List.isEmpty v then 1.0 else List.max v * 1.1
    let px c = float left + float pw * c / xmax
    let rnd = Random(20261022)
    let marks = us |> List.map (fun (a, c, ok) ->
                    let y = float (top + (if ok then 70 else 170)) + rnd.NextDouble() * 50.0
                    sprintf "<circle class=\"%s ring\" cx=\"%s\" cy=\"%s\" r=\"5\"><title>%s, context %s tokens, %s</title></circle>" (if ok then "ok" else "bad") (f1 (px c)) (f1 y) a (f1 c) (if ok then "accepted" else "not accepted"))
    let labels = [ sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">accepted</text>" (left - 8) (top + 100)
                   sprintf "<text class=\"t2\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">not accepted</text>" (left - 8) (top + 200)
                   sprintf "<line class=\"axis\" x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"/>" left (top + ph) (left + pw) (top + ph)
                   sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">prompt tokens at the unit's last request</text>" left (top + ph + 34) ]
    let ticks = [ 0.0 .. 50000.0 .. xmax ] |> List.map (fun v ->
                    sprintf "<line class=\"axis\" x1=\"%s\" y1=\"%d\" x2=\"%s\" y2=\"%d\"/><text class=\"t3\" x=\"%s\" y=\"%d\" font-size=\"10\" text-anchor=\"middle\">%sk</text>" (f1 (px v)) (top + ph) (f1 (px v)) (top + ph + 4) (f1 (px v)) (top + ph + 16) (f1 (v / 1000.0)))
    let none = if us |> List.exists (fun (_, _, ok) -> not ok) || List.isEmpty us then [] else [ sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"11\">no unit was not accepted</text>" (left + 10) (top + 200) ]
    let empty = if List.isEmpty us then [ sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"12\">no context measurements</text>" (left + 10) (top + 40) ] else []
    write "7-context-size-vs-error.svg" (svg w h "Context size and unit outcome" "Each dot is one unit; vertical jitter only separates dots" (labels @ ticks @ marks @ none @ empty) "Observational: context size grows with position and task, so no causal reading.")
ctxChart ()

// 8. Adaptive escalation frequency and cost (Arm E)
let escalation () =
    let us = perUnit "E"
    let tiers = [ "low"; "medium"; "high" ]
    let count t = us |> List.filter (fun u -> (match u["tier"] with null -> "" | v -> v.GetValue<string>()) = t) |> List.length
    let cost t = us |> List.filter (fun u -> (match u["tier"] with null -> "" | v -> v.GetValue<string>()) = t) |> List.choose (fun u -> num u "costUsdCli") |> List.sum
    let w, h, left, top, rowH = 640, 230, 110, 70, 40
    let maxc = tiers |> List.map count |> List.fold max 1
    let rows = tiers |> List.mapi (fun i t ->
                 let y = top + i * rowH
                 let bw = 380.0 * float (count t) / float maxc
                 [ sprintf "<text class=\"t1\" x=\"%d\" y=\"%d\" font-size=\"12\" text-anchor=\"end\">%s</text>" (left - 8) (y + 17) t
                   (if count t = 0 then "" else sprintf "<rect class=\"s5\" x=\"%d\" y=\"%d\" width=\"%s\" height=\"20\" rx=\"4\"/>" left (y + 3) (f1 (max 2.0 bw)))
                   sprintf "<text class=\"t2\" x=\"%s\" y=\"%d\" font-size=\"12\">%d units, $%s agent cost</text>" (f1 (float left + bw + 8.0)) (y + 17) (count t) ((cost t).ToString("0.00", Globalization.CultureInfo.InvariantCulture)) ])
               |> List.concat
    let empty = if List.isEmpty us then [ sprintf "<text class=\"t3\" x=\"%d\" y=\"%d\" font-size=\"12\">Arm E did not run</text>" left top ] else []
    write "8-adaptive-escalation.svg" (svg w h "Arm E: escalation tier per unit" "Tier chosen by the frozen policy 1.0.0 from observable signals" (rows @ empty) "Cost is the agent's cost of the units at that tier (repair turns included), not the gate's CPU time.")
escalation ()
printfn "8 figures written to %s" outDir
