/// Binding a report to the exact evaluated content: git HEAD, cleanliness, a git-compatible
/// tree hash of the working tree, and sha256 digests.
module Archcheck.Provenance

open System
open System.IO
open System.Security.Cryptography
open System.Text

let sha256Hex (bytes: byte[]) =
    SHA256.HashData bytes |> Convert.ToHexString |> _.ToLowerInvariant()

let sha256File (path: string) = File.ReadAllBytes path |> sha256Hex

let private git (repo: string) (args: string list) =
    Exec.run repo "git" args (TimeSpan.FromMinutes 2.0)

let isGitWorkTree (repo: string) =
    let r = git repo [ "rev-parse"; "--is-inside-work-tree" ]
    r.ExitCode = 0 && r.Stdout.Trim() = "true"

let gitHead (repo: string) : string option =
    let r = git repo [ "rev-parse"; "--verify"; "HEAD" ]
    if r.ExitCode = 0 then Some(r.Stdout.Trim()) else None

/// Build output the verifier itself produces. Untracked files under a `bin/` or `obj/`
/// directory are never evaluated content, so a repository without a .gitignore for them
/// stays clean (and keeps its tree hash) across repeated runs. Tracked files are never
/// excluded.
let isBuildOutput (relativePath: string) =
    let segments = relativePath.Split '/'
    segments[.. segments.Length - 2] |> Array.exists (fun s -> s = "bin" || s = "obj")

/// No staged, unstaged or untracked (non-ignored, non-build-output) change under `repo`.
let treeClean (repo: string) : bool =
    let r = git repo [ "status"; "--porcelain=v1"; "-z"; "--untracked-files=all"; "--"; "." ]

    r.ExitCode = 0
    && r.Stdout.Split('\000')
       |> Array.map (fun entry -> entry.Trim('\r', '\n'))
       |> Array.filter (fun entry -> entry <> "")
       |> Array.forall (fun entry ->
           // Paths in porcelain output are relative to the repository root; the
           // bin/obj test only needs the segments.
           entry.StartsWith "?? " && isBuildOutput (Paths.normalize (entry.Substring 3)))

/// Files that make up the evaluated content, relative to `repo`: tracked plus untracked
/// non-ignored files that exist on disk. Outside git, every file not under an ignored
/// directory (`.git`, `bin`, `obj`, dot-directories).
let contentFiles (repo: string) : string list =
    if isGitWorkTree repo then
        let list (args: string list) =
            let code, bytes = Exec.runBytes repo "git" ([ "ls-files"; "-z" ] @ args @ [ "--"; "." ])

            if code <> 0 then
                failwith "git ls-files failed"

            Encoding.UTF8.GetString(bytes).Split('\000', StringSplitOptions.RemoveEmptyEntries)
            |> Array.map Paths.normalize

        let tracked = list [ "--cached" ]
        let untracked = list [ "--others"; "--exclude-standard" ] |> Array.filter (isBuildOutput >> not)

        Array.append tracked untracked
        |> Array.distinct
        |> Array.filter (fun p ->
            let full = Path.Combine(repo, p)
            File.Exists full || not (isNull (FileInfo full).LinkTarget))
        |> Array.sort
        |> List.ofArray
    else
        Directory.EnumerateFiles(repo, "*", SearchOption.AllDirectories)
        |> Seq.map (Paths.relative repo)
        |> Seq.filter (fun p ->
            let segments = p.Split '/'
            segments[.. segments.Length - 2] |> Array.exists Paths.isIgnoredSegment |> not)
        |> Seq.sort
        |> List.ofSeq

let private sha1 (bytes: byte[]) = SHA1.HashData bytes

let private gitObject (kind: string) (body: byte[]) =
    let header = Encoding.ASCII.GetBytes($"{kind} {body.Length}\000")
    sha1 (Array.append header body)

type private Entry =
    | Blob of mode: string * sha: byte[]
    | Tree of Map<string, Entry>

let private blobOf (full: string) : string * byte[] =
    let info = FileInfo full

    if not (isNull info.LinkTarget) then
        "120000", gitObject "blob" (Encoding.UTF8.GetBytes info.LinkTarget)
    else
        let executable =
            not (OperatingSystem.IsWindows())
            && (File.GetUnixFileMode full &&& UnixFileMode.UserExecute) = UnixFileMode.UserExecute

        (if executable then "100755" else "100644"), gitObject "blob" (File.ReadAllBytes full)

let rec private insert (segments: string list) (leaf: Entry) (tree: Map<string, Entry>) =
    match segments with
    | [] -> tree
    | [ name ] -> tree |> Map.add name leaf
    | dir :: rest ->
        let sub =
            match tree |> Map.tryFind dir with
            | Some(Tree t) -> t
            | _ -> Map.empty

        tree |> Map.add dir (Tree(insert rest leaf sub))

let rec private hashTree (tree: Map<string, Entry>) : byte[] =
    // Git orders tree entries by name, comparing a directory as if it ended in '/'.
    let sortKey (name, entry) =
        match entry with
        | Tree _ -> name + "/"
        | Blob _ -> name

    let body =
        tree
        |> Map.toList
        |> List.sortWith (fun a b -> String.CompareOrdinal(sortKey a, sortKey b))
        |> List.collect (fun (name, entry) ->
            let mode, sha =
                match entry with
                | Blob(mode, sha) -> mode, sha
                | Tree t -> "40000", hashTree t

            [ Encoding.ASCII.GetBytes(mode + " ")
              Encoding.UTF8.GetBytes(name + "\000")
              sha ])
        |> Array.concat

    gitObject "tree" body

/// The SHA-1 `git write-tree` would print if exactly `files` (relative to `repo`) were
/// staged with their current bytes and no clean filters. Nothing is written to `.git`.
let treeHash (repo: string) (files: string list) : string =
    files
    |> List.fold
        (fun tree rel ->
            let mode, sha = blobOf (Path.Combine(repo, rel))
            insert (rel.Split('/') |> List.ofArray) (Blob(mode, sha)) tree)
        Map.empty
    |> hashTree
    |> Convert.ToHexString
    |> _.ToLowerInvariant()

/// `dotnet --version` as resolved from `repo` (so it honours the repo's global.json).
let sdkVersion (dotnet: string) (repo: string) : string =
    let r = Exec.run repo dotnet [ "--version" ] (TimeSpan.FromMinutes 1.0)
    if r.ExitCode = 0 then r.Stdout.Trim() else "unknown"
