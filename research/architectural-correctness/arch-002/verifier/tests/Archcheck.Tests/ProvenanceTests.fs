module Archcheck.Tests.ProvenanceTests

open System
open System.IO
open Xunit
open Archcheck

let private git (dir: string) (args: string list) =
    let r =
        Exec.run dir "git" ([ "-c"; "user.name=t"; "-c"; "user.email=t@invalid"; "-c"; "commit.gpgsign=false" ] @ args) (TimeSpan.FromMinutes 1.0)

    Assert.True((r.ExitCode = 0), r.Stderr)
    r.Stdout.Trim()

[<Fact>]
let ``tree hash equals git write-tree, including untracked files, modes and ignores`` () =
    let dir = Path.Combine(Path.GetTempPath(), "archcheck-tree-" + Guid.NewGuid().ToString("N"))
    Directory.CreateDirectory(Path.Combine(dir, "src", "a b")) |> ignore

    try
        git dir [ "init"; "-q" ] |> ignore
        File.WriteAllText(Path.Combine(dir, ".gitignore"), "bin/\n")
        File.WriteAllText(Path.Combine(dir, "README.md"), "hello\n")
        File.WriteAllText(Path.Combine(dir, "src", "a b", "x.fs"), "let x = 1\n")
        File.WriteAllText(Path.Combine(dir, "src", "a.fs"), "let a = 1\n")
        File.WriteAllText(Path.Combine(dir, "run.sh"), "#!/bin/sh\n")
        File.SetUnixFileMode(Path.Combine(dir, "run.sh"), UnixFileMode.UserRead ||| UnixFileMode.UserWrite ||| UnixFileMode.UserExecute)
        git dir [ "add"; "-A" ] |> ignore
        git dir [ "commit"; "-q"; "-m"; "x" ] |> ignore
        Assert.True(Provenance.treeClean dir)

        // Untracked and ignored content after the commit.
        File.WriteAllText(Path.Combine(dir, "new.fs"), "let n = 1\n")
        Directory.CreateDirectory(Path.Combine(dir, "bin")) |> ignore
        File.WriteAllText(Path.Combine(dir, "bin", "out.dll"), "ignored")
        Assert.False(Provenance.treeClean dir)

        let ours = Provenance.treeHash dir (Provenance.contentFiles dir)
        git dir [ "add"; "-A" ] |> ignore
        Assert.Equal(git dir [ "write-tree" ], ours)
    finally
        Directory.Delete(dir, true)

[<Fact>]
let ``untracked build output does not dirty the tree or change its hash`` () =
    let dir = Path.Combine(Path.GetTempPath(), "archcheck-obj-" + Guid.NewGuid().ToString("N"))
    Directory.CreateDirectory(Path.Combine(dir, "src")) |> ignore

    try
        git dir [ "init"; "-q" ] |> ignore
        File.WriteAllText(Path.Combine(dir, "src", "a.fs"), "let a = 1\n")
        git dir [ "add"; "-A" ] |> ignore
        git dir [ "commit"; "-q"; "-m"; "x" ] |> ignore
        let before = Provenance.treeHash dir (Provenance.contentFiles dir)
        // No .gitignore: a build leaves bin/ and obj/ untracked.
        Directory.CreateDirectory(Path.Combine(dir, "src", "obj")) |> ignore
        File.WriteAllText(Path.Combine(dir, "src", "obj", "project.assets.json"), "{}")
        Assert.True(Provenance.treeClean dir)
        Assert.Equal(before, Provenance.treeHash dir (Provenance.contentFiles dir))
        Assert.Equal(git dir [ "rev-parse"; "HEAD^{tree}" ], before)
        // A real untracked source file still counts.
        File.WriteAllText(Path.Combine(dir, "src", "b.fs"), "let b = 1\n")
        Assert.False(Provenance.treeClean dir)
    finally
        Directory.Delete(dir, true)
