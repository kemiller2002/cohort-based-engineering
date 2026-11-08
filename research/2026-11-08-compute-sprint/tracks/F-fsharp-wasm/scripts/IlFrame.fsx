// Estimate the Mono WASM interpreter's tier-0 locals frame for every method of .NET assemblies.
// Method (after Indy-init docs/engineering-improvement/investigations/wasm.md §4): frame ≈ align16(8 × (args + IL locals));
// value-type locals are counted as 8 bytes (an under-count). The interpreter refuses a method at ≥ 65,535 bytes
// ("locals size too big") unless its optimised no-inline retry fits.
//   dotnet fsi IlFrame.fsx [--top N] ASSEMBLY.dll ...      prints JSON lines, one per assembly, with the top-N methods
open System
open System.IO
open System.Reflection.Metadata
open System.Reflection.PortableExecutable

let Limit = 65535

/// Tier-0 frame estimate in bytes (pure).
let frameBytes (args: int) (locals: int) =
    let raw = 8 * (args + locals)
    (raw + 15) / 16 * 16

/// Headroom classification against the interpreter limit (pure).
let classify (bytes: int) =
    if bytes >= Limit then "error" elif bytes >= Limit / 2 then "warning" else "ok"

/// Read an ECMA-335 compressed unsigned integer from a blob reader.
let compressed (r: byref<BlobReader>) = r.ReadCompressedInteger()

/// Parameter count (+1 for instance methods) from a MethodDefSig blob.
let argCount (md: MetadataReader) (m: MethodDefinition) =
    let mutable r = md.GetBlobReader m.Signature
    let header = r.ReadSignatureHeader()
    if header.IsGeneric then compressed &r |> ignore
    let ps = compressed &r
    ps + (if header.IsInstance then 1 else 0)

/// Local count from a LocalVarSig blob (0x07, count, ...).
let localCount (md: MetadataReader) (body: MethodBodyBlock) =
    if body.LocalSignature.IsNil then 0
    else
        let sigBlob = md.GetStandaloneSignature(body.LocalSignature).Signature
        let mutable r = md.GetBlobReader sigBlob
        r.ReadByte() |> ignore
        compressed &r

type MethodFrame = { Name: string; Args: int; Locals: int; IlBytes: int; FrameBytes: int; Status: string }

let scan (path: string) =
    use pe = new PEReader(File.OpenRead path)
    let md = pe.GetMetadataReader()
    [ for h in md.MethodDefinitions do
        let m = md.GetMethodDefinition h
        if m.RelativeVirtualAddress <> 0 then
            let body = pe.GetMethodBody m.RelativeVirtualAddress
            let t = md.GetTypeDefinition(m.GetDeclaringType())
            let name = sprintf "%s.%s::%s" (md.GetString t.Namespace) (md.GetString t.Name) (md.GetString m.Name)
            let a, l = argCount md m, localCount md body
            let f = frameBytes a l
            yield { Name = name; Args = a; Locals = l; IlBytes = body.Size; FrameBytes = f; Status = classify f } ]

let json (s: string) = "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\""

let report top (path: string) =
    let ms = scan path |> List.sortByDescending (fun m -> m.FrameBytes)
    let row m = sprintf "{\"method\":%s,\"args\":%d,\"locals\":%d,\"ilBytes\":%d,\"frameBytes\":%d,\"status\":%s}" (json m.Name) m.Args m.Locals m.IlBytes m.FrameBytes (json m.Status)
    sprintf "{\"assembly\":%s,\"methods\":%d,\"maxFrameBytes\":%d,\"headroomPct\":%.1f,\"warnings\":%d,\"errors\":%d,\"top\":[%s]}"
        (json (Path.GetFileName path)) ms.Length (ms |> List.tryHead |> Option.map (fun m -> m.FrameBytes) |> Option.defaultValue 0)
        (100.0 * (1.0 - float (ms |> List.tryHead |> Option.map (fun m -> m.FrameBytes) |> Option.defaultValue 0) / float Limit))
        (ms |> List.filter (fun m -> m.Status = "warning") |> List.length) (ms |> List.filter (fun m -> m.Status = "error") |> List.length)
        (String.Join(",", ms |> List.truncate top |> List.map row))

let selfTest () =
    let check name cond = if not cond then failwithf "self-test failed: %s" name
    check "frame rounding" (frameBytes 1 7246 = 57984)   // wasm.md: e02d000 passed, last local ends at 57,984 B
    check "frame fail case" (frameBytes 1 8838 = 70720)  // wasm.md: ec6407b failed at 70,720 B
    check "classify ok" (classify 57984 = "warning")
    check "classify error" (classify 70720 = "error")
    check "classify small" (classify 160 = "ok")
    printfn "{\"selfTest\":\"pass\"}"

match fsi.CommandLineArgs |> Array.toList |> List.tail with
| [ "--self-test" ] -> selfTest ()
| "--top" :: n :: files -> files |> List.iter (report (int n) >> printfn "%s")
| files -> files |> List.iter (report 5 >> printfn "%s")
