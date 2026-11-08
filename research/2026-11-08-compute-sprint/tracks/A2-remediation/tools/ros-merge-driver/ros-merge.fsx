// EXPERIMENTAL Git merge driver for Praxis native history (SPR-A2-01). Prototype only.
// Configure (scratch clones only):
//   git config merge.ros-history.name "Praxis .ros history semantic merge"
//   git config merge.ros-history.driver "dotnet fsi /abs/path/ros-merge.fsx %O %A %B %P"
//   printf '%s\n' '.ros/context/current.json merge=ros-history' '.ros/events/events.jsonl merge=ros-history' >> .git/info/attributes
// Exit 0 = resolved (result written to %A). Exit 1 = refused: %A gets ordinary diff3 conflict markers.
#load "RosMerge.fs"
open System.IO
open System.Diagnostics

let fallbackConflict (ours: string) (baseF: string) (theirs: string) =
    let psi = ProcessStartInfo("git", UseShellExecute = false)
    [ "merge-file"; "-L"; "ours"; "-L"; "base"; "-L"; "theirs"; ours; baseF; theirs ] |> List.iter psi.ArgumentList.Add
    use p = Process.Start psi
    p.WaitForExit()

let run (argv: string list) =
    match argv with
    | [ baseF; ours; theirs; path ] ->
        match RosMerge.mergeByPath path with
        | None ->
            eprintfn "ros-merge: no semantic merge for %s" path
            fallbackConflict ours baseF theirs
            1
        | Some merge ->
            match merge (File.ReadAllText baseF) (File.ReadAllText ours) (File.ReadAllText theirs) with
            | Ok(text, mode) ->
                File.WriteAllText(ours, text)
                if mode <> "Strict" then eprintfn "ros-merge: %s %s" mode path
                0
            | Error why ->
                eprintfn "ros-merge: REFUSED %s: %s" path why
                fallbackConflict ours baseF theirs
                1
    | _ ->
        eprintfn "usage: dotnet fsi ros-merge.fsx %%O %%A %%B %%P"
        2

exit (run (fsi.CommandLineArgs |> Array.toList |> List.tail))
