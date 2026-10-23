// VAC-002-P3 Stage 2 sample size (PREREGISTRATION.md §5), by simulation of the primary test.
//   dotnet fsi --quiet --exec sizing.fsx PA PB "R1,R2,...,Rk" SIMS SEED
// PA, PB: the design rates (p_A = 0.75 × the Stage 1 confirmed rate; p_B = the sizing-run rate, floored at 0.02).
// R1..Rk: Stage 1 per-scenario arm-A rates, resampled for scenario heterogeneity (rescaled so their mean is PA; arm B's
// scenario rate keeps the same ratio PB/PA). Each block is one (scenario, replicate) with one opportunity per arm.
// Primary test: exchange arm labels within blocks; with one binary outcome per arm per block, that is the exact
// sign-flip (conditional McNemar) test on the discordant blocks, two-sided α = 0.05.
open System

let args = fsi.CommandLineArgs |> Array.toList |> List.tail
let pA, pB, rates, sims, seed =
    match args with
    | [ a; b; r; s; sd ] -> float a, float b, (r.Split(',') |> Array.map float |> Array.toList), int s, int sd
    | _ -> failwith "usage: PA PB R1,R2,.. SIMS SEED"

let logChoose (n: int) (k: int) =
    let lf (x: int) = [ 1 .. x ] |> List.sumBy (fun i -> log (float i))
    lf n - lf k - lf (n - k)

/// Two-sided exact p-value for d1 discordant blocks favouring one arm out of d discordant blocks.
let exactP (d1: int) (d: int) =
    if d = 0 then 1.0
    else
        let pk k = exp (logChoose d k - float d * log 2.0)
        let observed = pk d1
        [ 0 .. d ] |> List.sumBy (fun k -> if pk k <= observed + 1e-12 then pk k else 0.0) |> min 1.0

let meanRate = List.average rates
let scaled = rates |> List.map (fun r -> if meanRate = 0.0 then pA else min 1.0 (r * pA / meanRate))

let power (rng: Random) (blocks: int) =
    let one () =
        let outcomes =
            [ 1 .. blocks ]
            |> List.map (fun _ ->
                let qa = scaled.[rng.Next(List.length scaled)]
                let qb = qa * pB / pA
                (rng.NextDouble() < qa), (rng.NextDouble() < qb))
        let aOnly = outcomes |> List.filter (fun (a, b) -> a && not b) |> List.length
        let bOnly = outcomes |> List.filter (fun (a, b) -> b && not a) |> List.length
        exactP bOnly (aOnly + bOnly) < 0.05 && aOnly > bOnly
    let hits = [ 1 .. sims ] |> List.filter (fun _ -> one ()) |> List.length
    float hits / float sims

let rng = Random(seed)
let table = [ 4 .. 40 ] |> List.map (fun n -> n, power rng n)
table |> List.iter (fun (n, p) -> printfn "blocks=%2d power=%.3f" n p)
match table |> List.tryFind (fun (_, p) -> p >= 0.80) with
| Some(n, p) -> printfn "SMALLEST blocks=%d power=%.3f (pA=%.3f pB=%.3f, scenario rates scaled=%A)" n p pA pB scaled
| None -> printfn "NO DESIGN UP TO 40 BLOCKS REACHES 0.80"
