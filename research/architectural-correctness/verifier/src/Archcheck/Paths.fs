/// Path and name helpers. Pure.
module Archcheck.Paths

open System
open System.IO

/// Forward slashes, no trailing separator.
let normalize (p: string) = p.Replace('\\', '/').TrimEnd('/')

let full (p: string) = Path.GetFullPath p |> normalize

/// `path` relative to `root`, with forward slashes; both must be absolute.
let relative (root: string) (path: string) =
    Path.GetRelativePath(root, path) |> normalize

/// `path` is `dir` or lies beneath it (string comparison on full, normalised paths).
let isUnder (dir: string) (path: string) =
    let d = full dir
    let p = full path
    p = d || p.StartsWith(d + "/", StringComparison.Ordinal)

/// Dotted-name containment: `name` is `prefix` or a member of it (`System.IO` covers
/// `System.IO.File.ReadAllText`, but not `System.IOX`).
let isWithin (prefix: string) (name: string) =
    name = prefix || name.StartsWith(prefix + ".", StringComparison.Ordinal)

/// `*` matches any run of characters; everything else is literal and case-sensitive.
let wildcard (pattern: string) (text: string) =
    let parts = pattern.Split '*'

    if parts.Length = 1 then
        pattern = text
    else
        let first = parts[0]
        let last = parts[parts.Length - 1]

        if not (text.StartsWith(first, StringComparison.Ordinal) && text.EndsWith(last, StringComparison.Ordinal)) then
            false
        elif text.Length < first.Length + last.Length then
            false
        else
            let middle = text.Substring(first.Length, text.Length - first.Length - last.Length)

            parts[1 .. parts.Length - 2]
            |> Array.fold
                (fun (ok, rest: string) part ->
                    if not ok then
                        false, rest
                    else
                        match rest.IndexOf(part, StringComparison.Ordinal) with
                        | -1 -> false, rest
                        | i -> true, rest.Substring(i + part.Length))
                (true, middle)
            |> fst

/// Directories never treated as source: build output, VCS metadata, tool state.
let isIgnoredSegment (segment: string) =
    segment = "bin" || segment = "obj" || segment = "node_modules" || segment.StartsWith "."
